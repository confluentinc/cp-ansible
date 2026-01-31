# C3 Next Gen Active Active Setup

This directory contains a sample inventory file for setting up Confluent Platform with Control Center Next Gen in an active-active configuration for high availability.

## Overview

The C3 Next Gen Active Active setup demonstrates how to deploy multiple Control Center Next Gen instances that can work together to provide:

- **High Availability**: If one C3 Next Gen node fails, the other continues to operate

## Architecture

This sample configuration includes:

- **Kafka Controller**: 3 nodes for high availability
- **Kafka Brokers**: 3 nodes for data replication and fault tolerance
- **Control Center Next Gen**: 2 nodes in active-active configuration
  - Node 1: C3 Next Gen instance (ID: 1)
  - Node 2: C3 Next Gen instance (ID: 2)

## Prerequisites

Before using this sample, ensure you have:

1. **Minimum 5 hosts**:
   - 3 hosts for Kafka Controller nodes
   - 3 hosts for Kafka Broker nodes  
   - 2 hosts for Control Center Next Gen nodes

2. **Java 17** installed on all hosts

3. **Network connectivity** between all hosts

4. **DNS resolution** or `/etc/hosts` entries for all hostnames

5. **Ansible** installed on the control machine

6. **SSH access** configured to all target hosts

## Configuration

### 1. Update Host Information

Edit the `c3-next-gen-active-active.yml` file and update the hostnames to match your environment:

```yaml
kafka_controller:
  hosts:
    controller[01:03].confluent.io:  # Update these hostnames

kafka_broker:
  hosts:
    kafka-broker[01:03].confluent.io:  # Update these hostnames

control_center_next_gen:
  hosts:
    control-center-next-gen-node-1.confluent.io:  # Update this hostname
    control-center-next-gen-node-2.confluent.io:  # Update this hostname
```

### 2. Update Telemetry URLs

Update the telemetry exporter URLs to point to your actual C3 Next Gen nodes:

```yaml
kafka_broker_custom_properties:
  confluent.telemetry.exporter._c3-2.client.base.url: http://control-center-next-gen-node-2.confluent.io:9090/api/v1/otlp
```

### 3. Configure Connection Settings

Update the connection settings in the `all.vars` section:

```yaml
all:
  vars:
    ansible_user: ec2-user  # Update to your SSH user
    ansible_ssh_private_key_file: /home/ec2-user/guest.pem  # Update to your SSH key path
```

## Deployment

### Version-Specific Deployment Commands

**Important**: The deployment commands vary based on the Confluent Platform version you're using.

#### For Confluent Platform 8.0.0 and 8.0.1

```bash
# Install all components
ansible-playbook -i c3-next-gen-active-active.yml confluent.platform.all --skip-tags 'validate'

# Or install components individually:
ansible-playbook -i c3-next-gen-active-active.yml confluent.platform.all --tags kafka_controller --skip-tags 'validate'
ansible-playbook -i c3-next-gen-active-active.yml confluent.platform.all --tags kafka_broker --skip-tags 'validate'
ansible-playbook -i c3-next-gen-active-active.yml confluent.platform.all --tags control_center_next_gen --skip-tags 'validate'
```

#### For Confluent Platform 8.0.2, 8.1.0 and above

For active-active C3 Next Gen deployments with multiple nodes, you need to skip the host count validation by adding the following variable to your inventory file:

```yaml
all:
  vars:
    skip_control_center_next_gen_host_count_validation: true
```

Then run:

```bash
# Install all components
ansible-playbook -i c3-next-gen-active-active.yml confluent.platform.all

# Or install components individually:
ansible-playbook -i c3-next-gen-active-active.yml confluent.platform.all --tags kafka_controller
ansible-playbook -i c3-next-gen-active-active.yml confluent.platform.all --tags kafka_broker
ansible-playbook -i c3-next-gen-active-active.yml confluent.platform.all --tags control_center_next_gen
```

## Configuration Details

### Telemetry Exporters

The sample configures telemetry exporters on both Kafka Controller and Kafka Broker nodes to send metrics to the C3 Next Gen nodes:

- **C3-1 Exporter**: Sends metrics to the first C3 Next Gen node
- **C3-2 Exporter**: Sends metrics to the second C3 Next Gen node (with Prometheus integration)

### Control Center Next Gen Configuration

- **Node 1**: Basic configuration with ID 1
- **Node 2**: Enhanced configuration with:
  - ID 2
  - Prometheus integration on port 9090
  - Alertmanager integration on port 9093


## Troubleshooting

### Validation Errors

If you encounter validation errors during deployment:

- **For versions 8.0.0-8.0.1**: Use `--skip-tags 'validate'`
- **For versions 8.0.2+**: Add `skip_control_center_next_gen_host_count_validation: true` to the `all.vars` section of your inventory file
