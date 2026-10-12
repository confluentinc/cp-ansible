# KRaft Dynamic Quorum: Remove Controllers

This guide explains how to remove controllers from a running Confluent Platform cluster with a **dynamic KRaft controller quorum** (KIP-853). Use it to:

1. Reduce the number of controllers, for example from 5 to 3.
2. Decommission a controller host.
3. Replace a controller. Remove the old one first, then [add](../add_controllers/README.md) the new one.

Removing a controller is a manual procedure with `kafka-metadata-quorum remove-controller`, followed by an inventory change. cp-ansible does not automate it.

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
- Shell access to one of the controllers you are **keeping**. You run `kafka-metadata-quorum` there to find the controller's ids (step 1), remove it from the quorum (step 3), and check the result (step 4). The commands use that controller's `/etc/controller/client.properties`, which cp-ansible creates with the cluster's security settings.

To check that the quorum has a leader, run this on any controller:

```bash
kafka-metadata-quorum --bootstrap-controller <controller-host>:<controller-port> \
  --command-config /etc/controller/client.properties describe --status
```

`<controller-port>` is the controller port, `kafka_controller_port` in your inventory (default `9093`).

If the output shows a `LeaderId`, the quorum has a leader and you can continue.

If the command times out, that alone does not mean the quorum is lost. First rule out other causes:

- A wrong host or `<controller-port>`.
- A network or firewall problem between you and that controller.
- Wrong security settings in `client.properties`.

Try the command on another controller too. Only if every controller is reachable and none of them reports a leader is the quorum lost. In that case you cannot remove controllers. Use [Disaster Recovery](../disaster_recovery/README.md) instead.

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
- **Keep an odd number of voters**. 4 voters tolerate only 1 failure, the same as 3, but need one more voter for every metadata write.
- **If a controller is already down, remove that one first.** The quorum needs a majority of its voters to be **running**, not just listed. For example, with 3 voters where 1 is already down, removing one of the 2 running voters leaves 2 voters with only 1 running. That is not a majority of 2, so the quorum stops.

## Sample inventory

[`hosts.yml`](hosts.yml) shows a scale-down from 5 to 3 controllers. `kcontroller-4` and `kcontroller-5` were removed from the `kafka_controller` group. They are shown commented out.

## Remove the controllers

Run these steps for **one controller at a time**. The commands assume a package install with cp-ansible defaults. Adapt the paths and service names for archive installs, custom users, or rootless deployments.

### Step 1: find the controller's node id and directory id

Run this on a controller you are keeping:

```bash
kafka-metadata-quorum --bootstrap-controller <remaining-controller>:<controller-port> \
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

Run this on a controller you are keeping:

```bash
kafka-metadata-quorum --bootstrap-controller <remaining-controller>:<controller-port> \
  --command-config /etc/controller/client.properties \
  remove-controller --controller-id 9995 --controller-directory-id ezDCta58rqhUD_Fpr3UHJQ
```

If the removed controller was the leader, the remaining voters elect a new leader.

### Step 4: check the quorum

```bash
kafka-metadata-quorum --bootstrap-controller <remaining-controller>:<controller-port> \
  --command-config /etc/controller/client.properties describe --replication
```

The removed controller must no longer be listed as `Leader` or `Follower`. Repeat steps 1 to 4 for the next controller.

### Step 5: remove the hosts from the inventory

Remove the removed hosts from the `kafka_controller` group in your inventory.

### Step 6: decommission the removed hosts

**Why:** a removed host still has Kafka installed and still holds its KRaft data. If it is ever started again, for example after a reboot, by a playbook run with an old inventory, or when someone reuses the machine, it tries to rejoin the cluster, and auto-join adds it back as a voter.

**How:** on each removed host, after step 4 confirms it is out of the quorum, do one of these:

- Uninstall Confluent Platform from the host.
- Or keep it installed, but delete the controller data, so it has nothing to rejoin with:

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
# The remaining controllers are voters (Leader or Follower). The removed ones are gone.
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

   **Fix:** first confirm the host is really down by other means, such as the cloud console or hypervisor. A dead controller shows a `LastFetchTimestamp` that stops moving and a growing `Lag`, but lag alone does not prove it is gone. Then run steps 1, 3, and 4 from a remaining controller, and continue with step 5.
