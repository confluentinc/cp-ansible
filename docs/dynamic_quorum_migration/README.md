# KRaft Static to Dynamic Quorum Migration

This guide explains how to migrate an existing Confluent Platform cluster from a **static KRaft quorum** (`kraft.version=0`) to a **dynamic KRaft quorum** (`kraft.version=1`, KIP-853), in place.

Static quorum uses `controller.quorum.voters` with a fixed set of controllers. Dynamic quorum uses `controller.quorum.bootstrap.servers` and lets you add and remove controllers without rebuilding the cluster.

The migration is a one-time, one-way operation, run by `playbooks/StaticToDynamicQuorumMigration.yaml`. It rolls the controllers and brokers one at a time, so the cluster keeps serving during the migration.

To deploy a new cluster with a dynamic quorum, see [Greenfield Deployment](../dynamic_quorum_greenfield/README.md) instead.

## Contents

- [Requirements](#requirements)
- [Why a migration playbook is needed](#why-a-migration-playbook-is-needed)
- [Migration flow](#migration-flow)
- [Sample inventory](#sample-inventory)
- [Before you start](#before-you-start)
- [Run the migration](#run-the-migration)
- [If the migration stops partway](#if-the-migration-stops-partway)
- [Verify](#verify)
- [After the migration](#after-the-migration)

## Requirements

- Confluent Platform **8.4.0 or later**, deployed by cp-ansible, running a static KRaft quorum.
- The controller quorum is healthy: it has a leader and every controller is a voter.
- The inventory the cluster was deployed with.

Single region and multi-region clusters use the same procedure. cp-ansible already configures `advertised.listeners` on the controllers, so multi-region clusters need no extra step.

## Why a migration playbook is needed

You cannot simply set `kraft_dynamic_quorum_enabled: true` and re-run the normal playbooks. `controller.quorum.bootstrap.servers` only works once `kraft.version` is `1`, so the feature must be upgraded first, while the controllers still run with `controller.quorum.voters`.

cp-ansible protects you from the wrong order. If you run the normal playbooks with `kraft_dynamic_quorum_enabled: true` on a running static cluster, they stop with:

```
Detected a running static KRaft cluster (kraft.version=0). Applying dynamic quorum
configuration directly is unsafe. Run playbooks/StaticToDynamicQuorumMigration.yaml ...
```

## Migration flow

```
Precheck  -->  Upgrade kraft.version  -->  Switch controllers  -->  Switch brokers
(health)       (metadata only,             (bootstrap.servers,      (bootstrap.servers,
               no restart)                 rolling restart)         rolling restart)
```

Properties at each stage:

| Stage | Controller config | Broker config | kraft.version |
|---|---|---|---|
| Start | `controller.quorum.voters` | `controller.quorum.voters` | 0 |
| After upgrading kraft.version | `controller.quorum.voters` | `controller.quorum.voters` | 1 |
| After switching controllers | `controller.quorum.bootstrap.servers` | `controller.quorum.voters` | 1 |
| After switching brokers | `controller.quorum.bootstrap.servers` | `controller.quorum.bootstrap.servers` | 1 |

The playbook runs these stages as plays. Each has its own tag:

| Stage | Tag | What happens |
|---|---|---|
| Precheck | `static_to_dynamic_quorum_precheck` | Checks that `kraft_dynamic_quorum_enabled` is `true` and runs the controller health check. |
| Upgrade kraft.version | `static_to_dynamic_quorum_feature_upgrade` | Runs `kafka-features upgrade --feature kraft.version=1` if it is `0`, then checks that it is `1`. No restart. |
| Switch controller config | `static_to_dynamic_quorum_controller_config` | Removes `controller.quorum.voters` and sets `controller.quorum.bootstrap.servers` and `controller.quorum.auto.join.enable` on every controller. |
| Restart controllers | `static_to_dynamic_quorum_controller_restart` | Restarts the controllers one at a time, with a health check after each. |
| Switch broker config | `static_to_dynamic_quorum_broker_config` | Removes `controller.quorum.voters` and sets `controller.quorum.bootstrap.servers` on every broker. |
| Restart brokers | `static_to_dynamic_quorum_broker_restart` | Restarts the brokers one at a time, with a health check after each. |

## Sample inventory

[`hosts.yml`](hosts.yml) is a single-region cluster with 3 controllers and 3 brokers. It is the inventory the cluster was deployed with, plus `kraft_dynamic_quorum_enabled: true`.

`kafka_controller_initial_voter` is **not** needed. It is only used when a new cluster is created.

## Before you start

Check the starting state on any controller:

```bash
# kraft.version is 0.
kafka-features --bootstrap-controller <controller-host>:9093 \
  --command-config /etc/controller/client.properties describe | grep kraft.version

# The quorum has a leader and every controller is a voter.
kafka-metadata-quorum --bootstrap-controller <controller-host>:9093 \
  --command-config /etc/controller/client.properties describe --replication
```

> **⚠ The kraft.version upgrade cannot be undone.** Kafka does not support downgrading `kraft.version` from `1` to `0`. Run the migration on a staging cluster first.

## Run the migration

1. Add `kraft_dynamic_quorum_enabled: true` to the inventory, under `all.vars`.
2. Run the migration playbook:

   ```bash
   ansible-playbook -i hosts.yml confluent.platform.StaticToDynamicQuorumMigration
   ```

Run the migration playbook before any other playbook that would render the new configuration.

## If the migration stops partway

Fix the cause and **re-run the same command**. Every stage is safe to repeat:

- If `kraft.version` is already `1`, the upgrade is skipped.
- Config lines that are already switched are left as they are.
- The restart stages restart the controllers and brokers again, one at a time. That causes another rolling restart, but no downtime.

You can also run only the remaining stages with `--tags`, for example `--tags static_to_dynamic_quorum_broker_config,static_to_dynamic_quorum_broker_restart`.

## Verify

```bash
# kraft.version is 1.
kafka-features --bootstrap-controller <controller-host>:9093 \
  --command-config /etc/controller/client.properties describe | grep kraft.version

# Every controller is a voter (Leader or Follower), with low Lag.
kafka-metadata-quorum --bootstrap-controller <controller-host>:9093 \
  --command-config /etc/controller/client.properties describe --replication

# Controllers and brokers use bootstrap.servers, and no longer use voters.
grep -E '^controller\.quorum\.(voters|bootstrap\.servers)' /etc/controller/server.properties
grep -E '^controller\.quorum\.(voters|bootstrap\.servers)' /etc/kafka/server.properties
```

## After the migration

- Keep `kraft_dynamic_quorum_enabled: true` in the inventory. The normal playbooks now render the dynamic quorum configuration.
- You can now [add controllers](../dynamic_quorum_add_controllers/README.md), [remove controllers](../dynamic_quorum_remove_controllers/README.md), and use [disaster recovery](../dynamic_quorum_disaster_recovery/README.md).
