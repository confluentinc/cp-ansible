cp-ansible-vagrant
===

## Setup

### Vagrant plugins

```bash
vagrant plugin install vagrant-cachier vagrant-hostmanager vagrant-vbguest
```

### Define the hosts

Several profiles have already been defined in the `profiles/` directory.

By default, `kafka-1` will be started. You can override this behavior by exporting the `CP_PROFILE` variable prior to starting Vagrant. This variable does not persist and will need re-defined for each new terminal session.

All profiles have at least one broker and one zookeeper unless otherwise mentioned.

|Profile|Description|
|-|-|
|`kafka-1`||
|`kafka-cluster-3`|<ul><li>3 Zookeepers</li><li>3 Brokers</li></ul>|
|`kafka-registry-connect-1`|<ul><li>1 Schema Registry (on broker)</li><li>1 Distrubuted Kafka Connect Worker</li></ul>|
|`kafka-registry-connect-ksql-1`|<ul><li>1 Schema Registry (on broker)</li><li>1 Distrubuted Kafka Connect Worker</li><li>1 KSQL Server</li></ul>|
|`kafka-registry-connect-ksql-c3-1`|<p><i>Requires at least 16 GB RAM</i><ul><li>1 Schema Registry (on broker)</li><li>1 Distrubuted Kafka Connect Worker</li><li>1 KSQL Server</li><li>1 Confluent Control Center (C3)</li></ul>|
|`kafka-rest-1`|<ul><li>1 Kafka REST Proxy</li></ul>|
|`kafka-sslCA-1`|<ul><li>1 Certificate Authority</li></ul>|
|`kafka-tools-1`|<ul><li>1 Kafka Tools Server</li></ul>|

Example running a different profile

```bash
export CP_PROFILE=kafka-registry-connect-1
vagrant up
```

New profiles can be added following the YAML format of the other profiles. If not specified, the default memory is `1536` (MB) and default CPU is `1`. If a port value mapping is not specified, it'll create a direct port forward to the host for the given key. The `vars` key will be assigned to the Ansible host variables.

### Start Vagrant

By default, this starts up a `bento/centos-7` Vagrant box with `PLAINTEXT` security between all services.

```bash
vagrant up
```

To use a different OS, set the `VAGRANT_BOX` variable. For example, to start Ubuntu 16.04

```bash
VAGRANT_BOX=ubuntu/xenial64 vagrant up
```

To set a different security mode, find the sibling folders next to `roles/` in the parent directory that contain an `all.yml` and set the name of that directory to the `CP_SECURITY_MODE` variable. For example, to use the `sasl_ssl/all.yml` playbook file

```bash
CP_SECURITY_MODE=sasl_ssl vagrant up
```

## Provisioning

By default, all services are provisioned according to their machine groups and targets defined in the `all.yml` file for the chosen security mode playbook.
The `ANSIBLE_LIMIT` variable can be used override this behavior to target specific machines. Its syntax matches the `--limit` flag or host pattern options of `ansible` and `ansible-playbook` commands.

### Provision a group

Group names can be found in the Ansible playbook directory set by `CP_SECURITY_MODE`. For example, if we wanted to re-provision all the Kafka brokers:

```bash
ANSIBLE_LIMIT=broker vagrant provision
```

### Provision some hosts

The machines are labelled in the `profiles/` directory. If we wanted to re-provision two machines in the `zookeeper` group, `zk0` and `zk1`:   

```bash
ANSIBLE_LIMIT='zk[01]' vagrant provision
```

## References

- [Using Ansible and Vagrant](https://docs.ansible.com/ansible/latest/scenario_guides/guide_vagrant.html)
