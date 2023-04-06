================================
Ansible Playbooks for Confluent Platform - Release Notes
================================

.. contents:: Topics

v7.0.9
======

Notable fixes
-------------

- Introduce timeout while deploying connector

v7.0.8
======

Notable enhancements
-------------

- Improve error handling deploying kafka connectors
- Add confluent.ssl.* properties
- Fix export certificates from Keystore and Truststore
- Fix JMX Exporter Rules
- Support custom kerberos client config file and custom path


v7.0.7
======

Notable enhancements
-------------

- Add retries to installation tasks to resolve connectivity issues
- Dedicated playbook to restart services manually
- New var ansible_become_localhost introduced to specify the become value for localhost - used when dealing with any file present on localhost/controller
- Add ssl.* properties for kafka broker
- Enable running playbook in ansible check mode
- Bug Fixes
   * `#633 <https://github.com/confluentinc/cp-ansible/issues/633>`_ Removed unnecessary C3 log dir permissions

v7.0.6
======

Notable enhancements
-------------

 - Optimise the process of copying mds pem file to host nodes.
 - Making Java SID Repo as optional.
 - Cleanup Kafka Broker Custom properties
 - Introduced login shell for Linux users which are running the Component service.
 - Enhanced RBAC support with FIPS
 - Isolate truststore, keystore ceration when multiple kafka connect services run on same host.
 - Allow creation of keystore and truststore with custom password when using custom or self-signed certs
 - Minor code cleanup and refactoring.


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
