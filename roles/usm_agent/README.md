## Introduction

Ansible provides a simple way to deploy, manage, and configure the Confluent Platform services.
This role confluent.usm_agent is used to deploy usm_agent node(s) for Confluent Platform.
We don't recommend using this role explicitly, we'd rather suggest to use the playbook confluent.platform.all

## Command Handler

This role can also run the **USM Agent Command Handler**, an optional sibling service (shipped in the same `confluent-usm-agent` package) that lets Confluent Cloud manage self-managed Kafka Connect clusters through the agent. It is **enabled by declaring one or more Connect clusters** in `usm_agent_command_handler_connect_clusters` — there is no separate on/off flag, mirroring how the agent itself is enabled by inventory-group membership. A full example is in [docs/sample_inventories/usm_agent/usm_agent_command_handler.yml](../../docs/sample_inventories/usm_agent/usm_agent_command_handler.yml).

## Documentation

You can find the documentation for running CP-Ansible at https://docs.confluent.io/current/installation/cp-ansible/index.html.
You can find supported configuration variables in [VARIABLES.md](docs/VARIABLES.md)

## Contributing

If you would like to contribute to the CP-Ansible project, please refer to the [CONTRIBUTE.md](docs/CONTRIBUTING.md)

## License

[Apache 2.0](docs/LICENSE.md)
