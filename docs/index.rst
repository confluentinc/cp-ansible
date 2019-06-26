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

* Confluent Platform 5.3.x, 5.2.x, 5.1.x 
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

Future Recommendations 
~~~~~~~~~~~~~~~~~~~~~~

For those with a Confluent Support contract, future work and additional features should be filed by opening a case with Confluent Support at https://support.confluent.io.

Note: A Kerberos Key Distribution Center (KDC) and Active Directory KDC configurations are not currently configured by these playbooks.

For those without a Confluent Support Contract, please review the Contributing document [here]().

==========================
How to use this repository
==========================

Each playbook has its own directory within the repository containing a unique `all.yml` file at the root and where required a vars subdirectory containing a `security_vars.yml`, which is required to be filled in for SSL configuration. 

The default playbook in the root of the repo is PLAINTEXT.

------------------------

This repository has a demo `hosts.yml` file in the root directory. This file is where you specify which roles will be run on each host. For more information on
the host file in general please see the `Ansible documentation <http://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html#hosts-and-groups>`_. For this
particular setup, you will want to ensure each host in your cluster is a member of the `preflight` role. Other than that, you can specify as many or as few of each service
as makes sense for your use case.

Template properties files 
-------------------------

Each service has eight template properties files. The properties file template will be used based on the value of `security_mode` set. Valid options are `plaintext`, `ssl`, `sasl_ssl`, `SSL_customcerts`, `Kerberos_SSL`,`Kerberos`, `Kerberos_ssl_customcerts`.
Several security parameters for `SSL`, `SASL_SSL`, `Kerberos_SSL` hardcode some security parameters for ease of setup in a proof of concept environment. 

For a production environment, Confluent recommends using the `Kerberos_ssl_customcerts` playbook and providing your own SSL Certificates and Kerberos KDC with Keytabs to secure your environment.

Using your own SSL certificates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can provide your own SSL certificates with the following playbooks:

SSL_customcerts

This playbook is specifically designed to run with your own certificates.  You will need to update the `security_vars.yml` file with the names and paths to your ca cert, host certificate, and private key in pkcs12 format.  This playbook assumes that your certificate is a wildcard certificate and will setup client and Broker keystores and truststores.  It does not differenciate between services, for simplicity. 

Kerberos_ssl_customcerts

This playbook is specifically designed to be run with your own certificates as well as your own KDC and keytabs.  You will need to update the `security_vars.yml` file with the names and paths to your ca cert, host certificate, and private key in pkcs12 format.  This playbook assumes that your certificate is a wildcard certificate and will setup client and Broker keystores and truststores.  It does not differenciate between services, for simplicity. 


Using Kerberos keytabs for SASL authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Kerberos playbooks assume the hostname for the keytabs. If this is not the case in your environment, then you will need to manually copy the keytabs to each host.

Note: You need to setup your own KDC, independently of these playbooks and provide your own keytabs.

kerberos

This playbook is specifically designed to run with your own keytabs, against a KDC which you will have already setup.  You will need to update the following variables in the `hosts.yml` file:

`realm` - Your Kerberos Realm (for example, confluent.example.com). 

`kdc_hostname` - The hostname of the machine that your KDC is installed on.

`admin_hostname` - The hostname of the machine that your KDC is installed on.

`keytab_source_dir` - The path to the location of your keytabs to be copied to the hosts. 

Kerberos_SSL

This playbook is specifically designed to run with your own keytabs, against a KDC which you will have already setup.  It will also create selfsigned certificates to enable SSL and distribute them, and configure the components accordingly.  

You need to update the following variables in the `hosts.yml` file:

`realm` - Your Kerberos Realm (for example, confluent.example.com). 

`kdc_hostname` - The hostname of the machine that your KDC is installed on.

`admin_hostname` - The hostname of the machine that your KDC is installed on.

`keytab_source_dir` - The path to the location of your keytabs to be copied to the hosts, 

Kerberos_ssl_customcerts

This playbook is specifically designed to run with your own keytabs and your own SSL certificates, against a KDC which you will have already setup.  It will distribute the keytabs and SSL certificates and configure each component to work with both.  

You need to update the following variables in the `hosts.yml` file for kerberos:

`realm` - Your Kerberos Realm (for example, confluent.example.com). 

`kdc_hostname` - The hostname of the machine that your KDC is installed on.

`admin_hostname` - The hostname of the machine that your KDC is installed on.

`keytab_source_dir` - The path to the location of your keytabs to be copied to the hosts. 

You will also need to update the following variables in the `security_vars.yml` file in the playbook's `vars` directory:

`ssl_ca_certificate` - Enter the ca certificate name (for example, ca-cert).

`ssl_host_key` - Enter the host certificate name (for example, cert-signed).

`ssl_private_key` - Enter the private key file name. It must be pkcs format (for example, keystore.p12).

`ssl_ca_certificate_path` - Enter the full path to the ca certificate on the host you are running the playbook from.

`ssl_host_key_path` - Enter the full path to the ca certificate on the host you are running the playbook from.

`ssl_private_key_path` - Enter the full path to the ca certificate on the host you are running the playbook from.

`host_keystore_storepass` - Set the following to the desired password for each key-store.

`host_truststore_storepass` - Set the following to the desired password for each trust-store. 

`ca_cert_password` - Set the following to the password for the ca certificate.

`host_cert_password` - Set the following to the password for the host certificate.

`privatekey_keystore_password` - Set the following to the password for the private key key-store (pkcs12 file).

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

Example of Running Kerberos_ssl_customcerts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is a general example showing how to run the Kerberos_ssl_customcerts playbook, as it is currently the most complex playbook available in the repository.

We are assuming that you have already setup the following:

* your infrastructure
* KDC
* generated keytabs
* generated SSL certificates

Keytabs and SSL certificates should be located on the host where you are running Ansible from.  This allows the playbook to be pointed towards them so it can copy them to the appropriate locations on your behalf. 

1. Clone the CP-Ansible repostiory on your deployment host.

```git clone git@github.com:confluentinc/cp-ansible.git```

2. Change to the repository directory.

```cd cp-ansible```

3. Back up the existing `hosts.yml` and `all.yml`

```cp hosts.yml hosts.backup```
```cp all.yml all.backup```

4. Change to the `Kerberos_ssl_customcerts` playbook directory. 

```cd Kerberos_ssl_customcerts```

5. Copy the `hosts.yml` and `all.yml` to the repository root. 

```cp hosts.yml <pathToRepo>/cp-ansible```
```cp all.yml <pathToRepo>/cp-ansible```

6. Change to the vars subdirectory. 

```cd <pathToRepo>/cp-ansible/Kerberos_ssl_customcerts/vars```

7. Edit the `security_vars.yml` file. Complete the details based on the instructions provided in the file.

8. Change to the cp-ansible root directory.

```cd <pathToCP-Ansible>```

9. Edit `hosts.yml` to reflect the hostnames of the servers you want to install on, as well as the kerberos parameters mentioned in the playbook description above. 

10. Edit `all.yml` to reflect the roles which you want installed on each host.

11. Run the playbook.

```ansible-playbook -i hosts.yml all.yml```

======================
Additional information
======================

This repository makes use of the `systemd scripts provided in Confluent Platform <https://docs.confluent.io/current/installation/scripted-install.html>`_. As such, there is an expected default user/service mapping that follows the convention of using the prefix `cp-` followed by the service name. For example `cp-kafka` or `cp-schema-registry`. The one exception is that ZooKeeper is run as the `cp-kafka` user. This matches the systemd scripts as well.

======================
Troubleshooting 
======================

From time to time a playbook run could fail for a variety of reasons.  Complete the following steps if the playbook fails:

1. Append -vvv to the playbook run command and pipe it to a file.

```ansible-playbook -vvvv -i hosts.yml all.yml >failure.txt```

2. Open a support ticket with `Confluent Support https://support.confluent.io`__ and provide the following:

    a. Playbook name you are running.
    b. The step at which the playbook failed.
    c. All changes you have made to the playbook. 
    d. Attach the output from the failed test as a compressed text file.

