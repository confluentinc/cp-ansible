# KRaft Static-to-Dynamic Quorum Migration

Migrates an existing **static** KRaft cluster (`controller.quorum.voters`, `kraft.version=0`) to a
**dynamic** quorum (KIP-853: `controller.quorum.bootstrap.servers`, `kraft.version=1`) in place, with
no cluster rebuild. Works for single-region and MRC. Requires **Confluent Platform 8.4.0 or later**.

## Why a dedicated playbook

You cannot simply set `kraft_dynamic_quorum_enabled: true` and re-run `all.yml`.
`controller.quorum.bootstrap.servers` is only valid once `kraft.version` is finalized at `1`, so the
feature must be upgraded **before** the configuration is switched. A normal run that applies dynamic
configuration to a `kraft.version=0` cluster is blocked by a guard in the `kafka_controller` role.

The migration playbook performs the steps in the required order:

1. **Precheck** — confirm the quorum is reachable and read the current `kraft.version`.
2. **Feature upgrade** — `kafka-features upgrade --feature kraft.version=1` (metadata-only, no
   restart). Skipped if already `1`.
3. **Controller switch** — re-render controller config to `controller.quorum.bootstrap.servers`
   and roll the controllers one at a time.
4. **Broker switch** — re-render broker config to `controller.quorum.bootstrap.servers` and roll
   the brokers one at a time.
5. **Verify** — confirm `kraft.version=1`, quorum healthy, all controllers are voters.

## Prerequisites

- A running static KRaft cluster deployed by cp-ansible on CP 8.4.0+.
- In your inventory, set the dynamic-quorum end state:
  ```yaml
  all:
    vars:
      kraft_dynamic_quorum_enabled: true
      kafka_controller_initial_voter: <one of your kafka_controller hosts>
  ```
  (`kafka_controller_initial_voter` selects the `--standalone` node for greenfield; on migration it
  is required by validation but no reformat occurs.)

## Run

```bash
ansible-playbook -i hosts.yml confluent.platform.kraft_static_to_dynamic_migration
```

The playbook is idempotent: re-running after a completed migration is a no-op (feature already `1`,
config already `bootstrap.servers`, no restarts).

## Notes

- On the `kraft.version` upgrade, each controller's `DirectoryId` changes from the placeholder
  `AAAAAAAAAAAAAAAAAAAAAA` to a unique UUID. This is expected and is what later
  `kafka-metadata-quorum remove-controller` commands reference.
- Rollback (`kraft.version` 1 → 0) is not supported by Kafka; the upgrade is one-way.
- After migration, keep `kraft_dynamic_quorum_enabled: true` in the inventory so subsequent normal
  runs continue to render dynamic-quorum configuration.
