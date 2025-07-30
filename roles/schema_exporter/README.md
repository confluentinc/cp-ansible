## Introduction

Ansible provides a simple way to deploy, manage, and configure the Confluent Platform services.
This role confluent.schema_exporter is used to configure schema exporter(s) for Confluent Platform Schema Registry.
Schema exporters allow you to export schemas from one Schema Registry to another, enabling cross-cluster schema replication.

## Usage

This role can be used to create and manage multiple schema exporters. Each exporter can be configured with different contexts, subjects, and authentication methods.

## Sample Configuration

Below is an example of how to configure a schema exporter in your inventory file:

```yaml
schema_exporter:
  - name: "dev-to-staging-exporter"
    context_type: "CUSTOM"
    remote_context: "dev-context"
    subjects: ["orders.*", "customers.*"]
    subject_rename_format: "dc_${subject}"
    kek_rename_format: "dc_${kek}"
    config:
      remote_schema_registry_endpoint: "http://dev-schema-registry:8081"
      remote_authentication_type: "basic"
      basic_username: "dev-user"
      basic_password: "dev-password"

  - name: "prod-backup-exporter"
    context_type: "AUTO"
    subjects: [*]  # Export all subjects
    config:
      remote_schema_registry_endpoint: "https://prod-schema-registry:8081"
      remote_authentication_type: "basic"
      basic_username: "prod-client-id"
      basic_password: "prod-client-secret"

  - name: "simple-exporter"
    context_type: "NONE"
    subjects: ["payment.*"]
    config:
      remote_schema_registry_endpoint: "http://remote-schema-registry:8081"
      remote_authentication_type: "basic"
      basic_username: "client-id"
      basic_password: "client-secret"
```

This example shows:
- Different context types (CUSTOM, AUTO, NONE)
- Subject filtering and renaming patterns
- Basic authentication configuration
- Custom configuration overrides

## Documentation

You can find the documentation for running CP-Ansible at https://docs.confluent.io/current/installation/cp-ansible/index.html.
You can find supported configuration variables in [VARIABLES.md](docs/VARIABLES.md)

## Contributing

If you would like to contribute to the CP-Ansible project, please refer to the [CONTRIBUTE.md](docs/CONTRIBUTING.md)

## License

[Apache 2.0](docs/LICENSE.md)
