# KRaft Dynamic Quorum Disaster Recovery

This guide explains how to recover a Confluent Platform cluster that runs a **dynamic KRaft controller quorum** (KIP-853) after it loses its quorum.

A region, rack, or set of machines went down and took enough KRaft voters with it that the quorum is lost. There is no controller leader, so no metadata changes are possible: no topic changes, no partition leader moves, no new brokers. The surviving controllers and brokers are still there. This procedure builds a new working quorum from the surviving controllers so the cluster is available again. Until the failed hosts are restored, the cluster runs on a smaller quorum with less fault tolerance.

There are two ways to recover:

- **[Automated recovery](#automated-recovery):** the `playbooks/KRaftQuorumRecovery.yaml` playbook. This is the recommended path.
- **[Manual recovery](#manual-recovery):** the same steps by hand.

## Contents

- [Quorum loss in a dynamic quorum](#quorum-loss-in-a-dynamic-quorum)
- [Which procedure applies?](#which-procedure-applies)
- [Data safety and RPO](#data-safety-and-rpo)
- [Before you begin](#before-you-begin)
- [Sample inventory](#sample-inventory)
- [Automated recovery](#automated-recovery)
- [Manual recovery](#manual-recovery)
- [Replacing a host that will not come back](#replacing-a-host-that-will-not-come-back)
- [Minority of controllers down (quorum still healthy)](#minority-of-controllers-down-quorum-still-healthy)
- [Verification](#verification)
- [Clean up after recovery](#clean-up-after-recovery)
- [References](#references)

## Quorum loss in a dynamic quorum

In a dynamic KRaft quorum, the controllers that vote on metadata changes are called **voters**. The quorum can elect a leader and accept metadata writes only while a **majority** of voters are available. For `N` voters, the majority is `floor(N / 2) + 1`.

For example, a two-region cluster with three controllers in each region has six voters, so the majority is four. If one region is lost, only three voters remain. The quorum has no leader, and metadata writes are blocked.

## Which procedure applies?

Check whether the quorum still has a leader. Run this from any surviving controller:

```bash
kafka-metadata-quorum --bootstrap-controller <controller-host>:9093 \
  --command-config /etc/controller/client.properties describe --status
```

```
KRaft quorum status?
├── Healthy (describe --status returns a LeaderId)
│   ├── All voters present and caught up → nothing to do
│   └── A minority of voters down, cluster still serving →
│       Minority of controllers down (quorum still healthy)
└── Lost (describe --status times out, or there is no leader)
    ├── Failed voters < majority → quorum-loss recovery, RPO = 0
    └── Failed voters >= majority → quorum-loss recovery, metadata loss possible
```

| Topology | Voters | Majority | Quorum is lost when | Recovery |
|---|---|---|---|---|
| 1DC, 3 controllers | 3 | 2 | 2 voters fail | Metadata loss possible |
| 1DC, 5 controllers | 5 | 3 | 3 voters fail | Metadata loss possible |
| 2DC 3-3 | 6 | 4 | One region fails (3 voters) | RPO = 0 |
| 2.5DC 2-2-1 | 5 | 3 | 3 voters fail | Metadata loss possible |

## Data safety and RPO

The **Recovery Point Objective (RPO)** is how much committed data you can lose in a recovery. **RPO = 0** means no committed data is lost.

A metadata write is **committed** only after a majority of voters store it.

- **Failed voters fewer than the majority:** every committed metadata write reached at least one surviving controller. Rebuilding the quorum from the surviving controllers loses no metadata, so the RPO is zero. In the 2DC 3-3 example, three failed voters are fewer than the majority of four.
- **Failed voters equal to or greater than the majority:** this procedure still applies. But a committed metadata write might exist only on failed controllers, so rebuilding the quorum can lose that metadata.

The new quorum is rebuilt from one surviving controller, called the **seed**. Choose the seed by the **highest metadata epoch** first, and break ties by the **largest log end offset**. Do not choose the seed by log end offset alone. A longer log from an older epoch can be a stale copy that is missing committed writes. The playbook applies this rule for you.

Recovery only changes **metadata** (the `__cluster_metadata` log). Topic data on the brokers is not changed.

## Before you begin

### Prerequisites

- Confluent Platform **8.4.0 or later**, deployed by cp-ansible.
- The cluster runs with `kraft_dynamic_quorum_enabled: true` (deployed as dynamic, or migrated with `playbooks/StaticToDynamicQuorumMigration.yaml`).
- `kafka_controller_kraft_auto_join_enabled` is `true` (the default). Recovered controllers rejoin the quorum through auto-join.
- The inventory the cluster was deployed with.
- SSH access to every **surviving** controller and broker.
- Free disk space on each surviving controller for one copy of its `__cluster_metadata-0` folder.

**Rehearse this before you need it.** Run the full procedure on a staging cluster that matches your production layout. A dry run finds setup-specific problems (DNS, certificates, firewalls, custom paths) while there is no pressure.

### Keep the failed hosts down during recovery

Recovery rebuilds the quorum and creates a new metadata history, so the failed hosts must stay offline for the entire process. If the failed controllers come back while recovery is in progress and can reach each other, they can form a second, competing quorum on the old history. This results in **split-brain**: two leaders accepting different metadata changes for the same cluster.

**Keep the failed hosts powered off or unreachable until you finish Phase 1.** cp-ansible enables the Kafka services at boot, so a failed host that powers back on starts Kafka by itself. As soon as you can reach a failed host, and before it can reach the rest of the cluster, stop and disable Kafka on it:

```bash
sudo systemctl disable --now confluent-kcontroller   # controllers
sudo systemctl disable --now confluent-server        # brokers
```

Bring failed hosts back only with Phase 2, which clears their old metadata first.

### Snapshot the controller disks

The step that rebuilds the voter set **cannot be undone**. Before Phase 1, take a disk-level snapshot of each surviving controller's metadata disk (default `/var/lib/controller`). That is your real rollback if something goes wrong.

Both recovery paths also copy `__cluster_metadata-0` into a backup folder on each surviving controller before changing anything.

## Sample inventory

[`hosts.yml`](hosts.yml) is a two-region (2DC 3-3) cluster:

- `dc1`: `kcontroller-1..3.dc1.example.com` and `kafka-1..3.dc1.example.com`
- `dc2`: `kcontroller-1..3.dc2.example.com` and `kafka-1..3.dc2.example.com`

The quorum has 6 voters and needs 4. If `dc1` is lost, 3 voters remain, so the quorum is lost. The 3 failed voters are fewer than the majority of 4, so the RPO is zero.

The examples below use this inventory with `dc1` lost. With the default node ids, the controllers are `9991`, `9992`, `9993` in `dc1` and `9994`, `9995`, `9996` in `dc2`.

## Automated recovery

### Recovery variables

These variables are only read by `playbooks/KRaftQuorumRecovery.yaml`.

| Variable | Description |
|---|---|
| `kraft_quorum_recovery_failed_hosts` | List of failed controllers and brokers. The playbook never connects to them. Every other `kafka_controller` and `kafka_broker` host is treated as a survivor. |
| `kraft_quorum_recovery_confirmed` | Must be `true`. Confirms that the failed hosts are stopped and will stay stopped. The playbook refuses to run without it. |
| `kraft_quorum_recovery_force_standalone_done` | Only for resuming a run that stopped while the voter set was being rebuilt. See [How the playbook resumes safely](#how-the-playbook-resumes-safely). |

> **⚠ Failed means the disk, not the process.**
> List a host as failed only if its metadata disk is gone or cannot be used. A controller whose Kafka process crashed but whose disk is fine is a **survivor**. Do not list it. Its metadata counts, and leaving it out can make the recovery lose metadata.
>
> **How to identify the failed hosts:** while the quorum has no leader, Kafka cannot tell you which voters are dead. Identify them from your infrastructure: the region, rack, or machines that are down (cloud console, hypervisor, data center status).

### Phase 1: recover the surviving controllers

**Step 1. List the failed hosts** in a vars file, for example `recovery.yml`:

```yaml
kraft_quorum_recovery_failed_hosts:
  - kcontroller-1.dc1.example.com
  - kcontroller-2.dc1.example.com
  - kcontroller-3.dc1.example.com
  - kafka-1.dc1.example.com
  - kafka-2.dc1.example.com
  - kafka-3.dc1.example.com
```

**Step 2 (optional). Preview the seed.** To see which controller will be the seed before anything irreversible happens, run only the first stages:

```bash
ansible-playbook -i hosts.yml confluent.platform.KRaftQuorumRecovery \
  -e @recovery.yml -e kraft_quorum_recovery_confirmed=true \
  --tags kraft_quorum_recovery_precheck,kraft_quorum_recovery_stop_controllers,kraft_quorum_recovery_measure
```

This stops KRaft on the surviving controllers, backs up their metadata, and prints each controller's epoch and log end offset and the chosen seed:

```
"msg": {
    "seed": "kcontroller-2.dc2.example.com",
    "positions": [
        {"host": "kcontroller-1.dc2.example.com", "epoch": 12, "offset": 48210},
        {"host": "kcontroller-2.dc2.example.com", "epoch": 12, "offset": 48213},
        {"host": "kcontroller-3.dc2.example.com", "epoch": 11, "offset": 48300}
    ]
}
```

`kcontroller-2.dc2` wins. It shares the highest epoch (12) and has the larger offset. `kcontroller-3.dc2` has the largest offset, but its epoch is older.

Nothing irreversible has happened yet. The surviving controllers stay stopped until you run Step 3.

**Step 3. Run the recovery:**

```bash
ansible-playbook -i hosts.yml confluent.platform.KRaftQuorumRecovery \
  -e @recovery.yml -e kraft_quorum_recovery_confirmed=true
```

The playbook stops KRaft on the surviving controllers, backs up and measures their metadata, picks the seed, and rebuilds the voter set on the seed. It then starts the seed, rejoins the other surviving controllers one at a time, and restarts the brokers one at a time with fresh metadata. At the end, the surviving controllers are the voters and the cluster accepts metadata writes again.

### How the playbook resumes safely

Only one step is unsafe to repeat: **rebuilding the voter set** (`kafka-metadata-recovery reconfig force-standalone`). If it runs twice, or runs on a different seed, it can damage the metadata. Every other step is safe to run again.

So the playbook keeps a small note, `kraft-quorum-recovery.json`, next to the metadata folder on every surviving controller (default `/var/lib/controller/kraft-quorum-recovery.json`). The note records the seed and whether the rebuild has `started` or is `done`:

1. Just before the rebuild, the playbook writes `started` on every surviving controller.
2. It runs the rebuild on the seed.
3. Right after it succeeds, the playbook writes `done` on every surviving controller.
4. When the whole recovery finishes, it deletes the note.

**To resume after any failure, re-run the same command.** On every run, the playbook first reads the note:

| Note | What it means | What the playbook does |
|---|---|---|
| No note | The rebuild has not started. | Runs from the beginning. Everything before the rebuild is safe to repeat. A new backup is taken. |
| `started` | The run stopped during the rebuild. It may or may not have finished. | **Stops** and changes nothing. |
| `done` | The rebuild finished. | Skips stopping, measuring, and rebuilding. Continues from starting the saved seed. |

The note is written on every surviving controller, so one missing or out-of-date copy does not matter. The playbook uses the most advanced state it finds.

**If the note says `started`:**

1. Do not rebuild the voter set again, by hand or with the playbook.
2. Contact Confluent Support to check the seed controller's metadata.
3. Once Support confirms the rebuild finished, resume with:

   ```bash
   ansible-playbook -i hosts.yml confluent.platform.KRaftQuorumRecovery \
     -e @recovery.yml -e kraft_quorum_recovery_confirmed=true \
     -e kraft_quorum_recovery_force_standalone_done=true
   ```

   `kraft_quorum_recovery_force_standalone_done` is ignored on a new run. It only applies when the note says `started`.

**Other checks that make a re-run safe:**

| Check | Why it matters |
|---|---|
| Failed hosts are never contacted. | Nothing can start or change a failed host by mistake. |
| The run refuses to start without `kraft_quorum_recovery_confirmed=true`. | The operator must confirm the failed hosts are down. |
| A new recovery refuses to start while the quorum has a leader. | Recovery is only for a lost quorum. It cannot rebuild a healthy cluster by mistake. |
| On a resume, the saved seed is always used. If it is now a failed host, the run stops. | The recovery cannot switch to a different seed halfway. |
| The seed is not restarted if it is already the leader. | A resume does not interrupt a working quorum. |
| Before a controller is wiped and rejoined, the live quorum is checked. If the controller is already a voter, it is skipped. If the quorum has no leader, nothing is changed. | A controller that already rejoined is never wiped. Deleting a voter's log can lose committed metadata. |
| Brokers are restarted one at a time with a health check. | Restarting a broker again on a resume is harmless. |

### Phase 2: restore the failed hosts

Do this only after Phase 1 is complete and the new quorum is healthy. It is not urgent.

The failed hosts still hold metadata from before the rebuild. That history no longer matches the new one, so each returning controller and broker must have its old `__cluster_metadata-0` removed before Kafka starts.

1. Make sure Kafka is stopped and disabled on each returning host. See [Keep the failed hosts down during recovery](#keep-the-failed-hosts-down-during-recovery).
2. Remove the returning hosts from `kraft_quorum_recovery_failed_hosts`.
3. Run only the rejoin, broker, and cleanup stages, limited to the returning hosts:

   ```bash
   ansible-playbook -i hosts.yml confluent.platform.KRaftQuorumRecovery \
     -e kraft_quorum_recovery_confirmed=true \
     --tags kraft_quorum_recovery_rejoin_controllers,kraft_quorum_recovery_brokers,kraft_quorum_recovery_complete \
     --limit kcontroller-1.dc1.example.com,kcontroller-2.dc1.example.com,kcontroller-3.dc1.example.com,kafka-1.dc1.example.com,kafka-2.dc1.example.com,kafka-3.dc1.example.com
   ```

   Each returning controller is wiped and rejoined only if it is not already a voter. Each returning broker gets fresh metadata and is health checked.

   **Why only these tags:** after Phase 1 the quorum has a leader again. The full playbook only starts a new recovery when there is no leader, so a run without tags stops at the precheck. These tags skip the recovery stages and run only the steps that bring hosts back.

4. Re-enable Kafka at boot on the returning hosts:

   ```bash
   sudo systemctl enable confluent-kcontroller   # controllers
   sudo systemctl enable confluent-server        # brokers
   ```

## Manual recovery

The commands assume a package install with cp-ansible defaults:

| Item | Default |
|---|---|
| Controller service | `confluent-kcontroller` |
| Controller config | `/etc/controller/server.properties` |
| Controller admin client config | `/etc/controller/client.properties` |
| Controller metadata folder | `/var/lib/controller/data` |
| Controller port | `9093` |
| Broker service | `confluent-server` (`confluent-kafka` for Community) |
| Broker metadata folder | `/var/lib/kafka/data` |
| Service user | `cp-kafka` |

Archive installs, custom users, and rootless deployments use different paths and service names. Adapt the commands to your setup.

> **Note:** run `kafka-metadata-recovery` as the service user (`cp-kafka`, or your custom user), as shown below. If you run it as root, give ownership of `/var/lib/controller/data/__cluster_metadata-0` back to the service user before you start KRaft:
> `sudo chown -R cp-kafka:confluent /var/lib/controller/data/__cluster_metadata-0`

### Phase 1: recover the surviving controllers

```bash
# 0. Decide which controllers failed and which survived.
#    A controller is failed only if its metadata disk is gone or cannot be used.
#    A controller whose process crashed but whose disk is fine is a survivor.
#    While the quorum has no leader, Kafka cannot tell you which voters are dead.
#    Identify the failed hosts from your infrastructure (cloud console, hypervisor, data center status).

# 1. On EVERY surviving controller: stop KRaft.
sudo systemctl stop confluent-kcontroller

# 2. On EVERY surviving controller: back up the metadata log.
TS=$(date +%s)
sudo mkdir -p /var/lib/controller/kraft-quorum-recovery-backup/$TS
sudo cp -a /var/lib/controller/data/__cluster_metadata-0 /var/lib/controller/kraft-quorum-recovery-backup/$TS/

# 3. On EVERY surviving controller: read the epoch and log end offset.
#    The tool needs a .lock file in the metadata folder. A stopped controller may not have one.
sudo -u cp-kafka bash -c '[ -f /var/lib/controller/data/.lock ] || : > /var/lib/controller/data/.lock'
sudo -u cp-kafka kafka-metadata-recovery reconfig log-length --metadata-log-dir /var/lib/controller/data
# Example output:
#   epoch: 12, log end offset: 48213

# 4. Pick the SEED: highest epoch first, then (only on a tie) largest log end offset.
#    Never pick by offset alone.

# 5. On the SEED only: rebuild the voter set. IRREVERSIBLE. Run it exactly once.
#    If secrets protection is enabled, the tool needs the master key to read server.properties:
MASTER_KEY=$(sudo grep -oP 'CONFLUENT_SECURITY_MASTER_KEY=\K[^"]+' \
  /etc/systemd/system/confluent-kcontroller.service.d/override.conf)
sudo -u cp-kafka env CONFLUENT_SECURITY_MASTER_KEY="$MASTER_KEY" \
  kafka-metadata-recovery reconfig force-standalone --config /etc/controller/server.properties
#    Without secrets protection, drop the MASTER_KEY lines and the env part.
#    If it fails or is interrupted: STOP. Do not run it again. Contact Confluent Support.

# 6. On the SEED: start KRaft and confirm it is the only voter and the leader.
sudo systemctl start confluent-kcontroller
kafka-metadata-quorum --bootstrap-controller <seed-host>:9093 \
  --command-config /etc/controller/client.properties describe --status
# LeaderId must be the seed's node id, and CurrentVoters must list only the seed.

# 7. On each OTHER surviving controller, ONE AT A TIME:
#    delete the old metadata log (the backup from step 2 is kept), then start KRaft.
#    meta.properties stays, so the controller keeps its node id and directory id.
sudo rm -rf /var/lib/controller/data/__cluster_metadata-0
sudo systemctl start confluent-kcontroller
#    The controller starts as an Observer, copies the log from the seed,
#    and auto-join promotes it to a voter. Wait until it shows as Follower:
kafka-metadata-quorum --bootstrap-controller <seed-host>:9093 \
  --command-config /etc/controller/client.properties describe --replication
#    Then move on to the next controller.

# 8. On each surviving BROKER, ONE AT A TIME:
#    stop Kafka, delete its old metadata log (topic data is not touched), start Kafka.
sudo systemctl stop confluent-server
sudo rm -rf /var/lib/kafka/data/__cluster_metadata-0
sudo systemctl start confluent-server
#    Wait until the broker is healthy and has no under-replicated partitions before the next one.
```

**If auto-join is disabled** (`kafka_controller_kraft_auto_join_enabled: false`), a controller from step 7 stays an Observer. Promote it by running `add-controller` **on that controller**. The tool reads the node id and directory id from the local config:

```bash
kafka-metadata-quorum --bootstrap-controller <seed-host>:9093 \
  --command-config /etc/controller/server.properties add-controller
```

Phase 1 is complete here. The cluster runs on the surviving controllers.

### Phase 2: restore the failed hosts

Do this only after Phase 1 is complete and the new quorum is healthy. It is not urgent.

The failed hosts still hold metadata from before the rebuild, so each returning controller and broker must have its old `__cluster_metadata-0` removed before Kafka starts.

```bash
# 1. On each returning host, as soon as you can reach it: make sure Kafka is stopped and disabled.
sudo systemctl disable --now confluent-kcontroller   # controllers
sudo systemctl disable --now confluent-server        # brokers

# 2. On each returning CONTROLLER, ONE AT A TIME: move the old metadata log aside, then start KRaft.
TS=$(date +%s)
sudo mkdir -p /var/lib/controller/kraft-quorum-recovery-backup/$TS
sudo mv /var/lib/controller/data/__cluster_metadata-0 /var/lib/controller/kraft-quorum-recovery-backup/$TS/
sudo systemctl start confluent-kcontroller
#    Wait until it shows as Follower in describe --replication (auto-join), then do the next one.

# 3. On each returning BROKER, ONE AT A TIME: delete the old metadata log, then start Kafka.
sudo rm -rf /var/lib/kafka/data/__cluster_metadata-0
sudo systemctl start confluent-server
#    Wait until it is healthy and its partitions are back in sync, then do the next one.

# 4. On each returning host: re-enable Kafka at boot.
sudo systemctl enable confluent-kcontroller   # controllers
sudo systemctl enable confluent-server        # brokers
```

When the failed voters were fewer than the majority, the moved-aside metadata on the returning controllers holds nothing the survivors do not already have. When they were the majority or more, it may hold the only copy of metadata that was lost. Keep it until you have checked.

## Replacing a host that will not come back

If a failed controller's machine or disk is gone for good, it cannot rejoin. Replace it instead:

1. Remove the old controller from the voter set. See [Remove a dead voter](#remove-a-dead-voter).
2. Provision the new host with the same inventory hostname, or update the inventory.
3. Run the controller playbook for that host only:

   ```bash
   ansible-playbook -i hosts.yml confluent.platform.kafka_controller --limit <new-controller-host>
   ```

   cp-ansible sees that the other controllers are already formatted. It formats the new host as an observer (`--no-initial-controllers`), and auto-join makes it a voter. Existing controllers are not restarted.

Replace lost brokers with the `kafka_broker` playbook, also with `--limit`.

## Minority of controllers down (quorum still healthy)

If a minority of voters is down, the quorum still has a leader and the cluster keeps serving. No voter set rebuild is needed, and there is no risk of losing metadata.

**They will come back soon.** Do nothing. When they start again, they catch up from the leader and continue as voters.

**They will be gone for a while, and you want your failure headroom back.** Remove the dead voters so the remaining ones form a smaller quorum. For example, in a 2.5DC 2-2-1 cluster (5 voters, majority 3) that lost the 2-voter region, removing the 2 dead voters leaves 3 voters with a majority of 2. The cluster can then survive one more failure.

### Remove a dead voter

Because the quorum has a leader, `describe --replication` shows which voters are not responding. Dead voters stay listed, but their `LastFetchTimestamp` stops moving and their `Lag` grows.

> **Lag alone does not mean a voter is gone.** A voter can fall behind because of a short network problem, a restart, or a GC pause. Confirm the host is really down by other means before you remove it.

```bash
# 1. List the voters and find the dead ones.
kafka-metadata-quorum --bootstrap-controller <healthy-controller>:9093 \
  --command-config /etc/controller/client.properties describe --replication

# NodeId  DirectoryId             LogEndOffset  Lag   LastFetchTimestamp  Status
# 9994    lQ92sYMTnYHE2pVWw7bJ9w  33940         0     1777643877128       Leader
# 9991    kNxsHyUj3x0pKeAdMowmbQ  33808         132   1777643849923       Follower   <- dead

# 2. Remove each dead voter by node id and directory id.
kafka-metadata-quorum --bootstrap-controller <healthy-controller>:9093 \
  --command-config /etc/controller/client.properties \
  remove-controller --controller-id 9991 --controller-directory-id kNxsHyUj3x0pKeAdMowmbQ

# 3. Describe again. Only the remaining voters should be listed.
```

**The removal only sticks while the controller stays stopped.** With auto-join on (the cp-ansible default), a removed controller that starts again is added back as a voter automatically. That is also how it returns: when the host is back, start KRaft on it and auto-join promotes it. No metadata wipe is needed here, because the voter set was never rebuilt and the controller's log is simply behind.

Returning brokers need no manual step in this case. They catch up on their own.

## Verification

```bash
# Quorum status: a LeaderId and the expected CurrentVoters.
kafka-metadata-quorum --bootstrap-controller <controller-host>:9093 \
  --command-config /etc/controller/client.properties describe --status

# Every expected controller is Leader or Follower, with low Lag.
kafka-metadata-quorum --bootstrap-controller <controller-host>:9093 \
  --command-config /etc/controller/client.properties describe --replication

# No partitions are under-replicated or offline.
kafka-topics --bootstrap-server <broker-host>:<port> \
  --command-config /etc/kafka/client.properties --describe --under-replicated-partitions
kafka-topics --bootstrap-server <broker-host>:<port> \
  --command-config /etc/kafka/client.properties --describe --unavailable-partitions

# Metadata writes work: create and delete a test topic.
kafka-topics --bootstrap-server <broker-host>:<port> \
  --command-config /etc/kafka/client.properties --create --topic dr-check --partitions 1 --replication-factor 3
kafka-topics --bootstrap-server <broker-host>:<port> \
  --command-config /etc/kafka/client.properties --delete --topic dr-check
```

If secrets protection is enabled, the broker's `client.properties` is encrypted. Export `CONFLUENT_SECURITY_MASTER_KEY` (from `/etc/systemd/system/confluent-server.service.d/override.conf`) before running `kafka-topics`. The controller's `client.properties` is not encrypted.

## Clean up after recovery

The metadata backups are **never deleted automatically**. They let you inspect what was replaced. When metadata loss was possible, a backup may hold the only copy of a lost change. Once the full quorum is healthy and you have checked the recovery point, free the space:

```bash
# On each controller, after the quorum is confirmed healthy:
sudo rm -rf /var/lib/controller/kraft-quorum-recovery-backup
```

Also delete the disk snapshots you took before recovery, and remove the recovery variables from any inventory or vars file. **Do not clean up until the recovery is fully verified.**

If a recovery note (`/var/lib/controller/kraft-quorum-recovery.json`) is still there after an automated recovery, the playbook did not finish. Do not delete it unless you are sure the recovery is complete. It is what stops the voter set rebuild from running twice.

## References

- [KIP-853: KRaft Controller Membership Changes](https://cwiki.apache.org/confluence/display/KAFKA/KIP-853%3A+KRaft+Controller+Membership+Changes)
- [KRaft Configuration for Confluent Platform](https://docs.confluent.io/platform/current/kafka-metadata/config-kraft.html)
- [Disaster Recovery for Multi-Region KRaft Clusters (Confluent for Kubernetes)](https://docs.confluent.io/operator/current/co-disaster-recovery.html)
- [`playbooks/KRaftQuorumRecovery.yaml`](../../playbooks/KRaftQuorumRecovery.yaml)
- [`hosts.yml`](hosts.yml) (sample inventory)
