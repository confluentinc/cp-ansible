
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

You can find supported configuration variables in [VARIABLES.md](VARIABLES.md)


## Development

* Create a directory with the following structure:<br>
```mkdir -p <path_to_cp-ansible>/ansible_collections/confluent/```

  You can put <path_to_cp-ansible> anywhere in your directory structure, but the directory structure under <path_to_cp-ansible> should be set up exactly as specified above.

* Clone the Ansible Playbooks for Confluent Platform repo into the platform directory inside the directory you created in the previous step:<br>
```git clone https://github.com/confluentinc/cp-ansible <path_to_cp-ansible>/ansible_collections/confluent/platform```


## Contributing

If you would like to contribute to the CP-Ansible project, please refer to the [CONTRIBUTE.md](CONTRIBUTING.md)


## License

[Apache 2.0](LICENSE.md)
