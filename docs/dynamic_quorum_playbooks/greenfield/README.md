# KRaft Dynamic Quorum: Greenfield Deployment

This guide explains how to deploy a **new** Confluent Platform cluster with a **dynamic KRaft controller quorum** (KIP-853).

Greenfield means the cluster starts from scratch. It runs with a dynamic quorum (`kraft.version=1`) from day one. To move an existing static KRaft cluster to a dynamic quorum, see [Static to Dynamic Quorum Migration](../migration/README.md) instead.

## Contents

- [Static vs dynamic quorum](#static-vs-dynamic-quorum)
- [Requirements](#requirements)
- [Choosing the number of controllers](#choosing-the-number-of-controllers)
- [Sample inventory](#sample-inventory)
- [Variables](#variables)
- [Deploy](#deploy)
- [How the quorum is formed](#how-the-quorum-is-formed)
- [Verify](#verify)
- [Troubleshooting](#troubleshooting)
- [Next steps](#next-steps)

## Static vs dynamic quorum

| | Static quorum | Dynamic quorum |
|---|---|---|
| Controller config | `controller.quorum.voters` (fixed list of `id@host:port`) | `controller.quorum.bootstrap.servers` (list of `host:port`) |
| `kraft.version` | `0` | `1` |
| Add or remove controllers | Not supported without rebuilding the cluster | Supported at runtime |
| Disaster recovery | Not supported | [Supported](../disaster_recovery/README.md) |

Static quorum stays the default. Dynamic quorum is opt-in with `kraft_dynamic_quorum_enabled: true`.

## Requirements

- Confluent Platform **8.4.0 or later**.
- KRaft mode (`kraft_enabled: true`).
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

Use an odd number of controllers. Adding a fourth controller does not tolerate more failures than three.


## Sample inventory

[`hosts.yml`](hosts.yml) is a cluster with 3 controllers and 3 brokers.

## Variables

| Variable | Default | Description |
|---|---|---|
| `kraft_dynamic_quorum_enabled` | `false` | Set to `true` to deploy the controllers with a dynamic quorum. |
| `kafka_controller_initial_voter` | `""` | **Required.** The one controller that creates the new quorum. It must be a `kafka_controller` inventory hostname, exactly as written in the inventory (not an IP address or a hostname alias). Every controller must use the same value. Only used on the first deployment. |

`controller.quorum.bootstrap.servers` is built for you from the `kafka_controller` group, and it follows `hostname_aliasing_enabled` the same way the controllers' listeners do. `controller.quorum.auto.join.enable=true` is also set for you.

## Deploy

1. Copy the sample inventory and update the hostnames, connection settings, and security settings.
2. Set `kraft_dynamic_quorum_enabled: true` and `kafka_controller_initial_voter`.
3. Run the playbook as usual:

   ```bash
   ansible-playbook -i hosts.yml confluent.platform.all
   ```

## How the quorum is formed

1. **Checks.** cp-ansible checks that Confluent Platform is 8.4.0 or later and KRaft is enabled. It then checks the data directory of every controller. A new quorum is created only if **no** controller is formatted yet. If any controller cannot be reached, the run stops, because it cannot be sure the cluster is new.
2. **Initial voter.** The initial voter formats its storage with `--standalone`. It becomes the only voter of the new quorum.
3. **Other controllers.** Every other controller formats with `--no-initial-controllers` and the same cluster id. They start as observers.
4. **Auto-join.** Each observer catches up with the leader. Auto-join then promotes it to a voter.
5. **Brokers.** Brokers are deployed with `controller.quorum.bootstrap.servers` and connect to the quorum.

Re-running the playbook later is safe. Controllers that are already formatted are never formatted again. A wiped controller rejoins the existing quorum as an observer. It never creates a second quorum, even if it is the initial voter.

## Verify

Run these on any controller. With secrets protection, the controller's `client.properties` is not encrypted, so no master key is needed.

```bash
# Every controller is a voter (Leader or Follower), with low Lag.
kafka-metadata-quorum --bootstrap-controller <controller-host>:9093 \
  --command-config /etc/controller/client.properties describe --replication

# The quorum has a leader, and CurrentVoters lists every controller.
kafka-metadata-quorum --bootstrap-controller <controller-host>:9093 \
  --command-config /etc/controller/client.properties describe --status

# kraft.version is 1.
kafka-features --bootstrap-controller <controller-host>:9093 \
  --command-config /etc/controller/client.properties describe | grep kraft.version
```

In `describe --replication`, brokers always show as `Observer`. That is expected. Controllers should show as `Leader` or `Follower`.

## Troubleshooting

**The run fails with "requires every kafka_controller to set the same kafka_controller_initial_voter".** `kafka_controller_initial_voter` is empty, does not match a `kafka_controller` inventory hostname, or is set differently on some hosts. Set it once, under `all.vars`, to an inventory hostname.

**The run fails with "Could not read the data directory state of every kafka_controller".** At least one controller was unreachable during the first deployment. Bring it online and re-run.

**A controller stays an Observer.** Check that it caught up with the leader (low `Lag` in `describe --replication`), and that `controller.quorum.auto.join.enable=true` is in its `server.properties`. If you disabled auto-join, promote it by running this **on that controller**:

```bash
kafka-metadata-quorum --bootstrap-controller <leader-host>:9093 \
  --command-config /etc/controller/server.properties add-controller
```

**The run fails with "Detected a running static KRaft cluster".** The cluster already runs a static quorum. Use the [migration playbook](../migration/README.md) instead.

## Next steps

- [Add controllers](../add_controllers/README.md)
- [Remove controllers](../remove_controllers/README.md)
- [Disaster recovery](../disaster_recovery/README.md)
