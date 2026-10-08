# KRaft Dynamic Quorum: Remove Controllers

This guide explains how to remove controllers from a running Confluent Platform cluster with a **dynamic KRaft controller quorum** (KIP-853). Use it to shrink the quorum, to decommission a host, or as the first step of replacing a controller.

Removing a controller is a manual procedure with `kafka-metadata-quorum remove-controller`, followed by a normal playbook run. cp-ansible does not automate it, which matches Confluent for Kubernetes.

## Contents

- [Requirements](#requirements)
- [Before you remove a controller](#before-you-remove-a-controller)
- [Sample inventory](#sample-inventory)
- [Remove the controllers](#remove-the-controllers)
- [Why the controller must stay stopped](#why-the-controller-must-stay-stopped)
- [Verify](#verify)
- [Troubleshooting](#troubleshooting)

## Requirements

- The cluster runs a dynamic quorum (`kraft_dynamic_quorum_enabled: true`).
- The quorum is healthy: it has a leader.
- Access to a remaining controller to run `kafka-metadata-quorum`.

If the quorum has no leader, you cannot remove controllers. Use [Disaster Recovery](../dynamic_quorum_disaster_recovery/README.md) instead.

## Before you remove a controller

The quorum needs a majority of voters to work. For `N` voters, the majority is `floor(N / 2) + 1`.

| Voters | Majority | Failures tolerated |
|---|---|---|
| 5 | 3 | 2 |
| 4 | 3 | 1 |
| 3 | 2 | 1 |
| 2 | 2 | 0 |
| 1 | 1 | 0 |

- **Remove one controller at a time**, and check the quorum after each one.
- **Keep an odd number of voters** in a single region. 4 voters tolerate only 1 failure, the same as 3, but need one more voter for every metadata write.
- **Keep enough voters running.** Count the voters that are actually up, not only the ones in the voter set. Removing a running voter while another one is already down can leave the quorum without a majority.
- **To replace a controller, remove the old one first**, then [add](../dynamic_quorum_add_controllers/README.md) the new one.

## Sample inventory

[`hosts.yml`](hosts.yml) shows a 5-controller cluster after removing `kcontroller-4` and `kcontroller-5`. The removed hosts are taken out of `kafka_controller`.

## Remove the controllers

Run these steps for **one controller at a time**. The commands assume a package install with cp-ansible defaults. Adapt the paths and service names for archive installs, custom users, or rootless deployments.

### Step 1: find the controller's node id and directory id

Run this on any remaining controller:

```bash
kafka-metadata-quorum --bootstrap-controller <remaining-controller>:9093 \
  --command-config /etc/controller/client.properties describe --replication
```

```
NodeId  DirectoryId             LogEndOffset  Lag  LastFetchTimestamp  LastCaughtUpTimestamp  Status
9991    lQ92sYMTnYHE2pVWw7bJ9w  33940         0    1777643877128       1777643877128          Leader
9992    jknA-u7XR86Vkxnc2RGWgw  33940         0    1777643876933       1777643876933          Follower
9993    yRXWy70qdjW4yh_qzePwzg  33940         0    1777643876933       1777643876933          Follower
9994    kNxsHyUj3x0pKeAdMowmbQ  33940         0    1777643876931       1777643876931          Follower
9995    ezDCta58rqhUD_Fpr3UHJQ  33940         0    1777643876930       1777643876930          Follower
```

Note the `NodeId` and `DirectoryId` of the controller to remove. In this example, `kcontroller-5` is node `9995`.

### Step 2: stop and disable KRaft on the controller to remove

Run this **on the controller you are removing**:

```bash
sudo systemctl disable --now confluent-kcontroller
```

The controller must stay stopped. See [Why the controller must stay stopped](#why-the-controller-must-stay-stopped).

### Step 3: remove the controller from the quorum

Run this on any remaining controller:

```bash
kafka-metadata-quorum --bootstrap-controller <remaining-controller>:9093 \
  --command-config /etc/controller/client.properties \
  remove-controller --controller-id 9995 --controller-directory-id ezDCta58rqhUD_Fpr3UHJQ
```

If the removed controller was the leader, the remaining voters elect a new leader.

### Step 4: check the quorum

```bash
kafka-metadata-quorum --bootstrap-controller <remaining-controller>:9093 \
  --command-config /etc/controller/client.properties describe --replication
```

The removed controller must no longer be listed as `Leader` or `Follower`. Repeat steps 1 to 4 for the next controller.

### Step 5: remove the hosts from the inventory

Delete the removed hosts from `kafka_controller`. If `kafka_controller_initial_voter` points to a removed host, you can point it to any remaining controller. It is only used on the first deployment.

### Step 6: update the remaining controllers and the brokers

```bash
ansible-playbook -i hosts.yml confluent.platform.kafka_controller
ansible-playbook -i hosts.yml confluent.platform.kafka_broker
```

These restart the remaining controllers and the brokers one at a time, so their `controller.quorum.bootstrap.servers` no longer lists the removed controllers. The cluster keeps working without this step, so you can schedule it later.

### Step 7: decommission the removed hosts

Before you reuse or delete a removed host, uninstall Confluent Platform or empty its controller data directory (default `/var/lib/controller/data`). Then it cannot join the cluster again by accident.

## Why the controller must stay stopped

cp-ansible enables auto-join (`controller.quorum.auto.join.enable=true`). Auto-join adds any running, caught-up controller back to the voter set. So:

- If you run `remove-controller` while the controller is still running, it is added back right away. The removal has no lasting effect.
- If you leave a removed host in the inventory, the next playbook run starts it again, and auto-join adds it back.

That is why you stop and disable the controller before removing it, take it out of the inventory, and decommission it. This is how auto-join works in Kafka. It is not a cp-ansible limitation.

## Verify

```bash
# The remaining controllers are voters (Leader or Follower). The removed ones are gone.
kafka-metadata-quorum --bootstrap-controller <remaining-controller>:9093 \
  --command-config /etc/controller/client.properties describe --replication

# CurrentVoters lists only the remaining controllers.
kafka-metadata-quorum --bootstrap-controller <remaining-controller>:9093 \
  --command-config /etc/controller/client.properties describe --status
```

## Troubleshooting

**The removed controller shows up as a voter again.** It was still running, or it was started again, and auto-join added it back. Stop and disable it, remove it from the inventory, and run step 3 again.

**`remove-controller` fails with an unknown voter or wrong directory id.** The `NodeId` and `DirectoryId` must match the same row of `describe --replication`. Run step 1 again and copy both values from the same line.

**A controller host is lost and cannot be stopped.** A lost host is already stopped. Run steps 1, 3, and 4 from a remaining controller, then continue with step 5. The dead controller is listed with a `LastFetchTimestamp` that stops moving and a growing `Lag`. Lag alone does not mean a controller is gone, so confirm the host is really down by other means first.
