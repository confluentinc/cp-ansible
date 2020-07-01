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

