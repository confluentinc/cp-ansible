# Development Guide

The following document will be a reference guide to coding standards of cp-ansible. It is written to be idempotent, meaning whatever you set in your inventory file, the playbook and roles should provision on your hosts, and can be run multiple times without causing unnecessary changes to those hosts.

## Table Of Contents

[Roles](#roles)

[Variables](#variables)

[Component Properties](#component-properties)

[Custom Filters](#custom-filters)

[Testing](#testing)

[Linting](#linting)

[Branching Model](#branching-model)

## Roles
Each Confluent component has its own role, with the name `confluent.<component_name>`. Within that role, `main.yml` is the entrypoint of all tasks run when the role is invoked. Here are a few tasks and coding standards associated with them:

```
- name: Write Service Overrides	(1)
  template:	(2)
    src: override.conf.j2
    dest: "{{ kafka_broker.systemd_override }}"	(3)
    mode: 0640	(4)
    owner: "{{kafka_broker_user}}"	(5)
    group: "{{kafka_broker_group}}"
  notify: restart kafka	(6)
```

1. A name clearly defining what the task accomplishes, using capital letters
2. Uses an idempotent ansible module whenever possible
3. Make use of variables instead of hard coding paths
4. For file creation use 0640 permission, for directory creation use 0750 permission. There are some exceptions, but be sure to secure files.
5. Proper ownership set
6. Trigger component restart handler when necessary

```
- name: Register Cluster
  include_tasks: register_cluster.yml	(1)
  when: kafka_connect_cluster_name|length > 0	(2)
```

1. Put sets of related tasks into their own task file and include them (not import)
2. Use conditionals to skip entire sets of tasks, or singular tasks

```
- name: Import the CA cert into the Keystore
  shell: |
    keytool -noprompt -keystore {{keystore_path}} \
      -storetype pkcs12 \
      -alias CARoot \
      -import -file {{ca_cert_path}} \
      -storepass {{keystore_storepass}}
  no_log: "{{mask_secrets|bool}}"	(1)
```

1. Passwords are not logged

## Variables

Variables are defined in multiple places within cp-ansible. Each role will have its own variables defined in `defaults/main.yml`. These variables can be used by tasks within that role, but not tasks from other roles. For variables that must be scoped to multiple roles there is the confluent.variables role. This role is set as a dependency for most of our roles:

```
# roles/confluent.ksql/meta/main.yml
---
dependencies:
  - role: confluent.variables
```

What this means is all the variables defined in the confluent.variables role are accessible in the ksql provisioning tasks. When defining variables ask these questions:

1. Is the variable only used by tasks in one role? Yes -> Define variable  in `<role>/defaults/main.yml` Ex:

```
### Root logger within ksqlDB's log4j config. Only honored if ksql_custom_log4j: true
ksql_log4j_root_logger: "INFO, stdout, main"
```

This log4j variable is only needed in the ksql’s log4j tasks.

2. Is the variable needed by multiple components and should be customizable by users? Yes -> Define variable in `confluent.variables/defaults/main.yml` Ex:

```
### Boolean to configure ksqlDB with TLS Encryption. Also manages Java Keystore creation
ksql_ssl_enabled: "{{ssl_enabled}}"
```

Now `ksql_ssl_enabled` may seem like its only relevant for ksql tasks, but control center needs to be aware of the ssl settings of ksqlDB in its provisioning logic

3. Is the variable needed my multiple components and should not be customizable by users? Yes -> Define variable in `confluent.variables/vars/main.yml`

```
ksql_service_name: "{{(confluent_package_version is version('5.5.0', '>=')) | ternary('confluent-ksqldb' , 'confluent-ksql')}}"
```

We need the ksql_service_name defined, because it gets used in many tasks, but we do not want users changing it.

### Setting variable names

Variables should be named with their component as a prefix and with underscores in between each word. Customizable variables should have its description in an annotation in the line above its definition. This annotation gets scraped into documentation. For example:

```
### Boolean to enable TLS encryption on Kafka jolokia metrics
kafka_broker_jolokia_ssl_enabled: "{{ ssl_enabled }}"
```

### Writing Variable Documentation
All customizable variables with proper annotations get written to the VARIABLES.md file via a simple python script. After editing variables or annotations be sure to run:

```
python doc.py
git add VARIABLES.md
git commit -m 'updated variable docs'
```

## Component Properties

A complex aspect of CP-Ansible is setting the correct properties for a component based on variables set in an inventory or group_vars. There are many logic gates that determine if a set of properties should be added to a component or not. All of the logic surrounding which properties get added to a component is defined in `roles/confluent.variables/vars/main.yml`. Here is an example:

```
schema_registry_properties:
  defaults:
    enabled: true
    properties:
      debug: 'false'
      schema.registry.group.id: schema-registry
      kafkastore.topic: _schemas
      kafkastore.topic.replication.factor: "{{schema_registry_default_internal_replication_factor}}"
      listeners: "{{schema_registry_http_protocol}}://0.0.0.0:{{schema_registry_listener_port}}"
      host.name: "{{inventory_hostname}}"
      inter.instance.protocol: "{{schema_registry_http_protocol}}"
      kafkastore.bootstrap.servers: "{{ groups['kafka_broker'] | default(['localhost']) | join(':' + kafka_broker_listeners[schema_registry_kafka_listener_name]['port']|string + ',') }}:{{kafka_broker_listeners[schema_registry_kafka_listener_name]['port']}}"
      confluent.license.topic: _confluent-license
  ssl:
    enabled: "{{schema_registry_ssl_enabled}}"
    properties:
      security.protocol: SSL
      ssl.keystore.location: "{{schema_registry_keystore_path}}"
      ssl.keystore.password: "{{schema_registry_keystore_storepass}}"
      ssl.key.password: "{{schema_registry_keystore_keypass}}"
```

Within the `schema_registry_properties` dictionary, there are subditionaries containing an enabled flag and a set of properties. In the above example, the ssl properties only need to be included when `schema_registry_ssl_enabled` is set to true. Below there is this line:

```
schema_registry_combined_properties: "{{schema_registry_properties | combine_properties}}"
```

A `combine_properties` filter is used to merge all "enabled" property sets. And finally we use one final merge to enable customizing the property sets:

```
schema_registry_final_properties: "{{ schema_registry_combined_properties | combine(schema_registry_custom_properties) }}"
```

The `schema_registry_final_properties` dictionary contains a set of enabled properties that can be fully customized by users via the customizable dictionary variable: `schema_registry_custom_properties`.

Now the schema_registry_final_properties property set eventually gets written to Schema Registry hosts at `/etc/schema-registry/schema-registry.properties`. But in tasks that may need access to certain properties they can be referenced like below:

```
- name: Set Permissions on Data Dirs
  file:
    path: "{{item}}"
    owner: "{{kafka_broker_user}}"
    group: "{{kafka_broker_group}}"
    state: directory
    mode: 0750
  with_items: "{{ kafka_broker_final_properties['log.dirs'].split(',') }}"
```

Because properties are fully customizable, it is important to use the final property setting in component tasks.

## Custom Filters

Ansible itself has a robust set of filters, but at times they do not fit cp-ansible’s needs. We have defined additional filters at `roles/confluent.variables/filter_plugins/filters.py`. In the below example we combine a custom filter `get_sasl_mechanisms` and our of the box ansible filters to set a variable:

```
kafka_broker_sasl_enabled_mechanisms: "{{ kafka_broker_listeners | get_sasl_mechanisms(sasl_protocol) | difference(['none']) | unique }}"
```

The `kafka_broker_sasl_enabled_mechanisms` variable is a list built out of all of the sasl mechanisms defined in the `kafka_broker_listeners` dictionary.

## Adding new features

When adding new features to cp-ansible, ask these questions:

1. What properties need to be added to enable this feature?

Put those properties into the `<component>_properties` dictionary in `roles/confluent.variables/vars/main.yml`.

2. What customizable variables should be defined to enable this feature?

See the Variables section.

3. What tasks need to be added to enable this feature on a host?

Maybe additional rolebindings need to be created or additional files put on a host. Put those tasks in `roles/confluent.<component>/tasks/main.yml`.

4. Does this feature need to be added to all components?

If you add a security feature to one component, like a schema registry authentication type, the other components that connect to Schema Registry now need to be able to authenticate. All features should be developed and tested with the full platform suite in mind.

## Testing

Refer to our [How to test guide](HOW_TO_TEST.md) for how to set up Molecule testing on your development machine. We run all scenarios within `roles/confluent.test/molecule/` before each release. When developing a new feature, we ask that you add a test case in molecule. You may be inclined to make a new scenario to test it, but please consider adding your feature test to an existing scenario to save time/resources during our release testing.

## Linting

All Yaml files in CP-Ansible will get run through a linter during our build process.
Pull requests with linting errors will not be accepted.

We are currently linting with:

- `yamllint`; latest stable version
- `ansible-lint`; latest stable 5.x.x version

To test/check manually you can run:

```shell
yamllimt .
ansible-lint *.yml
```

## Branching Model

Our `-post` branches are released branches and not meant for Pull Requests, unless there is a major bug. For bugs and minor features make PRs into the `.x` branches. For example if `6.1.1-post` is the latest version, make a bug fix PR into `6.1.x`, and expect that change to be released with the `6.1.2-post` branch. For major features we ask those get added into the next major release. To follow the example, make PRs for major features into `6.2.x` and expect them to be released with `6.2.0-post`. The CP-Ansible maintainers will handle merging your changes up through the various branches.
