cp-ansible-vagrant
===

## Setup

### Vagrant plugins

```bash
vagrant plugin install vagrant-cachier vagrant-hostmanager vagrant-vbguest
```

## Provisioning 

### Provision a group

```bash
ANSIBLE_LIMIT=broker vagrant provision
```

### Provision some hosts

```
ANSIBLE_LIMIT='cp.zk[01].vagrant' vagrant provision
```

