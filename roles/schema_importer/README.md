## Introduction

Ansible provides a simple way to deploy, manage, and configure the Confluent Platform services.
This role confluent.schema_importer is used to configure schema importer(s) for Confluent Platform Schema Registry.
Schema importers allow you to import schemas from one Schema Registry to another, enabling cross-cluster schema replication.

## Usage

This role can be used to create and manage multiple schema importers. Each importer can be configured with different contexts, subjects, and authentication methods.

## Sample Configuration

Below is an example of how to configure schema importers in your inventory file:

```yaml
schema_importers:
  - name: "staging-to-prod-importer"
    context: "staging-context"
    subjects: ["orders.*", "customers.*"]
    config:
      schema_registry_endpoint: "http://staging-schema-registry:8081"
      authentication_type: "basic"
      basic_username: "staging-user"
      basic_password: "staging-password"

  - name: "dev-sync-importer"
    subjects: ["*"]  # Import all subjects
    config:
      schema_registry_endpoint: "https://dev-schema-registry:8081"
      authentication_type: "basic"
      basic_username: "dev-client-id"
      basic_password: "dev-client-secret"

  - name: "backup-restore-importer"
    context: "backup-context"
    subjects: ["payment.*", "user.*"]
    config:
      schema_registry_endpoint: "http://backup-schema-registry:8081"
      authentication_type: "basic"
      basic_username: "backup-user"
      basic_password: "backup-password"

password_encoder_secret: "mysecret"
```

This example shows:
- Different contexts for schema organization
- Subject filtering patterns (specific patterns or wildcard)
- Basic authentication configuration
- Custom configuration overrides for fine-tuning
- Required password encoder secret for Schema Registry

## Documentation

You can find the documentation for running CP-Ansible at https://docs.confluent.io/current/installation/cp-ansible/index.html.
You can find supported configuration variables in [VARIABLES.md](docs/VARIABLES.md)

## Contributing

If you would like to contribute to the CP-Ansible project, please refer to the [CONTRIBUTE.md](docs/CONTRIBUTING.md)

## License

[Apache 2.0](docs/LICENSE.md)
