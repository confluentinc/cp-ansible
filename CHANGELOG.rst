================================
Ansible Playbooks for Confluent Platform - Release Notes
================================

.. contents:: Topics

v7.3.5
======

Notable enhancements
-------------

- Parametrize the number of retries for MDS API requests
- Removed timeout configs from client properties of Kafka Broker, allowing customers to use custom timeout values
- Archived installation of Confluent Platform on Debian 9 since the OS version reached end-of-life


v7.3.4
======

Notable fixes
-------------

- Introduced timeout while deploying connector
- Added optional vars to configure kerberos.kdc_port (default: 88), kerberos.admin_port (default: 749)
- Minor fixes to support confluent CLI v3
- Fixed minor bugs in SSL principal mapping rule logic
- Fixed some non-root CP deployment issues
- Fixed mTLS healthchecks

v7.3.3
======

Notable enhancements
-------------

- Move out host validations as an on-demand playbook
- Improve error handling deploying kafka connectors
- Add confluent.ssl.* properties
- Fix export certificates logic from Keystore and Truststore
- Fix JMX Exporter Rules
- Support custom kerberos client config file and custom path
- Add retries to register cluster task


v7.3.2
======

Notable enhancements
-------------

- Added provision to configure Kafka Connect Replicator custom rest extension classes
- For archive installations, fixed logic to use `config_prefix` variable for zookeeper, kafka broker, schema registry, kafka connect
- Skip "Install pip" and "Upgrade pip" tasks using `package` tag
- Introduced new tag `cp_package` for installing/ upgrading confluent packages


v7.3.1
======

Notable enhancements
-------------

- Bug fixes to enable running playbook in ansible check mode.
- Validation about python version - 3.6+
- Bug fixes for rhel7 related to epel-release package


v7.3.0
======

New features
-------------

- CP-Ansible playbooks are Red Hat certified now and are available on Automation Hub starting 7.0.X
- Confluent Platform and CP-Ansible now supports JDK 17, in addition to JDK 8 and JDK 11. CP-Ansible support is now available for custom Java installations too.
- Day 2 Operations - upgrade from non-RBAC to RBAC using CP-Ansible is guarded with zero downtime and officially supported.
- Ansible Playbooks for Confluent Platform is now officially supported for Ansible 2.12 and 2.13 in addition to 2.11.

Notable enhancements
-------------

- Default confluent cli version has been updated to 2.28.1 from 2.19
- New var ansible_become_localhost introduced to specify the become value for localhost - used when dealing with any file present on localhost/controller
- Dedicated playbook to restart services manually
- rbac_component_additional_system_admins now supports assignment of principals and not just users
- Pip and python modules can/will now be installed on managed nodes via CP-Ansible

Upgrade considerations
-------------

- Upgrades to CP 7.3 can be taken up with CP-Ansible using Ansible 2.12 and 2.13 too.
- Variable rbac_component_additional_system_admins now can be updated in inventory file for assignment of principals. Backward compatible.


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