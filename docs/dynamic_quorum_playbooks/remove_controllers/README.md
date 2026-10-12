# KRaft Dynamic Quorum: Remove Controllers

This guide explains how to remove a controller from a running Confluent Platform cluster with a **dynamic KRaft controller quorum** (KIP-853). Use it when a controller is lost, or when its host is being retired. Removing it is the first step of replacing it:

1. Remove the old controller from the quorum, with this guide.
2. Add the replacement, with [Add Controllers](../add_controllers/README.md).

Reducing the number of controllers (scale-down) is not supported.

Removing a controller is a manual procedure with `kafka-metadata-quorum remove-controller`. cp-ansible does not automate it.

## Contents

- [Requirements](#requirements)
- [Sample inventory](#sample-inventory)
- [Remove the controller](#remove-the-controller)
- [Why the controller must stay stopped](#why-the-controller-must-stay-stopped)
- [Verify](#verify)
- [Troubleshooting](#troubleshooting)

## Requirements

- The cluster runs a dynamic quorum (`kraft_dynamic_quorum_enabled: true`).
- The quorum is healthy: it has a leader.
- Shell access to one of the controllers you are **keeping**. You run `kafka-metadata-quorum` there to find the controller's ids (step 1), remove it from the quorum (step 3), and check the result (step 4). The commands use that controller's `/etc/controller/client.properties`, which cp-ansible creates with the cluster's security settings.

To check that the quorum has a leader, run this on any controller:

```bash
kafka-metadata-quorum --bootstrap-controller <controller-host>:<controller-port> \
  --command-config /etc/controller/client.properties describe --status
```

`<controller-port>` is the controller port, `kafka_controller_port` in your inventory (default `9093`).

If the output shows a `LeaderId`, the quorum has a leader and you can continue.

If the command times out, rule out common causes (incorrect port, network or firewall issues, and so on), or contact Confluent Support for assistance.

In a disaster where controllers are lost, use the [Disaster Recovery](../disaster_recovery/README.md) runbook instead.

## Sample inventory

[`hosts.yml`](hosts.yml) shows a 3-controller cluster where `kcontroller-2` is replaced:

- `kcontroller-2` was removed from the quorum, then removed from the `kafka_controller` group. It is shown commented out.
- `kcontroller-4` is its replacement, added with the [Add Controllers](../add_controllers/README.md) guide.
- Every controller has `node_id` set, so removing a host from the middle of the list does not change the node ids of the others. See [step 5](#step-5-update-the-inventory).

## Remove the controller

The commands assume a package install with cp-ansible defaults. Adapt the paths and service names for archive installs, custom users, or rootless deployments. If more than one controller needs removing, remove one at a time, and check the quorum after each one.

### Step 1: find the controller's node id and directory id

Run this on a controller you are keeping:

```bash
kafka-metadata-quorum --bootstrap-controller <remaining-controller>:<controller-port> \
  --command-config /etc/controller/client.properties describe --replication
```

```
NodeId  DirectoryId             LogEndOffset  Lag  LastFetchTimestamp  LastCaughtUpTimestamp  Status
9991    lQ92sYMTnYHE2pVWw7bJ9w  33940         0    1777643877128       1777643877128          Leader
9992    jknA-u7XR86Vkxnc2RGWgw  33808         132  1777643849923       1777643849923          Follower
9993    yRXWy70qdjW4yh_qzePwzg  33940         0    1777643876933       1777643876933          Follower
```

Note the `NodeId` and `DirectoryId` of the controller to remove. In this example, `kcontroller-2` is node `9992`.

### Step 2: stop and disable KRaft on the controller to remove

If the host is lost, it is already down. Confirm it is actually down, then skip this step.

Otherwise, run this **on the controller you are removing**:

```bash
sudo systemctl disable --now confluent-kcontroller
```

If the service name was changed, use the value of `kafka_controller_service_name` instead of `confluent-kcontroller`.

The controller must stay stopped. See [Why the controller must stay stopped](#why-the-controller-must-stay-stopped).

### Step 3: remove the controller from the quorum

Run this on a controller you are keeping:

```bash
kafka-metadata-quorum --bootstrap-controller <remaining-controller>:<controller-port> \
  --command-config /etc/controller/client.properties \
  remove-controller --controller-id 9992 --controller-directory-id jknA-u7XR86Vkxnc2RGWgw
```

If the removed controller was the leader, the remaining voters elect a new leader.

### Step 4: check the quorum

```bash
kafka-metadata-quorum --bootstrap-controller <remaining-controller>:<controller-port> \
  --command-config /etc/controller/client.properties describe --replication
```

The removed controller must no longer be listed as `Leader` or `Follower`.

### Step 5: update the inventory

1. **Pin the node ids first.** If `node_id` is not set, cp-ansible works out each controller's node id from its position in the `kafka_controller` group (`9991`, `9992`, and so on). Removing a host from the middle of the list would then give every controller after it a different node id on the next playbook run, and those controllers would fail to start. So, on every controller you are keeping, set `node_id` to its current node id, as shown in step 1. In the sample inventory, `kcontroller-3` keeps `node_id: 9993`.
2. **Remove the host** from the `kafka_controller` group in your inventory.

### Step 6: decommission the removed host

Skip this step if the host is lost.

**Why:** a retired host still holds its KRaft data, including the cluster id and its node id. If the service is started on it again, for example after a reboot, by a playbook run with an old inventory, or when someone reuses the machine, it tries to rejoin the cluster, and auto-join adds it back as a voter.

**How:** after step 4 confirms it is out of the quorum, delete the controller data so it has nothing to rejoin with:

```bash
sudo rm -rf /var/lib/controller/data/*
```

KRaft is already stopped and disabled from step 2.

## Why the controller must stay stopped

cp-ansible enables auto-join (`controller.quorum.auto.join.enable=true`). Auto-join adds any running, caught-up controller back to the voter set. So:

- If you run `remove-controller` while the controller is still running, it is added back right away. The removal has no lasting effect.
- If you leave a removed host in the inventory, the next playbook run starts it again, and auto-join adds it back.

That is why you stop and disable the controller before removing it, take it out of the inventory, and decommission it.

## Verify

```bash
# The remaining controllers are voters (Leader or Follower). The removed one is gone.
kafka-metadata-quorum --bootstrap-controller <remaining-controller>:<controller-port> \
  --command-config /etc/controller/client.properties describe --replication

# CurrentVoters lists only the remaining controllers.
kafka-metadata-quorum --bootstrap-controller <remaining-controller>:<controller-port> \
  --command-config /etc/controller/client.properties describe --status
```

## Troubleshooting

1. **The removed controller shows up as a voter again.**

   **Cause:** it was still running, or it was started again, and auto-join added it back.

   **Fix:** stop and disable it (step 2), remove it from the inventory (step 5), then run step 3 again.

2. **`remove-controller` fails with an unknown voter or a wrong directory id.**

   **Cause:** the `NodeId` and `DirectoryId` do not come from the same row of `describe --replication`.

   **Fix:** run step 1 again and copy both values from the same line.

3. **A controller host is lost and cannot be stopped.**

   **Cause:** its machine or disk is gone, so it is already down.

   **Fix:** confirm that the host is actually down. Then contact Confluent Support, who will help you with the disaster recovery.

4. **Controllers fail to start after the host is removed from the inventory.**

   **Cause:** `node_id` was not pinned, so removing a host from the middle of the `kafka_controller` group changed the node ids of the controllers after it.

   **Fix:** set `node_id` on each controller back to the node id stored on its disk (`node.id` in `/var/lib/controller/data/meta.properties`), then re-run the controller playbook.
