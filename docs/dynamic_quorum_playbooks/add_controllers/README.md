# KRaft Dynamic Quorum: Add Controllers

This guide explains how to add controllers to a running Confluent Platform cluster with a **dynamic KRaft controller quorum** (KIP-853). Use it to tolerate more controller failures, to add a second region, or to replace a controller that was removed.

With a dynamic quorum, adding a controller is a normal playbook run. You add the host to the inventory and run the controller playbook. cp-ansible formats the new controller to join the existing cluster, and auto-join makes it a voter. No `kafka-metadata-quorum` commands are needed.

## Contents

- [Requirements](#requirements)
- [How many controllers to add](#how-many-controllers-to-add)
- [Sample inventory](#sample-inventory)
- [Add the controllers](#add-the-controllers)
- [What happens to a new controller](#what-happens-to-a-new-controller)
- [Verify](#verify)
- [Adding a region](#adding-a-region)
- [Replacing a controller](#replacing-a-controller)
- [Troubleshooting](#troubleshooting)

## Requirements

- The cluster runs a dynamic quorum (`kraft_dynamic_quorum_enabled: true`), deployed as greenfield or migrated.
- The quorum is healthy: it has a leader and every existing controller is a voter.
- `kafka_controller_kraft_auto_join_enabled` is `true` (the default).
- The new hosts are reachable from the Ansible host and from the existing controllers on the controller port (default `9093`).

## How many controllers to add

The quorum needs a majority of voters to work. For `N` voters, the majority is `floor(N / 2) + 1`.

| Voters | Majority | Failures tolerated |
|---|---|---|
| 3 | 2 | 1 |
| 4 | 3 | 1 |
| 5 | 3 | 2 |

Add controllers in pairs within a single region. Going from 3 to 4 voters does not tolerate more failures, and needs one more voter for every metadata write.

## Sample inventory

[`hosts.yml`](hosts.yml) shows a 3-controller cluster after adding `kcontroller-4` and `kcontroller-5`. Only the new hosts are added.

## Add the controllers

### Step 1: add the new hosts to the inventory

Add the new hosts under `kafka_controller`, with the same settings as the existing controllers.

### Step 2: deploy the new controllers

Run the controller playbook for the new controllers only:

```bash
ansible-playbook -i hosts.yml confluent.platform.kafka_controller \
  --limit kcontroller-4.example.com,kcontroller-5.example.com
```

The existing controllers and the brokers are not restarted.

## What happens to a new controller

1. cp-ansible checks the data directory of every controller. Because the existing controllers are already formatted, it knows the cluster exists.
2. It reads the cluster id from an existing controller and formats the new controller with that cluster id and `--no-initial-controllers`. A new controller never creates a new quorum.
3. The new controller starts as an observer and copies the metadata log from the leader.
4. Once it has caught up, auto-join promotes it to a voter.

## Verify

```bash
# Every controller, old and new, is a voter (Leader or Follower), with low Lag.
kafka-metadata-quorum --bootstrap-controller <controller-host>:9093 \
  --command-config /etc/controller/client.properties describe --replication

# CurrentVoters lists every controller.
kafka-metadata-quorum --bootstrap-controller <controller-host>:9093 \
  --command-config /etc/controller/client.properties describe --status

# Every controller has the same cluster.id.
grep cluster.id /var/lib/controller/data/meta.properties
```

A new controller can show as `Observer` for a short time while it catches up. That is expected.

## Adding a region

Adding a second region is the same procedure. For example, to go from 3 controllers in `dc1` to the 2DC 3-3 layout, add the 3 `dc2` controllers and the `dc2` brokers to the inventory (see [`hosts_2dc.yml`](../greenfield/hosts_2dc.yml)). Then run the controller playbook with `--limit` on the new controllers, and the broker playbook with `--limit` on the new brokers. cp-ansible reads the cluster id from an existing controller.

## Replacing a controller

To replace a controller whose host or disk is lost:

1. Remove the old controller from the quorum. See [Remove Controllers](../remove_controllers/README.md).
2. Add the new host by following this guide. You can reuse the old inventory hostname.

If the quorum itself is lost, use [Disaster Recovery](../disaster_recovery/README.md) instead.

## Troubleshooting

**A new controller stays an Observer.** Check that it caught up with the leader (low `Lag` in `describe --replication`), that it can reach the other controllers on the controller port, and that `controller.quorum.auto.join.enable=true` is in its `server.properties`. If you disabled auto-join, promote it by running this **on the new controller**:

```bash
kafka-metadata-quorum --bootstrap-controller <leader-host>:9093 \
  --command-config /etc/controller/server.properties add-controller
```

**A new controller fails to start with `INCONSISTENT_CLUSTER_ID`.** Its storage was formatted for a different cluster, for example by a manual `kafka-storage format`. Stop it, empty its data directory (default `/var/lib/controller/data`), and re-run the controller playbook for that host.
