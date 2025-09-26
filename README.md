
[![Try Confluent Cloud - The Data Streaming Platform](https://images.ctfassets.net/8vofjvai1hpv/10bgcSfn5MzmvS4nNqr94J/af43dd2336e3f9e0c0ca4feef4398f6f/confluent-banner-v2.svg)](https://confluent.cloud/signup?utm_source=github&utm_medium=banner&utm_campaign=oss-repos&utm_term=cp-ansible)

# CP-Ansible

## Description

Ansible provides a simple way to deploy, manage, and configure the Confluent Platform services. This repository provides playbooks and templates to easily spin up a Confluent Platform installation. Specifically this repository:

* Installs Confluent Platform packages or archive.
* Starts services using systemd scripts.
* Provides configuration options for many security options including encryption, authentication, and authorization.

The services that can be installed from this repository are:

* Kraft Controller (or Kafka Controller)
* Kafka
* Schema Registry
* REST Proxy
* Confluent Control Center
* Kafka Connect (distributed mode)
* KSQL Server
* Replicator

## Requirements

Prerequisites for installing CP can be found at [General Requirements](https://docs.confluent.io/ansible/current/ansible-requirements.html#general-requirements).


## Installation

You can install this collection from Ansible Automation Hub and Ansible Galaxy by following [Download Ansible Playbooks for Confluent Platform](https://docs.confluent.io/ansible/current/ansible-download.html).

As an alternative to the recommended methods above, you can install the package directly from the source repository.

* Create a directory with the following structure:<br>
```mkdir -p <path_to_cp-ansible>/ansible_collections/confluent/```

  You can put <path_to_cp-ansible> anywhere in your directory structure, but the directory structure under <path_to_cp-ansible> should be set up exactly as specified above.

* Clone the Ansible Playbooks for Confluent Platform repo into the platform directory inside the directory you created in the previous step:<br>
```git clone https://github.com/confluentinc/cp-ansible <path_to_cp-ansible>/ansible_collections/confluent/platform```


## Use Cases

Ansible Playbooks for Confluent Platform (Confluent Ansible) offers a simplified way to configure and deploy Confluent Platform.


## Testing

CP-Ansible's tests use the [Molecule](https://ansible.readthedocs.io/projects/molecule/) framework, and it is strongly advised to test this way before submitting a Pull Request. Please refer to the [HOW_TO_TEST.md](docs/HOW_TO_TEST.md)


## Contributing

If you would like to contribute to the CP-Ansible project, please refer to the [CONTRIBUTE.md](docs/CONTRIBUTING.md)

## Support

For any support request, please reach out to [Confluent Support Portal](https://support.confluent.io/).
> **Disclaimer:** This collection contains a dependency on `community.crypto` that is currently not certified. If an issue is encountered that is determined to be caused by this unsupported module, the collection will not be supported under the Redhat support program. A certified and fully supported alternative will be introduced in a future release.

## Release Notes

This [page](https://docs.confluent.io/ansible/current/ansible-release-notes.html) summarizes the technical details of the Confluent releases.

## License

[Apache 2.0](LICENSE.md)
