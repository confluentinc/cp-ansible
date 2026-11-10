# KRaft Dynamic Quorum: Greenfield Deployment

This guide explains how to deploy a **new** Confluent Platform cluster with a **dynamic KRaft controller quorum** (KIP-853).

Greenfield means the cluster starts from scratch. It runs with a dynamic quorum (`kraft.version=1`) from day one. To move an existing static KRaft cluster to a dynamic quorum, see [Static to Dynamic Quorum Migration](../migration/README.md) instead.

## Contents

- [Requirements](#requirements)
- [Choosing the number of controllers](#choosing-the-number-of-controllers)
- [Sample inventory](#sample-inventory)
- [Variables](#variables)
- [Deploy](#deploy)
- [Verify](#verify)
- [Troubleshooting](#troubleshooting)
- [Next steps](#next-steps)

## Requirements

- Confluent Platform **8.4.0 or later**.
- Dedicated controllers in the `kafka_controller` group.
- Every controller is reachable from the Ansible host during the first deployment.

## Choosing the number of controllers

The quorum can elect a leader and accept metadata changes only while a **majority** of voters is available. For `N` voters, the majority is `floor(N / 2) + 1`.

| Voters | Majority | Failures tolerated |
|---|---|---|
| 3 | 2 | 1 |
| 4 | 3 | 1 |
| 5 | 3 | 2 |
| 6 | 4 | 2 |

## Sample inventory

[`hosts.yml`](hosts.yml) is a cluster with 3 controllers and 3 brokers.

## Variables

### Variables you set

Set these in your inventory, under `all.vars`:

| Variable | Default | Description |
|---|---|---|
| `kraft_dynamic_quorum_enabled` | `false` | **Required.** Set to `true` to deploy the controllers with a dynamic quorum. |
| `kafka_controller_initial_voter` | `""` | **Required.** The one controller that creates the new quorum. It must be a `kafka_controller` inventory hostname, exactly as written in the inventory (not an IP address or a hostname alias). Every controller must use the same value. Only used on the first deployment. |

### Set automatically

When you run the playbooks, Ansible automatically templates the following. You do not set them yourself.

- `controller.quorum.bootstrap.servers` on every controller and broker. It lists every host in the `kafka_controller` group as `host:port`, and follows `hostname_aliasing_enabled` the same way the controllers' listeners do.
- `controller.quorum.auto.join.enable=true` on every controller.
- No `controller.quorum.voters`. That property is only used by a static quorum.

## Deploy

1. Copy the sample inventory and update the hostnames, connection settings, and security settings.
2. Set `kraft_dynamic_quorum_enabled: true` and `kafka_controller_initial_voter`.
3. Run the playbook as usual:

   ```bash
   ansible-playbook -i hosts.yml confluent.platform.all
   ```

## Verify

Run these on any controller. `<controller-port>` is the controller port, `kafka_controller_port` in your inventory (default `9093`).

```bash
# Every controller is a voter (Leader or Follower), with low Lag.
kafka-metadata-quorum --bootstrap-controller <controller-host>:<controller-port> \
  --command-config /etc/controller/client.properties describe --replication

# The quorum has a leader, and CurrentVoters lists every controller.
kafka-metadata-quorum --bootstrap-controller <controller-host>:<controller-port> \
  --command-config /etc/controller/client.properties describe --status

# kraft.version is 1.
kafka-features --bootstrap-controller <controller-host>:<controller-port> \
  --command-config /etc/controller/client.properties describe | grep kraft.version
```

In `describe --replication`, brokers always show as `Observer`. That is expected. Controllers should show as `Leader` or `Follower`.

## Troubleshooting

1. **The playbook fails with this error:**

   ```
   Forming a new KRaft dynamic quorum requires every kafka_controller to set the same
   kafka_controller_initial_voter, pointing to exactly one kafka_controller inventory host
   ```

   **Cause:** `kafka_controller_initial_voter` is empty, does not match a `kafka_controller` inventory hostname, or is set differently on some hosts.

   **Fix:** set it once, under `all.vars`, to a `kafka_controller` inventory hostname, then re-run.

2. **The playbook fails with this error:**

   ```
   Could not read the data directory state of every kafka_controller (one or more were
   unreachable). Founding a new dynamic quorum is unsafe until all controllers can be reached.
   ```

   **Cause:** at least one controller could not be reached during the first deployment.

   **Fix:** bring every controller online, then re-run.

3. **The playbook fails with this error:**

   ```
   Detected a running static KRaft cluster (kraft.version=0). Applying dynamic quorum
   configuration directly is unsafe.
   ```

   **Cause:** the cluster already runs a static quorum, so it is not a new cluster.

   **Fix:** use the [migration playbook](../migration/README.md) instead.

4. **A controller stays an Observer.**

   **Cause:** it has not caught up with the leader yet, or auto-join is off.

   **Fix:** check that its `Lag` is low in `describe --replication`, and that `controller.quorum.auto.join.enable=true` is in its `server.properties`. If you turned auto-join off, promote it by running this **on that controller**:

   ```bash
   kafka-metadata-quorum --bootstrap-controller <leader-host>:<controller-port> \
     --command-config /etc/controller/server.properties add-controller
   ```

## Next steps

- [Add controllers](../add_controllers/README.md)
- [Remove controllers](../remove_controllers/README.md)
