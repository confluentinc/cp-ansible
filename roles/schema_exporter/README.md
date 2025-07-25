## Introduction

Ansible provides a simple way to deploy, manage, and configure the Confluent Platform services.
This role confluent.schema_exporter is used to configure schema exporter(s) for Confluent Platform Schema Registry.
Schema exporters allow you to export schemas from one Schema Registry to another, enabling cross-cluster schema replication.

## Usage

This role can be used to create and manage multiple schema exporters. Each exporter can be configured with different contexts, subjects, and authentication methods.

## Documentation

You can find the documentation for running CP-Ansible at https://docs.confluent.io/current/installation/cp-ansible/index.html.
You can find supported configuration variables in [VARIABLES.md](docs/VARIABLES.md)

## Contributing

If you would like to contribute to the CP-Ansible project, please refer to the [CONTRIBUTE.md](docs/CONTRIBUTING.md)

## License

[Apache 2.0](docs/LICENSE.md)
