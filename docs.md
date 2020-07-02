***

### jolokia_enabled

Boolean to enable Jolokia Agent installation and configuration on all components

Default:  true

***

### jolokia_jar_path

Full path to download the Jolokia Agent Jar

Default:  /opt/jolokia/jolokia.jar

***

### jmxexporter_enabled

Boolean to enable Prometheus Exporter Agent installation and configuration on all components

Default:  false

***

### jmxexporter_jar_path

Full path to download the Prometheus Exporter Agent Jar

Default:  /opt/prometheus/jmx_prometheus_javaagent.jar

***

### fips_enabled

Boolean to have cp-ansible configure components with FIPS security settings

Default:  false

***

### custom_log4j

Boolean to enable cp-ansible's Custom Log4j Configuration across all components

Default:  true

***

### custom_yum_repofile

Boolean to configure custom repo file on RHEL/Centos hosts, must also set custom_yum_repofile_filepath variable

Default:  false

***

### custom_yum_repofile_filepath

Full path on control node to custom yum repo file, must also set custom_yum_repofile to true

Default:  ""

***

### custom_apt_repo

Boolean to configure custom apt repo file on Debian hosts, must also set custom_apt_repo_filepath variable

Default:  false

***

### custom_apt_repo_filepath

Full path on control node to custom apt repo file, must also set custom_apt_repo to true

Default:  ""

***

### confluent_server_enabled

Boolean to install commercially licensed confluent-server instead of community version: confluent-kafka

Default:  true

***

### health_checks_enabled

Boolean to enable health checks on all components

Default:  true

***

### sasl_protocol

SASL Mechanism to set on all Kafka Listeners. Configures all components to use that mechanism for authentication. Possible options none, kerberos, plain, scram

Default:  none

***

### ssl_enabled

Boolean to configure components with TLS Encryption. Also manages Java Keystore creation

Default:  false

***

### ssl_mutual_auth_enabled

Boolean to enable mTLS Authentication on all Kafka Listeners. Configures all components to use mTLS for authentication.

Default:  false

***

### confluent_common_repository_baseurl

Base URL for Confluent's RPM and Debian Package Repositories

Default:  "https://packages.confluent.io"

***

### install_java

Boolean to have cp-ansible install Java on hosts

Default:  true

***

### redhat_java_package_name

Java Package to install on RHEL/Centos hosts

Default:  java-1.8.0-openjdk

***

### debian_java_package_name

Java Package to install on Debian hosts

Default:  openjdk-8-jdk

***

### ubuntu_java_package_name

Java Package to install on Ubuntu hosts

Default:  openjdk-8-jdk

***

### ubuntu_java_repository

Deb Repository to use for Java Installation

Default:  ppa:openjdk-r/ppa

***

### jolokia_version

Version of Jolokia Agent Jar to Download

Default:  1.6.2

***

### jolokia_jar_url

Full URL used for Jolokia Agent Jar Download

Default:  "http://search.maven.org/remotecontent?filepath=org/jolokia/jolokia-jvm/{{jolokia_version}}/jolokia-jvm-{{jolokia_version}}-agent.jar"

***

### jmxexporter_jar_url

Full URL used for Prometheus Exporter Jar Download

Default:  https://repo1.maven.org/maven2/io/prometheus/jmx/jmx_prometheus_javaagent/0.12.0/jmx_prometheus_javaagent-0.12.0.jar

***

### confluent_cli_download_enabled

Boolean to have cp-ansible download the Confluent CLI

Default:  "{{rbac_enabled}}"

***

### confluent_cli_path

Full path on hosts to install the Confluent CLI

Default:  /usr/local/bin/confluent

***

### control_center_custom_log4j

Boolean to enable cp-ansible's Custom Log4j Configuration

Default:  "{{ custom_log4j }}"

***

### control_center_custom_java_args

Custom Java Args to add to the Control Center Process

Default:  ""

***

### control_center_rocksdb_path

Full Path to the RocksDB Data Directory. If left as empty string, cp-ansible will not configure RocksDB

Default:  ""

***

### kafka_broker_custom_log4j

Boolean to enable cp-ansible's Custom Log4j Configuration

Default:  "{{ custom_log4j }}"

***

### kafka_broker_custom_java_args

Custom Java Args to add to the Kafka Process

Default:  ""

***

### kafka_connect_custom_log4j

Boolean to enable cp-ansible's Custom Log4j Configuration

Default:  "{{ custom_log4j }}"

***

### kafka_connect_custom_java_args

Custom Java Args to add to the Connect Process

Default:  ""

***

### kafka_rest_custom_log4j

Boolean to enable cp-ansible's Custom Log4j Configuration

Default:  "{{ custom_log4j }}"

***

### kafka_rest_custom_java_args

Custom Java Args to add to the Rest Proxy Process

Default:  ""

***

### ksql_custom_log4j

Boolean to enable cp-ansible's Custom Log4j Configuration

Default:  "{{ custom_log4j }}"

***

### ksql_custom_java_args

Custom Java Args to add to the ksqlDB Process

Default:  ""

***

### schema_registry_custom_log4j

Boolean to enable cp-ansible's Custom Log4j Configuration

Default:  "{{ custom_log4j }}"

***

### schema_registry_custom_java_args

Custom Java Args to add to the Schema Registry Process

Default:  ""

***

### zookeeper_custom_log4j

Boolean to enable cp-ansible's Custom Log4j Configuration

Default:  "{{ custom_log4j }}"

***

### zookeeper_custom_java_args

Custom Java Args to add to the Zookeeper Process

Default:  ""

***

### kerberos_configure

Boolean to configure Kerberos krb5.conf file, must also set kerberos_realm, keberos_kdc_hostname, kerberos_admin_hostname

Default:  true

***

### kerberos_realm

KDC Server Realm

Default:  "{{ kerberos.realm }}"

***

### keberos_kdc_hostname

KDC Server Hostname

Default:  "{{ kerberos.kdc_hostname }}"

***

### kerberos_admin_hostname

KDC Admin Server Hostname

Default:  "{{ kerberos.realm }}"

