.. _cp-ansible:

Ansible Playbooks for Confluent Platform
========================================

========
Overview
========

Confluent provides `Ansible playbooks <https://github.com/confluentinc/cp-ansible>`__ for installing the `Confluent Platform <http://www.confluent.io>`__.

.. note:: As of the Confluent Platform 5.3.0 release, these playbooks are fully supported for those with a Confluent Support Contract. Any issues encountered can be reported via Confluent Support at https://support.confluent.io.  For those without a Confluent Support contract, issues can be reported via the `cp-ansible GitHub repo <https://github.com/confluentinc/cp-ansible/issues>`__ and will be addressed on a best effort basis.


============
Requirements
============

General Requirements:

* Confluent Platform 5.3.0 or higher - are we sure? 
* Ansible 2.5.x or higher (on control node)
* `Confluent Platform Ansible playbooks <https://github.com/confluentinc/cp-ansible>`__
* passwordless ssh between all hosts
* sudo access for ssh user for all hosts

Operating System Support:

* RHEL 7.x or later
* Ubuntu 16.04 or later

Minimum Hardware Recommendations:

* 4 hosts 
* 8 CPU Cores per host
* 32GB of RAM per host  

============
Introduction
============

Ansible provides a simple way to deploy, manage, and configure the Confluent Platform services. The `cp-ansible  <https://github.com/confluentinc/cp-ansible>`__ repository provides playbooks and templates to easily spin up a Confluent Platform installation. Specifically this repository:

* Installs Confluent Platform packages
* Starts services using systemd scripts
* Provides configuration options for plaintext, SSL, SASL_SSL, SASL_Kerberos, SSL_Kerberos, Kerberos, Kerberos_ssl_customcerts  communication amongst the services

The services that can be installed from this repository are:

* ZooKeeper
* Kafka
* Schema Registry
* REST Proxy
* Confluent Control Center
* Kafka Connect (distributed mode)


Scope
-----

In Scope
~~~~~~~~

These Ansible playbooks are intended as a general template for setting up a production-ready proof of concept environment. There are four available templates.

* PLAINTEXT -- use these templates if you have no requirements for a secured environment
* SSL -- use these templates if you require only SSL encryption and would like the playbook to create the certificates for you
* SASL_SSL -- use these templates if you require plaintext SASL authentication and SSL encryption and would like the playbook to create the certificates for you 
* SSL_customcerts -- use these templates if you require only SSL encryption, but using your own self signed or CA certificates
* Kerberos_SSL -- use these templates if you require SSL encryption and would like the playbook to create the certificates for you and you would like Kerberos authentication, providing your own KDC and keytabs
* Kerberos -- use these templates if you require Kerberos authentication and are providing your own KDC and keytabs 
* Kerberos_ssl_customcerts -- use these templates if you require SSL encryption and will be providing your own certificates and also require kerberos authentication and are providing your own KDC and keytabs

Out of Scope
~~~~~~~~~~~~

The following are not in scope:

* Provisioning of machines
* Setting up a Kerberos KDC or an Active Directory KDC 

Future work and additional features
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For those with a Conluent Support contract, future work and additional features should be filed by opening a case with Confluent Support at https://support.confluent.io.

For those without a Confluent Support Contract, please review the Contributing document [here]().


==========================
How to use this repository
==========================

Each playbook has it's own directory within the repository containing a unique `all.yml` file at the root and where required a vars subdirectory containing a `security_vars.yml` 

The default playbook in the root of the repo is PLAINTEXT.

------------------------

This repository has a demo `hosts.yml` file in the root directory. This file is where you specify which roles will be run on each host. For more information on
the host file in general please see the `Ansible documentation <http://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html#hosts-and-groups>`_. For this
particular setup, you will want to ensure each host in your cluster is a member of the `preflight` role. Other than that, you can specify as many or as few of each service
as makes sense for your use case.

Template properties files 
-------------------------

Each service has 8 template properties files. Which properties file template will be used depends on the value of `security_mode` set. Valid options are `plaintext`, `ssl`, `sasl_ssl`, `SSL_customcerts`, `Kerberos_SSL`,`Kerberos`, `Kerberos_ssl_customcerts`.
The `SSL`, `SASL_SSL`, `Kerberos_SSL` hardcode some security parameters for ease of setup in a proof of concept environment. 

For a production environment we would recommend using the `Kerberos_ssl_customcerts` playbook and providing your own SSL Certificates and Kerberos KDC with Keytabs to secure your environment.

Using your own SSL certificates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can provide your own SSL certificates with the following playbooks:

SSL_customcerts

This playbook is specifically designed to be run with your own certificates.  You will need to update the `security_vars.yml` file with the names and paths to your ca cert, host certificate, and private key in pkcs12 format.  This playbook assumes that your certificate is a wildcard certificate and will setup client and Broker keystores and truststores.  It does not differenciate between services, for simplicity. 

Kerberos_ssl_customcerts

This playbook is specifically designed to be run with your own certificates as well as your own KDC and keytabs.  You will need to update the `security_vars.yml` file with the names and paths to your ca cert, host certificate, and private key in pkcs12 format.  This playbook assumes that your certificate is a wildcard certificate and will setup client and Broker keystores and truststores.  It does not differenciate between services, for simplicity. 


Using Kerberos keytabs for SASL authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can setup your own KDC, independently of these playbooks and provide your own keytabs:

kerberos

This playbook is specifically designed to be run with your own keytabs, against a KDC which you will have already setup.  You will need to 

Kerberos_SSL

Kerberos_ssl_customcerts


Running
-------

Run the whole setup
~~~~~~~~~~~~~~~~~~~

.. sourcecode:: bash

   ansible-playbook -i hosts.yml all.yml

Check for Changes
~~~~~~~~~~~~~~~~~

.. sourcecode:: bash

   ansible-playbook --check -i hosts.yml all.yml

Apply Changes
~~~~~~~~~~~~~

.. sourcecode:: bash

   ansible-playbook -i hosts.yml all.yml


======================
Additional information
======================

This repository makes use of the `systemd scripts provided in Confluent Platform <https://docs.confluent.io/current/installation/scripted-install.html>`_. As such, there is an expected default user/service mapping that follows the convention of using the prefix `cp-` followed by the service name. For example `cp-kafka` or `cp-schema-registry`. The one exception is that ZooKeeper is run as the `cp-kafka` user. This matches the systemd scripts as well.

======================
Troubleshooting 
======================

Ansible has general troubleshooting 
