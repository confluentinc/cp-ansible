## Introduction

Ansible provides a simple way to deploy, manage, and configure the Confluent Platform services.
This role confluent.schema_exporter is used to configure schema exporter(s) for Confluent Platform Schema Registry.
Schema exporters allow you to export schemas from one Schema Registry to another, enabling cross-cluster schema replication.

## Usage

This role can be used to create and manage multiple schema exporters. Each exporter can be configured with different contexts, subjects, and authentication methods.

### Inventory Configuration

Configure schema exporters in your inventory:

```yaml
schema_exporter:
  - name: production-exporter
    context_type: CUSTOM
    remote_context: production-context
    subjects: ["user-events", "order-events"]
    config:
      remote_schema_registry_endpoint: https://remote-sr.example.com:8081
      remote_authentication_type: basic
      basic_username: client-id
      basic_password: client-secret
  - name: staging-exporter
    context_type: AUTO
    subjects: []
    config:
      remote_schema_registry_endpoint: https://staging-sr.example.com:8081
```

### Configuration Options

- **name**: Unique name for the exporter
- **context_type**: Context type (AUTO, CUSTOM, NONE, DEFAULT)
- **remote_context**: Context name (required when context_type is CUSTOM)
- **subjects**: List of subjects to export (empty list exports all subjects)
- **config**: Required configuration including remote endpoint and authentication
- **config_overrides**: Additional configuration overrides

## Documentation

You can find the documentation for running CP-Ansible at https://docs.confluent.io/current/installation/cp-ansible/index.html.
You can find supported configuration variables in [VARIABLES.md](docs/VARIABLES.md)

## Contributing

If you would like to contribute to the CP-Ansible project, please refer to the [CONTRIBUTE.md](docs/CONTRIBUTING.md)

## License

[Apache 2.0](docs/LICENSE.md)
