Ansible playbooks for installing the [Confluent Platform](http://www.confluent.io).

# Requirements

* Confluent Platform 4.1 or higher
* Ansible (on control node)
* passwordless ssh between all hosts
* sudo access for ssh user for all hosts

# Introduction

Ansible provides a simple way to deploy, manage, and configure the Confluent Platform services. This repository provides playbooks and templates to easily 
spin up a Confluent Platform installation. Specifically this repository:

* Installs Confluent Platform packages
* Starts services using systemd scripts
* Provides configuration options for plaintext, SSL, and SASL_SSL communication amongst the services

The services that can be installed from this repository are:

* ZooKeeper
* Kafka
* Schema Registry
* REST Proxy
* Confluent Control Center
* Kafka Connect (distributed mode)

## Scope

These Ansible playbooks are intended as a general template for setting up a production-ready proof of concept environment. There are three available templates.

* PLAINTEXT -- use these templates if you have no requirements for a secured environment
* SSL -- use these templates if you require only SSL encryption
* SASL_SSL -- use these templates if you require plaintext SASL authentication and SSL encryption

### Out of scope

The playbooks and templates generate self-signed certificates and use SASL plaintext authentication for a simple proof of concept that demonstrates the use of security features. The following are not in scope:

* Generating production-ready SSL certificates
* Setting up a Kerberos KDC or integration with Active Directory
* Guidance on business usage of authentication and authorization
* Provisioning of machines

### Future work and additional features

Future work and additional features should be tracked in the GitHub issues for the repository.

# How to use this repository

PLAINTEXT, SSL, SASL_SSL each have example playbooks and hosts files in their respective `plaintext`, `ssl`, `sasl_ssl` directories.
The `hosts.yml` and `all.yml` files at the repository root match the `sasl_ssl` and this can be considered the default path.

## Template properties files

Each service has three template properties files. Which properties file template will be used depends on the value of `security_mode` set. Valid options are `plaintext`, `ssl`, `sasl_ssl`.
These templates hardcode some security parameters for ease of setup in a proof of concept environment. If you want to use this setup in a production environment, you will likely want to use
SSL certificates provided by your own Certificate Authority and use Kerberos keytabs for SASL authentication.

### Using your own SSL certificates

The service properties file templates in this repository expect certificates to be stored under `/var/ssl/private`. In this directory, each host stores a keystore and trustore for clients 
and a keystore and truststore for Brokers. No differentiation between services is made for simplicity. You can update the exact path to the certificate stores by updating 
`roles/<service>/templates/<service>_ssl.properties.j2` or `roles/<service>/templates/<service>_sasl_ssl.properties.j2` depending on the security mode you have chosen.

### Using Kerberos keytabs for SASL authentication

The service properties file templates in this repository use the plaintext SASL mechanism that is shipped with Kafka. The JAAS configurations are specified in the properties files directly, so
if you choose to use Kerberos keytabs for authentication, you can modify `roles/<service>/templates/<service>_sasl_ssl.properties.j2` to use the SASL mechanism GSSAPI and update the JAAS
configuration. Please consult [the security documentation](https://docs.confluent.io/current/kafka/authentication_sasl_gssapi.html) for specific examples on updating the configuration.

## Running

### Run the whole setup

```bash
ansible-playbook -i hosts.yml all.yml
```

### Check for Changes

```bash
ansible-playbook --check -i hosts.yml all.yml
```

### Apply Changes

```bash
ansible-playbook -i hosts.yml all.yml
```

# Additional information

This repository makes use of the [systemd scripts provided in Confluent Platform](https://docs.confluent.io/current/installation/scripted-install.html). As such, there is an expected default user/service mapping that follows the convention of using the prefix
`cp-` followed by the service name. For example `cp-kafka` or `cp-schema-registry`. The one exception is that ZooKeeper is run as the `cp-kafka` user. This matches the systemd scripts as well.
