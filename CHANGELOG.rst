================================
Ansible Playbooks for Confluent Platform - Release Notes
================================

.. contents:: Topics

v7.2.3
======

New features
-------------

- Ansible Playbooks for Confluent Platform is now officially supported for Ansible 2.12 and 2.13 in addition to 2.11

Notable enhancements
-------------

- Add retries to installation tasks to resolve connectivity issues
- Introduced fetch_logs_path - Path on component to store logs
- Dedicated playbook to restart services manually
- New var ansible_become_localhost introduced to specify the become value for localhost - used when dealing with any file present on localhost/controller
- Add ssl.* properties for kafka broker
- Improved internal handling of SSL certificates using crypto module
- Fixed proxy settings for yum repo, It now supports both https_proxy and http_proxy
- Pip and python modules can/will now be installed on managed nodes via CP-Ansible
- Added provision to configure Kafka Connect Replicator custom rest extension classes
- Validation about python version - 3.6+
- Skip host validation for rolling deployment/upgrades
- Bug Fixes
   * `ANSIENG-1764 <https://confluentinc.atlassian.net/browse/ANSIENG-1764>`_ C3 fails with NPE when SR url is not structured
   * Enable running playbook in ansible check mode
   * `#633 <https://github.com/confluentinc/cp-ansible/issues/633>`_ Removed unnecessary C3 log dir permissions
   * `ANSIENG-1864 <https://confluentinc.atlassian.net/browse/ANSIENG-1864>`_ For archive installations, fixed logic to use `config_prefix` variable for zookeeper, kafka broker, schema registry, kafka connect
   * `ANSIENG-1953 <https://confluentinc.atlassian.net/browse/ANSIENG-1953>`_ Make Pip install and Upgrade pip tasks skippable using `tags: package`


v7.2.2
======

Notable enhancements
-------------

 - Improved validation of certificates, accepts ssl key file in ansible-vault format
 - Optimise the process of copying mds pem file to host nodes, and other security improvements.
 - Minor code cleanup and refactoring.
 - Making Java SID Repo as optional.
 - Isolate truststore, keystore ceration when multiple kafka connect services run on same host.
 - Allow creation of keystore and truststore with custom password when using custom or self-signed certs
 - Improved Validations, Internet access check now considers whether proxy is set or not.
 - Fix typo kakfa to kafka
 - New Sample inventory with single node.
 - Cleanup Kafka Broker Custom properties
 - Enhanced RBAC support with FIPS


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
