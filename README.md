Please note that these playbooks are provided without support and are intended to be a guideline. Any issues encountered can be reported via the GitHub issues and will be addressed on a best effort basis. Pull requests are also encouraged.

# Introduction

Ansible provides a simple way to deploy, manage, and configure the Confluent Platform services. This repository provides playbooks and templates to easily spin up a Confluent Platform installation. Specifically this repository:

* Installs Confluent Platform packages
* Starts services using systemd scripts
* Provides configuration options for plaintext, SSL, SASL_SSL, and user supplied self signed ssl communication amongst the services

The services that can be installed from this repository are:

* ZooKeeper
* Kafka
* Schema Registry
* REST Proxy
* Confluent Control Center
* Kafka Connect (distributed mode)

# Documentation

You can find the documentation for running this playbook at https://docs.confluent.io/current/tutorials/cp-ansible/docs/index.html.

Steps to run Kerberos and ssl playbooks.

Below are the Kerberos Directories,
1. kerberos
2. kerberos_ssl
3. kerberos_ssl_customcerts

Prerequisites:
1. Generate Keytabs and place the keytabs under /root/keytabs folder in jump host, path to keytabs file is located in kerberos/hosts.yml, kerberos_ss/hosts.yml and kerberos_ssl_customcerts/hosts.yml
2. Set the ansible roles path
ex: export ANSIBLE_ROLES_PATH=/root/cp-ansible-internal/roles

Under each of the directories has host.yml file, update host.yml file with hosts IPs or FQDN names

If you want setup Kafka cluster with Kerberos, run below command
ansible-playbook kerberos/all.yml -i kerberos/hosts.yml --key-file=/root/kerberos.pem -s --ssh-common-args='-o StrictHostKeyChecking=no'

If you want setup Kafka cluster with Kerberos with ssl self-signed certs, run below command
ansible-playbook kerberos_ssl/all.yml -i kerberos_ssl/hosts.yml --key-file=/root/kerberos.pem -s --ssh-common-args='-o StrictHostKeyChecking=no'

If you want setup Kafka cluster with Kerberos with ssl custom certs, run below command
ansible-playbook kerberos_ssl_customcerts/all.yml -i kerberos_ssl_customcerts/hosts.yml --key-file=/root/kerberos.pem -s --ssh-common-args='-o StrictHostKeyChecking=no' 
