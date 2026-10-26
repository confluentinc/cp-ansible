# KRaft Dynamic Quorum: Add Controllers

This guide explains how to add controllers to a running Confluent Platform cluster with a **dynamic KRaft controller quorum** (KIP-853). Use it to:

1. Add more controllers so as to tolerate more controller failures.
2. Replace a controller that was removed.

With a dynamic quorum, adding a controller is a normal playbook run. You add the host to the inventory and run the controller playbook. cp-ansible formats the new controller to join the existing cluster, and auto-join makes it a voter.

## Contents

- [Requirements](#requirements)
- [How many controllers to add](#how-many-controllers-to-add)
- [Sample inventory](#sample-inventory)
- [Add the controllers](#add-the-controllers)
- [Verify](#verify)
- [Replacing a controller](#replacing-a-controller)
- [Troubleshooting](#troubleshooting)

## Requirements

- The cluster runs a dynamic quorum (`kraft_dynamic_quorum_enabled: true`), deployed as greenfield or migrated from static to dynamic quorum.
- The quorum is healthy: it has a leader and every existing controller is a voter.
- `kafka_controller_kraft_auto_join_enabled` is `true` (the default if you used the cp-ansible playbooks).
- The new hosts are reachable from the Ansible host and from the existing controllers on the controller port (default `9093`).

Check the quorum on any existing controller:

```bash
kafka-metadata-quorum --bootstrap-controller <controller-host>:<controller-port> \
  --command-config /etc/controller/client.properties describe --replication
```

Every existing controller must show as `Leader` or `Follower`. Brokers show as `Observer`, which is expected.

`<controller-port>` is the controller port, `kafka_controller_port` in your inventory (default `9093`).

## How many controllers to add

The quorum needs a majority of voters to work. For `N` voters, the majority is `floor(N / 2) + 1`.

| Voters | Majority | Failures tolerated |
|---|---|---|
| 3 | 2 | 1 |
| 4 | 3 | 1 |
| 5 | 3 | 2 |

## Sample inventory

[`hosts.yml`](hosts.yml) shows a scale-up from 3 to 5 controllers. `kcontroller-1` to `kcontroller-3` already exist, and `kcontroller-4` and `kcontroller-5` are added under `kafka_controller`. Nothing else needs to change in the inventory.

## Add the controllers

### Step 1: add the new hosts to the inventory

Add the new hosts at the **end** of the `kafka_controller` group, with the same settings as the existing controllers. If `node_id` is not set, cp-ansible works out each controller's node id from its position in the group, so inserting a host earlier in the list would change the node ids of the controllers after it, and they would fail to start.

### Step 2: deploy the new controllers

Run the controller playbook for the new controllers only:

```bash
ansible-playbook -i hosts.yml confluent.platform.kafka_controller \
  --limit kcontroller-4.example.com,kcontroller-5.example.com
```

- **With `--limit`** (as above), only the new controllers are installed and started. The existing controllers are not restarted.
- **Without `--limit`**, the playbook also updates the existing controllers so their `controller.quorum.bootstrap.servers` lists the new hosts, and restarts them one at a time. This is not required. The quorum works either way, because controllers know the voters from the metadata log.

Brokers are not restarted in either case, and do not need to be. A broker only needs one reachable controller in its `controller.quorum.bootstrap.servers` list.

## Verify

```bash
# Every controller, old and new, is a voter (Leader or Follower), with low Lag.
kafka-metadata-quorum --bootstrap-controller <controller-host>:<controller-port> \
  --command-config /etc/controller/client.properties describe --replication

# CurrentVoters lists every controller.
kafka-metadata-quorum --bootstrap-controller <controller-host>:<controller-port> \
  --command-config /etc/controller/client.properties describe --status

# Every controller has the same cluster.id.
grep cluster.id /var/lib/controller/data/meta.properties
```

A new controller can show as `Observer` for a short time while it catches up. That is expected.

## Replacing a controller

To replace a controller whose host or disk is lost:

1. Remove the old controller from the quorum. See [Remove Controllers](../remove_controllers/README.md).
2. Add the new host by following this guide. You can reuse the old inventory hostname.

If the quorum itself is lost, use [Disaster Recovery](../disaster_recovery/README.md) instead.

## Troubleshooting

1. **A new controller stays an Observer.**

   **Cause:** it has not caught up with the leader yet, it cannot reach the other controllers on the controller port, or auto-join is off.

   **Fix:** check that its `Lag` is low in `describe --replication`, that it can reach the other controllers on the controller port (default `9093`), and that `controller.quorum.auto.join.enable=true` is in its `server.properties`. If you turned auto-join off, promote it by running this **on the new controller**:

   ```bash
   kafka-metadata-quorum --bootstrap-controller <leader-host>:<controller-port> \
     --command-config /etc/controller/server.properties add-controller
   ```

2. **A new controller fails to start with `INCONSISTENT_CLUSTER_ID`.**

   **Cause:** its storage was formatted for a different cluster, for example by a manual `kafka-storage format`.

   **Fix:** stop it, empty its data directory (default `/var/lib/controller/data`), and re-run the controller playbook with `--limit` on that host.
