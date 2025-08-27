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
    context: "dev-context"
    subjects: ["orders.*", "customers.*"]
    subject_rename_format: "dc_${subject}"
    kek_rename_format: "dc_${kek}"
    config:
      schema_registry_endpoint: "http://dev-schema-registry:8081"
      authentication_type: "basic"
      basic_username: "dev-user"
      basic_password: "dev-password"
        # Override to use mTLS instead of basic auth
    config_overrides:
      security.protocol: "SSL"
      ssl.keystore.location: "/var/ssl/private/client.keystore.jks"
      ssl.keystore.password: "keystorepass"
      ssl.key.password: "keypass"
      ssl.truststore.location: "/var/ssl/private/client.truststore.jks"
      ssl.truststore.password: "truststorepass"

  - name: "prod-backup-exporter"
    context_type: "AUTO"
    subjects: [*]  # Export all subjects
    config:
      schema_registry_endpoint: "https://prod-schema-registry:8081"
      authentication_type: "basic"
      basic_username: "prod-client-id"
      basic_password: "prod-client-secret"
     # Method 1: Override config section only
    config_overrides:
      basic_username: "dev-user"
      basic_password: "dev-password"

    # Method 2: Override entire request body (if needed)
    body_overrides:
      contextType: "CUSTOM"
      context: "prod-context"
      config:
        basic.auth.credentials.source: "USER_INFO"


  - name: "simple-exporter"
    context_type: "NONE"
    subjects: ["payment.*"]
    config:
      schema_registry_endpoint: "http://remote-schema-registry:8081"
      authentication_type: "basic"
      basic_username: "client-id"
      basic_password: "client-secret"

password_encoder_secret: "secret"

Complete Request Body Override**

```yaml
schema_exporters:
  - name: "custom-exporter"
    subjects: ["default.*"]  # This will be overridden
    config:
      schema_registry_endpoint: "http://localhost:8081"
      authentication_type: "basic"
      basic_username: "user"
      basic_password: "pass"

    # Override entire request body structure
    body_overrides:
      name: "production-exporter"  # Override name
      contextType: "CUSTOM"
      context: "prod-dc1"
      subjects: ["orders.*", "payments.*", "users.*"]  # Override subjects
      subjectRenameFormat: "prod_${subject}"
      kekRenameFormat: "prod_${kek}"
      config:
        schema.registry.url: "https://prod-sr.company.com:8081"
        basic.auth.credentials.source: "USER_INFO"
        basic.auth.user.info: "{{ prod_sr_user }}:{{ prod_sr_password }}"
        schema.registry.ssl.truststore.location: "/etc/ssl/certs/java/cacerts"
        schema.registry.ssl.truststore.password: "changeit"
        schema.registry.ssl.endpoint.identification.algorithm: "https"
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
