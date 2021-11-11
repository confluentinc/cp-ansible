
# CP-Ansible

## Introduction

Ansible provides a simple way to deploy, manage, and configure the Confluent Platform services. This repository provides playbooks and templates to easily spin up a Confluent Platform installation. Specifically this repository:

* Installs Confluent Platform packages or archive.
* Starts services using systemd scripts.
* Provides configuration options for many security options including encryption, authentication, and authorization.

The services that can be installed from this repository are:

* ZooKeeper
* Kafka
* Schema Registry
* REST Proxy
* Confluent Control Center
* Kafka Connect (distributed mode)
* KSQL Server
* Replicator

## Documentation

You can find the documentation for running CP-Ansible at https://docs.confluent.io/current/installation/cp-ansible/index.html.

You can find supported configuration variables in [VARIABLES.md](https://github.com/confluentinc/cp-ansible/blob/6.2.1-post/VARIABLES.md)

## Contributing


If you would like to contribute to the CP-Ansible project, please refer to the [CONTRIBUTE.md](https://github.com/confluentinc/cp-ansible/blob/6.2.1-post/CONTRIBUTING.md)


## License

[Apache 2.0](https://github.com/confluentinc/cp-ansible/blob/6.2.1-post/LICENSE.md)
