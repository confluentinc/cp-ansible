================================
Ansible Playbooks for Confluent Platform - Release Notes
================================

.. contents:: Topics

v7.2.2
======
* e95187504 Rename group index
* 77606eacf Resolve index in Assert SSL key hash matches SSL cert hash
* 0931bab28 Resolve zookeeper_ssl failure
* 5186ccfe2 Resolve SSL Key test failure
* 44757230f Fix Zookeeper ssl Test failure on 7.2.x
* e97adaa77 fix ansible version compare
* 7b2574205 Fix pint merge issue of double when
* ed7723ed9 Remove all occurence of create_certs
* fbe0c84d0 Make ansi-takeover work for 6x
* fb3610297 Prevent pem file copy when not req
* 766e79ffc Remove all occurence of copy_certs
* 4290d68ab Remove all occurence of create_certs
* b9bb78f0f Make ansi-takeover work for 6x
* 6b7b482c3 support replicator for takeover
* 21c2ae013 Update ansible version check
* 08678ce52 Skip restart message based on restart var
* e670dc111 Fix release version for archive-scram-rhel
* c770f8dc6 Add Sid Repo variable for Debain 1
* 1fec0f5d3 remove trailing space
* d291750d0 Allow creation of keystore and truststore with custom password when using custom or self-signed certs
* 02460ef9d Separate trustore/keystore creation with custom certificates by service when running multiple services in the same host, in particular for multiple connect workers in the same host
* d60859d0d Fixed Kafka Connect children registration with MDS
* d9cc8dfd6 Remove all instances of community.general
* 42731bf5a fix test when entry undefined
* 5dbd3b94a Check Internet Access thru proxy if any
* ce8d47286 accept ssl key file in ansible-vault format
* 4b4056471 Fix typo kakfa to kafka
* add023f14 Resolve rbac-mtls-rhel Test Failure
* c51705d5c zookeeper_skip_restart prints message -> restarting zokeeper<-
* 905564842 Single Dev Node with Notes
* 71fc26ee4 Resolve mtls-java11-rhel Test Failure
* 8f9881796 Resolve mtls-java11-ubuntu Test Failure
* 58f201950 Remove Deprecated Properties from Kafka Broker
* 5cfb910bb mention docker version requirement
* 4a5699f04 Extract DNAME from BCFKS keystore
* ffaf38bce Remove duplicate var definition
* e229ea7d2 Document user_login_shell
* 5203d5b98 Define user login shell for all components user
* 4d7344880 Improve decryption logic


v7.2.1
======

New features
-------------

You can obfuscate sensitive information in Confluent Platform component logs and then create a single bundle of those logs to share with Confluent Support.

Notable enhancements
-------------

You can configure CP-Ansible to use the JKS files existing on each worker node for TLS encryption. You dont need to provide the JKS files on the Ansible control node. For more information, see Configure Encryption for Confluent Platform with Ansible Playbooks.

Upgrade considerations
-------------

CP-Ansible 7.2 does not support Ansible 2.9 or Python 2.x because those runtimes are end-of-life. Upgrade to Ansible 2.11+ or Python 3.6+ to use CP-Ansible 7.2 (https://docs.confluent.io/ansible/7.2.0/ansible-encrypt.html).


v7.1.3
======

New features
-------------

- Ansible Playbooks for Confluent Platform now have tag-based separation of tasks that require root permission from tasks that do not require root permission. You can take advantage of these tags to run tasks that do not require root permission. This enables users who have their own method to manage the prerequisites of Confluent Platform to use the Ansible Playbooks for Confluent Platform without root privileges.
- You can customize the SSL principal name by extracting one of the fields from the long distinguished name.

Notable enhancements
-------------

- Extended the support of the Ansible Playbooks for Confluent Platform to include Ansible 2.9 and Python 2.7.
- Extended host validation for memory and storage validation during installation.

Upgrade considerations
-------------

The Confluent CLI v2 has a breaking change that impacts Confluent Platform upgrades performed using Ansible Playbooks for Confluent Platform. Specifically, if you are using secret protection without RBAC, you cannot upgrade to Confluent Platform 7.1 as RBAC is mandatory with secret protection. For additional details, see here (https://docs.confluent.io/confluent-cli/current/migrate.html#breaking-changes-for-confluent-cli).


v7.0.5
======

Refer https://docs.confluent.io/platform/7.0.5/release-notes/index.html#ansible for more details.

New features
-------------

The Ansible Playbooks for Confluent Platform are now structured as Ansible Collections (https://docs.ansible.com/collections.html). This modernizes the structure of the Ansible Playbooks for Confluent Platform to conform with industry-standard best practices for Ansible. This will make it easier to compose using the Ansible Playbooks for Confluent Platform and other Ansible content, and improve the ability for your organization to provision and configure software holistically and consistently with Ansible. To understand how to work with the new structure, see the documentation on downloading Ansible Playbooks for Confluent Platform and using the Playbooks to install or upgrade Confluent Platform.

Notable enhancements
-------------

- Installs Java version 11 by default; the previous default was Java version 8. If you want to use Java 8, you can use the inventory variable appropriate for your platform: ubuntu_java_package_name, debian_java_package_name, or redhat_java_package_name.
- Adds support for Ubuntu 20.
- Adds support for Debian 10.

Notable fixes
-------------

When debug is enabled with the -vvv Ansible option, sensitive information, such as passwords, certificates, and keys, are printed in the output. Ansible does not provide a way to suppress sensitive information with the -vvv. Therefore, it is not recommended to use the debug mode in production environments.
As an alternative, use the playbook with the --diff option when troubleshooting issues. With this release, Ansible Playbooks for Confluent Platform no longer prints sensitive information, such as passwords, certificates, and keys, in the output of the --diff option.
For details, see Troubleshoot (https://docs.confluent.io/ansible/current/ansible-troubleshooting.html).

Known issues
-------------

If you have deployed Confluent Platform with the Ansible Playbooks where Java 8 was installed, you cannot use Ansible Playbooks to update the Confluent Platform deployment to use Java 11. Even if your inventory file is configured to install Java 11, running the Ansible Playbooks will only install Java 11 but the Confluent Platform components will continue to use Java 8.

Upgrade considerations
-------------

- If you are deploying Confluent Platform with the Ansible Playbooks configured for FIPS operational readiness, you must use Java 8. Confluent Platform FIPS operational readiness is not compatible with Java 11. For new installations or upgrades where FIPS operational readiness is desired, it is recommended that you explicitly configure your inventory file to use Java 8 by using the inventory variable appropriate for your platform: ubuntu_java_package_name, debian_java_package_name, or redhat_java_package_name.
- The Ansible Playbooks are now structured as Ansible Collections. To understand how to work with the new structure, see the documentation on using the Playbooks to upgrade Confluent Platform (https://docs.confluent.io/ansible/current/ansible-upgrade.html).
