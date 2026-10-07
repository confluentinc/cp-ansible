# KRaft Dynamic Quorum Disaster Recovery

This guide explains how to recover a Confluent Platform cluster that runs a **dynamic KRaft controller quorum** (KIP-853) after controllers are lost.

**The goal (quorum-loss recovery):** a region, rack, or set of machines went down and took enough KRaft voters with it that the quorum is lost. There is no controller leader, so no metadata changes are possible: no topic changes, no partition leader moves, no new brokers. The surviving controllers and brokers are still there. This procedure builds a new working quorum from the surviving controllers so the cluster is available again. Until the failed hosts are restored, the cluster runs with less fault tolerance.

There are two ways to run it:

- **Automated:** the `playbooks/KRaftQuorumRecovery.yaml` playbook. This is the recommended path.
- **Manual:** the same steps by hand with `kafka-metadata-recovery` and `kafka-metadata-quorum`.

Both paths run the same steps in the same order.

A milder case, where only a minority of voters is down and the quorum is still healthy, does not need this procedure. See [Minority of controllers down (quorum still healthy)](#minority-of-controllers-down-quorum-still-healthy).

> **⚠ Core assumption: the failed hosts must stay down while you recover.**
> Recovery runs `force-standalone`, which rewrites the voter set and starts a new metadata history. If the failed controllers come back **during** recovery with their old metadata, and enough of them can reach each other, they can form a second quorum on the old history. That is a **split-brain**: two leaders accepting different metadata changes for the same cluster. Keep the failed hosts powered off, or keep Kafka stopped on them, until recovery is complete and the new quorum is healthy. Bring them back only with the [Phase 2](#phase-2-restore-the-failed-hosts) procedure, which clears their old metadata first.
> This is how KRaft works. It is not a cp-ansible limitation.

## Contents

- [Which procedure applies?](#which-procedure-applies)
- [Data safety](#data-safety)
- [Prerequisites](#prerequisites)
- [Before you start: snapshot the controller disks](#before-you-start-snapshot-the-controller-disks)
- [Sample inventory](#sample-inventory)
- [Recovery variables](#recovery-variables)
- [Phase 1 (automated): recover with the playbook](#phase-1-automated-recover-with-the-playbook)
- [If the playbook stops partway](#if-the-playbook-stops-partway)
- [Phase 1 (manual): recover by hand](#phase-1-manual-recover-by-hand)
- [Phase 2: restore the failed hosts](#phase-2-restore-the-failed-hosts)
- [Minority of controllers down (quorum still healthy)](#minority-of-controllers-down-quorum-still-healthy)
- [Verification](#verification)
- [After recovery: clean up](#after-recovery-clean-up)
- [Gotchas](#gotchas)
- [References](#references)

## Which procedure applies?

First check whether the quorum still has a leader. Run this from any surviving controller:

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
│       (no force-standalone, no recovery playbook)
└── Lost (describe --status times out, or there is no leader)
    ├── Lost controllers < majority (for example 2DC 3-3, one region down: 3 lost, majority is 4) →
    │   Quorum-loss recovery, data safe (RPO = 0)
    └── Lost controllers >= majority (for example 3 controllers, 2 lost disks) →
        Quorum-loss recovery, data loss possible (RPO > 0)
```

A **lost controller** is one whose metadata disk is gone or cannot be used. A controller whose Kafka process crashed but whose disk is fine is a **survivor**. The recovery uses its metadata.

The majority for `N` voters is `floor(N / 2) + 1`.

| Topology | Voters | Majority | Lose 1 region / rack | Recovery |
|---|---|---|---|---|
| 1DC, 3 controllers | 3 | 2 | 1 lost: quorum healthy. 2 lost: quorum lost | 2 lost disks: data loss possible |
| 1DC, 5 controllers | 5 | 3 | 2 lost: quorum healthy. 3 lost: quorum lost | 3 lost disks: data loss possible |
| 2DC 3-3 | 6 | 4 | 3 lost: quorum lost | Data safe |
| 2.5DC 2-2-1 | 5 | 3 | 2 lost: quorum healthy. 3 lost: quorum lost | 3 lost disks: data loss possible |

## Data safety

KRaft only treats a metadata change as committed after a majority of voters store it. So:

- If **fewer than a majority** of controllers lost their metadata, every committed change is on at least one survivor. Recovery picks the most up-to-date survivor as the **seed**, so no committed metadata is lost (**RPO = 0**).
- If **a majority or more** lost their metadata, some committed changes may exist only on the lost controllers. Recovery still brings the cluster back, but those changes are gone (**RPO > 0**).

**How the seed is chosen:** largest **epoch** first, then (only on a tie) largest **log end offset**. Never by offset alone. A longer log from an older epoch can be a stale branch that is missing committed changes. The playbook applies this rule for you. On the manual path you apply it yourself.

Recovery only touches **metadata** (the `__cluster_metadata` log). Topic data on the brokers is not changed.

## Prerequisites

- Confluent Platform **8.4.0 or later**, deployed by cp-ansible.
- The cluster was deployed with `kraft_dynamic_quorum_enabled: true` (greenfield, or migrated with `playbooks/StaticToDynamicQuorumMigration.yaml`).
- `kafka_controller_kraft_auto_join_enabled` is `true` (the default). Recovered controllers rejoin the quorum through auto-join.
- The inventory you deployed with. The recovery playbook reads the same inventory.
- SSH access from the Ansible host to every **surviving** controller and broker.
- `kafka-metadata-recovery` and `kafka-metadata-quorum` are on the controllers. Both ship with Confluent Platform in the same `bin` folder as the other Kafka tools.
- Free disk space on each surviving controller for one copy of its `__cluster_metadata-0` folder (the playbook takes a backup).
- You have confirmed, by means other than Kafka, that the failed hosts are really down: cloud console, hypervisor, data center status. Then power them off or stop Kafka on them, and make sure Kafka cannot start on them by itself (see [Gotchas](#gotchas)).

**Rehearse this before you need it.** Run the full procedure on a staging cluster that matches your production layout. A dry run finds setup-specific problems (DNS, certificates, firewalls, custom paths) while there is no pressure.

## Before you start: snapshot the controller disks

`force-standalone` rewrites the voter set and **cannot be undone**. Before Phase 1, take a disk-level snapshot of each surviving controller's metadata disk (default `/var/lib/controller`). That is your real rollback if something goes wrong, for example if the wrong seed is used. Use whatever your platform offers: cloud disk snapshots, LVM snapshots, or VM snapshots.

The playbook also copies `__cluster_metadata-0` into a backup folder on each survivor before it changes anything. That protects the metadata log, but a disk snapshot protects against a wider class of mistakes.

## Sample inventory

[`hosts.yml`](hosts.yml) is a two-region (2DC 3-3) cluster:

- `dc1`: `kcontroller-1..3.dc1.example.com` and `kafka-1..3.dc1.example.com`
- `dc2`: `kcontroller-1..3.dc2.example.com` and `kafka-1..3.dc2.example.com`

The quorum has 6 voters and needs 4. If `dc1` is lost, 3 voters remain, so the quorum is lost. Because only 3 of 6 metadata copies are lost (fewer than the majority of 4), recovery is data safe.

The examples below use this inventory with `dc1` lost. With the default node ids, the controllers are `9991`, `9992`, `9993` in `dc1` and `9994`, `9995`, `9996` in `dc2`.

## Recovery variables

These variables are only read by `playbooks/KRaftQuorumRecovery.yaml`. Do not keep them in the inventory during normal operation. Pass them with `-e`, or with a separate vars file, only when you run the recovery.

| Variable | Required | Description |
|---|---|---|
| `kraft_quorum_recovery_failed_hosts` | Yes | List of lost controllers and brokers. The playbook never connects to these hosts. Every other `kafka_controller` and `kafka_broker` host is treated as a survivor. |
| `kraft_quorum_recovery_confirmed` | Yes | Must be `true`. Confirms that the failed hosts are stopped and will stay stopped. The playbook refuses to run without it. |
| `kraft_quorum_recovery_seed` | No | Forces a specific seed controller instead of the one the playbook picks. Only use this when Confluent Support asks you to. It must be a surviving controller. It cannot be changed once the voter set rebuild has started. |
| `kraft_quorum_recovery_force_standalone_done` | No | Only for resuming a run that stopped while the voter set was being rebuilt. See [If the playbook stops partway](#if-the-playbook-stops-partway). |

## Phase 1 (automated): recover with the playbook

### Step 1: list the failed hosts

Create a vars file for the recovery, for example `recovery.yml`:

```yaml
kraft_quorum_recovery_failed_hosts:
  - kcontroller-1.dc1.example.com
  - kcontroller-2.dc1.example.com
  - kcontroller-3.dc1.example.com
  - kafka-1.dc1.example.com
  - kafka-2.dc1.example.com
  - kafka-3.dc1.example.com
```

### Step 2 (optional): preview the seed

To see which controller will be the seed before anything irreversible happens, run only the precheck, stop, and measure stages:

```bash
ansible-playbook -i hosts.yml confluent.platform.KRaftQuorumRecovery \
  -e @recovery.yml -e kraft_quorum_recovery_confirmed=true \
  --tags kraft_quorum_recovery_precheck,kraft_quorum_recovery_stop_controllers,kraft_quorum_recovery_measure
```

This stops Kafka on the surviving controllers, backs up their metadata, and prints each controller's epoch and log end offset and the chosen seed:

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

Here `kcontroller-2.dc2` wins. It shares the highest epoch (12) with `kcontroller-1.dc2` and has the larger offset. `kcontroller-3.dc2` has the largest offset, but its epoch is older, so its log may be missing committed changes.

Nothing irreversible has happened yet. The controllers stay stopped until you run Step 3.

### Step 3: run the recovery

```bash
ansible-playbook -i hosts.yml confluent.platform.KRaftQuorumRecovery \
  -e @recovery.yml -e kraft_quorum_recovery_confirmed=true
```

### What the playbook does

| # | Stage (tag) | What happens | Impact |
|---|---|---|---|
| 1 | Select surviving hosts (always runs) | Checks the failed host list and groups the survivors. | None. No host is contacted. |
| 2 | Load recovery state (always runs) | Reads the recovery note on each surviving controller. Decides whether this is a new run or a resume. | None. |
| 3 | Precheck (`kraft_quorum_recovery_precheck`) | Checks `kraft_quorum_recovery_confirmed`, dynamic quorum, and auto-join. Checks whether the quorum still has a leader, and **stops if it does**. | None. With no leader, this step waits up to about a minute for the check to time out. |
| 4 | Stop controllers (`kraft_quorum_recovery_stop_controllers`) | Stops Kafka on every surviving controller. | Surviving controllers are down. Metadata changes were already blocked. |
| 5 | Measure (`kraft_quorum_recovery_measure`) | Creates the `.lock` file the tool needs, copies `__cluster_metadata-0` to a backup folder, reads each controller's epoch and log end offset with `kafka-metadata-recovery reconfig log-length`, and picks the seed. | Disk space for the backup. |
| 6 | Rebuild the voter set (`kraft_quorum_recovery_force_standalone`) | Records "started" on every survivor, runs `kafka-metadata-recovery reconfig force-standalone` on the seed, then records "done". The seed is now the only voter. | **Irreversible.** Runs once. |
| 7 | Start the seed (`kraft_quorum_recovery_start_seed`) | Starts Kafka on the seed, waits until it is the leader, and runs the controller health check. | **Metadata is available again** from here. |
| 8 | Rejoin controllers (`kraft_quorum_recovery_rejoin_controllers`) | One controller at a time: confirms the quorum has a leader, and if this controller is not already a voter, stops it, deletes its old `__cluster_metadata-0`, starts it, and waits until auto-join makes it a voter. | Each controller restarts once. |
| 9 | Recover brokers (`kraft_quorum_recovery_brokers`) | One broker at a time: stops it, deletes its old `__cluster_metadata-0` (topic data is not touched), starts it, and runs the broker health check. | Rolling broker restart. |
| 10 | Clear recovery state (`kraft_quorum_recovery_complete`) | Deletes the recovery note on each surviving controller. Backups are kept. | None. |

At the end, `dc2`'s three controllers are the voters, the brokers in `dc2` are serving, and the quorum tolerates one more controller failure. `dc1` is still down. Restore it with [Phase 2](#phase-2-restore-the-failed-hosts).

### Safety checks built into the playbook

- The failed hosts are never contacted or changed.
- It refuses to run without `kraft_quorum_recovery_confirmed=true`.
- It refuses to start a new recovery while the quorum still has a leader.
- `force-standalone` runs at most once. See the next section.
- A controller that is already a voter is never wiped.
- No controller is touched while the quorum has no leader (during the rejoin stage).
- The seed is not restarted if it is already the leader.

## If the playbook stops partway

The playbook saves its progress in a small note, `kraft-quorum-recovery.json`, next to the metadata folder on every surviving controller (default `/var/lib/controller/kraft-quorum-recovery.json`). The note holds the seed and whether `force-standalone` has started or is done. It is deleted when the recovery finishes.

To resume, **re-run the same command**. What happens depends on where it stopped:

| Where it stopped | Note says | What the next run does |
|---|---|---|
| Before stage 6 | (no note) | Starts again from the beginning. Everything before stage 6 is safe to repeat. A new backup is taken. |
| During stage 6 | `started` | **Stops.** It cannot tell whether `force-standalone` finished, and running it twice can damage the metadata. See below. |
| After stage 6 | `done` | Skips stop, measure, and rebuild. Continues from starting the saved seed. Controllers that already rejoined are skipped. Brokers restart once more, which is harmless. |

**If the run stopped during stage 6:**

1. Do not run `force-standalone` again, by hand or with the playbook.
2. Contact Confluent Support to check the seed controller's metadata.
3. Once Support confirms that `force-standalone` finished, resume with:

   ```bash
   ansible-playbook -i hosts.yml confluent.platform.KRaftQuorumRecovery \
     -e @recovery.yml -e kraft_quorum_recovery_confirmed=true \
     -e kraft_quorum_recovery_force_standalone_done=true
   ```

   `kraft_quorum_recovery_force_standalone_done` is ignored on a new run. It only applies when the note says `started`.

**Other rules while a recovery is in progress:**

- The seed cannot be changed. Passing a different `kraft_quorum_recovery_seed` fails the run.
- If the saved seed is now in `kraft_quorum_recovery_failed_hosts` or cannot be reached, the run fails. Recovery can only continue from that seed.
- If you take over by hand, use the note to see where to pick up, and continue the [manual steps](#phase-1-manual-recover-by-hand) from the next step for the same seed.

## Phase 1 (manual): recover by hand

Use this path if you cannot run Ansible, or you want to control each step. The commands assume a package install with cp-ansible defaults:

| Item | Default |
|---|---|
| Controller service | `confluent-kcontroller` |
| Controller config | `/etc/controller/server.properties` |
| Controller admin client config | `/etc/controller/client.properties` |
| Controller metadata folder | `/var/lib/controller/data` |
| Controller port | `9093` |
| Broker service | `confluent-server` (`confluent-kafka` for Community) |
| Broker config | `/etc/kafka/server.properties` |
| Broker metadata folder | `/var/lib/kafka/data` |
| Service user and group | `cp-kafka` / `confluent` |

Archive installs, custom users, and rootless deployments use different paths and service names. Check your inventory and adapt the commands.

Replace `<seed-host>` and the other placeholders with your values.

```bash
# 1. On EVERY surviving controller: stop Kafka.
sudo systemctl stop confluent-kcontroller

# 2. On EVERY surviving controller: back up the metadata log.
TS=$(date +%s)
sudo mkdir -p /var/lib/controller/kraft-quorum-recovery-backup/$TS
sudo cp -a /var/lib/controller/data/__cluster_metadata-0 /var/lib/controller/kraft-quorum-recovery-backup/$TS/

# 3. On EVERY surviving controller: read the epoch and log end offset.
#    The tool needs the .lock file in the metadata folder. A stopped controller may not have one.
sudo -u cp-kafka bash -c '[ -f /var/lib/controller/data/.lock ] || : > /var/lib/controller/data/.lock'
sudo -u cp-kafka kafka-metadata-recovery reconfig log-length --metadata-log-dir /var/lib/controller/data
# Example output:
#   epoch: 12, log end offset: 48213

# 4. Pick the SEED: largest epoch first, then (only on a tie) largest log end offset.
#    Never pick by offset alone.

# 5. On the SEED only: rebuild the voter set. IRREVERSIBLE. Run it exactly once.
#    If secrets protection is enabled, the tool needs the master key to read server.properties:
MASTER_KEY=$(sudo grep -oP 'CONFLUENT_SECURITY_MASTER_KEY=\K[^"]+' \
  /etc/systemd/system/confluent-kcontroller.service.d/override.conf)
sudo -u cp-kafka env CONFLUENT_SECURITY_MASTER_KEY="$MASTER_KEY" \
  kafka-metadata-recovery reconfig force-standalone --config /etc/controller/server.properties
#    Without secrets protection, drop the MASTER_KEY lines and the env part.
#    If it fails or is interrupted: STOP. Do not run it again. Contact Confluent Support.

# 6. On the SEED: start Kafka and confirm it is the only voter and the leader.
sudo systemctl start confluent-kcontroller
kafka-metadata-quorum --bootstrap-controller <seed-host>:9093 \
  --command-config /etc/controller/client.properties describe --status
# LeaderId must be the seed's node id, and CurrentVoters must list only the seed.

# 7. On each OTHER surviving controller, ONE AT A TIME:
#    delete the old metadata log (the backup from step 2 is kept), then start Kafka.
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

**If auto-join is disabled** (`kafka_controller_kraft_auto_join_enabled: false`), a controller from step 7 stays an Observer. Promote it by running `add-controller` **on that controller**. The tool reads the node id and directory id from the local config, so it must run on the controller being added:

```bash
kafka-metadata-quorum --bootstrap-controller <seed-host>:9093 \
  --command-config /etc/controller/server.properties add-controller
```

**Phase 1 is complete here.** The cluster runs on the surviving controllers. Phase 2 restores full fault tolerance and is not urgent.

## Phase 2: restore the failed hosts

Do this only after Phase 1 is complete and the new quorum is healthy.

The failed controllers still hold metadata from **before** `force-standalone`. That history no longer matches the new one, so each returning controller and broker must have its old `__cluster_metadata-0` removed before Kafka starts. Its `meta.properties` stays, so it keeps its node id.

### Step 1: keep Kafka from starting on the returning hosts

cp-ansible enables the Kafka services at boot. Before a failed host can reach the rest of the cluster again, make sure Kafka will not start by itself:

```bash
# On each returning host, as soon as you can reach it (ideally before it rejoins the network):
sudo systemctl disable --now confluent-kcontroller   # controllers
sudo systemctl disable --now confluent-server        # brokers
```

If Kafka already started on a returning host, stop it right away.

### Step 2 (automated): rejoin with the playbook

Remove the returning hosts from `kraft_quorum_recovery_failed_hosts` (or leave the list empty). Then run only the rejoin, broker, and cleanup stages, limited to the returning hosts:

```bash
ansible-playbook -i hosts.yml confluent.platform.KRaftQuorumRecovery \
  -e kraft_quorum_recovery_confirmed=true \
  --tags kraft_quorum_recovery_rejoin_controllers,kraft_quorum_recovery_brokers,kraft_quorum_recovery_complete \
  --limit kcontroller-1.dc1.example.com,kcontroller-2.dc1.example.com,kcontroller-3.dc1.example.com,kafka-1.dc1.example.com,kafka-2.dc1.example.com,kafka-3.dc1.example.com
```

For each returning controller, the playbook checks the live quorum. If the controller is not a voter, it stops it, deletes its old metadata log, starts it, and waits until auto-join makes it a voter. A controller that is already a voter is never wiped. Each returning broker is stopped, its metadata log is deleted, and it is started and health checked.

Do **not** run the full playbook without `--tags` for Phase 2. The precheck will stop it because the quorum now has a leader.

### Step 2 (manual): rejoin by hand

```bash
# On each returning CONTROLLER, ONE AT A TIME:
TS=$(date +%s)
sudo mkdir -p /var/lib/controller/kraft-quorum-recovery-backup/$TS
sudo mv /var/lib/controller/data/__cluster_metadata-0 /var/lib/controller/kraft-quorum-recovery-backup/$TS/
sudo systemctl start confluent-kcontroller
# Wait until it shows as Follower in describe --replication (auto-join), then do the next one.

# On each returning BROKER, ONE AT A TIME:
sudo rm -rf /var/lib/kafka/data/__cluster_metadata-0
sudo systemctl start confluent-server
# Wait until it is healthy and its partitions are back in sync, then do the next one.
```

In the data-safe case, the moved-aside metadata on the returning controllers holds nothing that the surviving region does not already have. It is kept only so both procedures are the same. In the data-loss case, it may hold the only copy of changes that were lost. Keep it until you have checked what was lost.

### Step 3: re-enable the services at boot

```bash
sudo systemctl enable confluent-kcontroller   # controllers
sudo systemctl enable confluent-server        # brokers
```

### Replacing a host that will not come back

If a failed controller's machine or disk is gone for good, it cannot rejoin. Replace it instead:

1. Remove the old controller from the voter set. See [Remove a dead voter](#remove-a-dead-voter).
2. Provision the new host with the same inventory hostname, or update the inventory.
3. Run the normal controller playbook for that host only:

   ```bash
   ansible-playbook -i hosts.yml confluent.platform.kafka_controller --limit <new-controller-host>
   ```

   cp-ansible sees that the other controllers are already formatted. It formats the new host as an observer (`--no-initial-controllers`), and auto-join makes it a voter. Existing controllers are not restarted.

Replace lost brokers with the normal `kafka_broker` playbook, also with `--limit`.

## Minority of controllers down (quorum still healthy)

If a minority of voters is down, the quorum still has a leader and the cluster keeps serving. There is no `force-standalone`, no recovery playbook, and no data-loss risk. What you do depends on how long the controllers will be gone.

**They will come back soon.** Do nothing. When they start again, they catch up from the leader and continue as voters.

**They will be gone for a while, and you want your failure headroom back.** Remove the dead voters so the remaining ones form a smaller quorum. For example, in a 2.5DC 2-2-1 cluster (5 voters, majority 3) that lost the 2-voter region, removing the 2 dead voters leaves 3 voters with a majority of 2, so the cluster can survive one more failure.

> **Lag alone does not mean a voter is gone.** A voter can fall behind because of a short network problem, a restart, or a GC pause. Confirm the host is really down by other means before you remove it.

### Remove a dead voter

```bash
# 1. List the voters and find the dead ones. They have a frozen LastFetchTimestamp and growing Lag.
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

**The removal only sticks while the controller stays stopped.** With auto-join on (the cp-ansible default), a removed controller that starts again is added back as a voter automatically. That is also how it returns: when the host is back, start Kafka on it and auto-join promotes it. No `add-controller` and no metadata wipe are needed here, because there was no `force-standalone` and the controller's log is simply behind.

Returning brokers need no manual step in this case. They catch up on their own.

## Verification

```bash
# Quorum status: a LeaderId and the expected CurrentVoters.
kafka-metadata-quorum --bootstrap-controller <controller-host>:9093 \
  --command-config /etc/controller/client.properties describe --status

# Every expected controller is Leader or Follower, with low Lag.
kafka-metadata-quorum --bootstrap-controller <controller-host>:9093 \
  --command-config /etc/controller/client.properties describe --replication

# Topics are intact and no partitions are under-replicated or offline.
kafka-topics --bootstrap-server <broker-host>:<port> \
  --command-config /etc/kafka/client.properties --describe --under-replicated-partitions
kafka-topics --bootstrap-server <broker-host>:<port> \
  --command-config /etc/kafka/client.properties --describe --unavailable-partitions

# The metadata write path works: create and delete a test topic.
kafka-topics --bootstrap-server <broker-host>:<port> \
  --command-config /etc/kafka/client.properties --create --topic dr-check --partitions 1 --replication-factor 3
kafka-topics --bootstrap-server <broker-host>:<port> \
  --command-config /etc/kafka/client.properties --delete --topic dr-check
```

If secrets protection is enabled, the broker's `client.properties` is encrypted. Export `CONFLUENT_SECURITY_MASTER_KEY` (from `/etc/systemd/system/confluent-server.service.d/override.conf`) before running `kafka-topics`. The controller's `client.properties` is not encrypted.

## After recovery: clean up

The backups are **never deleted automatically**. They let you inspect what was replaced. In the data-loss case, a backup may hold the only copy of a lost change. Once the full quorum is healthy and you have checked the recovery point, free the space:

```bash
# On each controller, after the quorum is confirmed healthy:
sudo rm -rf /var/lib/controller/kraft-quorum-recovery-backup
```

Also delete the disk snapshots you took before recovery, and remove the recovery variables from any inventory or vars file. **Do not clean up until the recovery is fully verified.** These are your rollback copies.

If a recovery note (`/var/lib/controller/kraft-quorum-recovery.json`) is still there, the playbook did not finish. Do not delete it unless you are sure the recovery is complete. It is what stops `force-standalone` from running twice.

## Gotchas

- **`force-standalone` is irreversible.** Run it exactly once. If it fails or is interrupted, stop and contact Confluent Support. Do not run it again.
- **Keep the failed hosts down.** A failed controller that starts with its old metadata while you recover can cause a split-brain. cp-ansible enables Kafka at boot, so disable the services on failed hosts before they come back.
- **Pick the seed by epoch, then offset.** Never by offset alone.
- **Lost means the disk, not the process.** A controller with a crashed process and a good disk is a survivor. Include it, because its metadata counts.
- **The rebuilt quorum is smaller.** In the 2DC 3-3 example, it has 3 voters and tolerates 1 more failure until Phase 2 is done.
- **Run tools as the service user.** On the manual path, run `kafka-metadata-recovery` as `cp-kafka` (or your custom user). If you run it as root, give ownership of `/var/lib/controller/data/__cluster_metadata-0` back to the service user before you start Kafka. The playbook does this for you.
- **The quorum check in the precheck can take about a minute** when there is no leader. That is expected.
- **Full playbook runs refuse to start while the quorum has a leader.** Use the Phase 2 tags with `--limit` to rejoin returning hosts.
- **Custom paths.** If you set `metadata.log.dir` or a custom `log.dirs`, the playbook uses them. On the manual path, use your own paths.

## References

- [KIP-853: KRaft Controller Membership Changes](https://cwiki.apache.org/confluence/display/KAFKA/KIP-853%3A+KRaft+Controller+Membership+Changes)
- [KRaft Configuration for Confluent Platform](https://docs.confluent.io/platform/current/kafka-metadata/config-kraft.html)
- [Disaster Recovery for Multi-Region KRaft Clusters (Confluent for Kubernetes)](https://docs.confluent.io/operator/current/co-disaster-recovery.html)
- [`playbooks/KRaftQuorumRecovery.yaml`](../../playbooks/KRaftQuorumRecovery.yaml)
- [`hosts.yml`](hosts.yml) (sample inventory)
