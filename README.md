
# CP-Ansible

## Introduction

Ansible provides a simple way to deploy, manage, and configure the Confluent Platform services. This repository provides playbooks and templates to easily spin up a Confluent Platform installation. Specifically this repository:

* Installs Confluent Platform packages.
* Starts services using systemd scripts.
* Provides configuration options for plaintext, SSL, SASL_SSL, and Kerberos.

The services that can be installed from this repository are:

* ZooKeeper
* Kafka
* Schema Registry
* REST Proxy
* Confluent Control Center
* Kafka Connect (distributed mode)
* KSQL Server

## Documentation

You can find the documentation for running CP-Ansible at https://docs.confluent.io/current/tutorials/cp-ansible/docs/index.html.

## Contributing


If you would like to contribute to the CP-Ansible project, please refer to the [CONTRIBUTE.md](https://github.com/confluentinc/cp-ansible/blob/5.4.x/CONTRIBUTING.md)


## License

[Apache 2.0](https://github.com/confluentinc/cp-ansible/blob/5.4.x/LICENSE.md)
