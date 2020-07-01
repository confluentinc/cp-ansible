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

