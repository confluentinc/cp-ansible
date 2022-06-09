# Refer to this doc to get an overview of all tags used inside the cp-ansible project

Refer https://docs.ansible.com/ansible/latest/user_guide/playbooks_tags.html to know more about ansible tags
While running cp-ansible, you can use --tags or --skip-tags to run or skip any specific tag. E.g.
ansible-playbook -i hosts.yml confluent.platform.all --tags 'tag-name'
ansible-playbook -i hosts.yml confluent.platform.all --skip-tags 'tag-name'

***

### Tag - always

Description: To make a task/play run always regardless of the tag specified. It's a default ansible tag.

***

### Tag - certificate_authority

Description: To generate the certificate authority (CA) if TLS encryption is enabled and using self-signed certificates.

***

### Tag - common

Description: Runs the common role. For performing all tasks common to the components.

***

### Tag - configuration

Description: For all configuration related tasks. Creating, editing, changing permissions for component config files.

***

### Tag - control_center

Description: For all control center tasks - installing, configuring. Runs the control_center role.

***

### Tag - filesystem

Description: For all filesystem related tasks across components - creating directory, setting permissions.

***

### Tag - health_check

Description: For health check of all components. Runs health_check.yml inside all component roles.

***

### Tag - kafka_broker

Description: For all kafka broker tasks - installing, configuring. Runs the kafka_broker role.

***

### Tag - kafka_connect

Description: For all kafka connect tasks - installing, configuring. Runs the kafka_connect role.

***

### Tag - kafka_connect_replicator

Description: For all kafka connect replicator tasks - installing, configuring. Runs the kafka_connect_replicator role.

***

### Tag - kafka_rest

Description: For all kafka rest tasks - installing, configuring. Runs the kafka_rest role.

***

### Tag - ksql

Description: For all ksql tasks - installing, configuring. Runs the ksql role.

***

### Tag - log

Description: For all log and log4j related tasks.

***

### Tag - masterkey

Description: To generate secrets protection masterkey if secrets protection enabled.

***

### Tag - package

Description: This is applied to all package installation related tasks. Skip this if you don't want to reinstall.

***

### Tag - privileged

Description: This tag is applied to tasks which require root access. Skip this tag if running without root permission.

***

### Tag - schema_registry

Description: For all schema registry tasks - installing, configuring. Runs the schema_registry role.

***

### Tag - ssl

Description: To run role ssl for all components. Run when anything related to keys/certs are changed.

***

### Tag - sysctl

Description: For sysctl related tasks on the kafka broker.

***

### Tag - systemd

Description: For all component service and systemd related tasks.

***

### Tag - validate

Description: To validate all of the aforementioned things.

***

### Tag - validate_ansi_version

Description: To verify if supported ansible versions are being used.

***

### Tag - validate_disk_usage

Description: Pre flight check. To check free space for package installation.

***

### Tag - validate_hash_merge

Description: To check if hash merge is enabled in ansible.cfg.

***

### Tag - validate_internet_access

Description: Pre flight check. To check internet access for confluent packages/archive.

***

### Tag - validate_memory_usage

Description: Pre flight check. To validate if enough free memory is available to install components on the host machines.

***

### Tag - validate_memory_usage_control_center

Description: Pre flight check. As name suggests.

***

### Tag - validate_memory_usage_kafka_broker

Description: Pre flight check. As name suggests.

***

### Tag - validate_memory_usage_kafka_connect

Description: Pre flight check. As name suggests.

***

### Tag - validate_memory_usage_kafka_connect_replicator

Description: Pre flight check. As name suggests.

***

### Tag - validate_memory_usage_kafka_rest_proxy

Description: Pre flight check. As name suggests.

***

### Tag - validate_memory_usage_ksql

Description: Pre flight check. As name suggests.

***

### Tag - validate_memory_usage_schema_registry

Description: Pre flight check. As name suggests.

***

### Tag - validate_memory_usage_zookeeper

Description: Pre flight check. As name suggests.

***

### Tag - validate_os_version

Description: Pre flight check. To confirm supported versions of rhel, ubuntu or debian.

***

### Tag - validate_ssl_keys_certs

Description: Pre flight check. Validate keys and certs if custom_certs provided.

***

### Tag - validate_tmp_access

Description: Pre flight check. Check if /tmp directory exists or not.

***

### Tag - zookeeper

Description: For all zookeeper tasks - installing, configuring. Runs the zookeeper role.

***