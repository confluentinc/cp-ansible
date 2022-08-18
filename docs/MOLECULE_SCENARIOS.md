### molecule/plain-customcerts-rhel

#### Scenario plain-customcerts-rhel test's the following:

Installation of Confluent Platform on CentOS7.

TLS enabled.

SASL Plain enabled.

#### Scenario plain-customcerts-rhel verify test's the following:

Validates that keystores are present on all components.

Validates that SASL mechanism is set to PLAIN on all components.

***

### molecule/confluent-kafka-kerberos-customcerts-rhel

#### Scenario confluent-kafka-kerberos-customcerts-rhel test's the following:

Installation of Confluent Community Edition on CentOS7.

Kerberos protocol.

TLS Enabled.

Custom TLS certificates.

#### Scenario confluent-kafka-kerberos-customcerts-rhel verify test's the following:

Validates GSSAPI Protocol for Kerberos is set.

Validates that SASL_SSL is Protocol is set.

Validates that Confluent Community Packages are used.

***

### molecule/broker-scale-up

#### Scenario broker-scale-up test's the following:

Installation of Confluent Platform on CentOS7.

MTLS enabled.

Installs Three unique Kafka Connect Clusters with unique connectors.

Installs two unique KSQL Clusters.

#### Scenario broker-scale-up verify test's the following:

***

### molecule/scram-rhel

#### Scenario scram-rhel test's the following:

Installs Confluent Platform Cluster on CentOS7.

SCRAM enabled.

#### Scenario scram-rhel verify test's the following:

Validates that SCRAM is enabled on all components.

***

### molecule/kerberos-customcerts-rhel

#### Scenario kerberos-customcerts-rhel test's the following:

Installation of Confluent Platform on CentOS7.

TLS Enabled with custom certs.

Kerberos enabled.

#### Scenario kerberos-customcerts-rhel verify test's the following:

Validates that Kerberos is enabled across all components.

Validates that SASL SSL Protocol is enabled across all components.

***

### molecule/rbac-plain-provided-debian

#### Scenario rbac-plain-provided-debian test's the following:

Installs Confluent Platform Cluster on Debian9.

RBAC enabled.

SASL PLAIN enabled.

TLS with custom certs enabled.

Kafka Broker Customer Listener.

Secrets protection enabled.

Control Center disabled, metrics reporters enabled.

#### Scenario rbac-plain-provided-debian verify test's the following:

Validates Metrics reporter without C3.

Validates that secrets protection is enabled on correct properties.

Validates truststore is present across components.

***

### molecule/rbac-mds-mtls-custom-rhel

#### Scenario rbac-mds-mtls-custom-rhel test's the following:

Installs two Confluent Platform Clusters on CentOS7.

RBAC enabled.

Remote MDS from Cluster2 to Cluster1 (MDS).

Custom TLS certificates.

MTLS enabled on both clusters.

Kafka Broker Customer Listener.

RBAC Additional System Admin.

#### Scenario rbac-mds-mtls-custom-rhel verify test's the following:

Validates that Audit logs are working on topic creation.

Validates that keystores are in place.

Validates that MDS is HTTP on Cluster1 (MDS).

Validates that all components on Cluster2 are pointing to the MDS on Cluster1.

***

### molecule/rbac-mds-mtls-existing-keystore-truststore-ubuntu

#### Scenario rbac-mds-mtls-existing-keystore-truststore-ubuntu test's the following:

Installs Confluent Platform Cluster on CentOS7.

RBAC enabled.

Provided user supplied keystore and truststore already present on the host

MTLS enabled.

Kafka Broker Customer Listener.

RBAC Additional System Admin.

#### Scenario rbac-mds-mtls-existing-keystore-truststore-ubuntu verify test's the following:

Validates that keystores are present on all components.

Validates that LDAPS is working.

Validates that TLS CN is being registered as super user.

***

### molecule/zookeeper-digest-rhel

#### Scenario zookeeper-digest-rhel test's the following:

Installs Zookeeper, Kafka Broker, Schema Registry on CentOS7

Digest authentication enabled.

SASL SCRAM enabled.

Customer Zookeeper Root.

#### Scenario zookeeper-digest-rhel verify test's the following:

Validates authorization mechanism as SASL.

Validates that SCRAM is enabled on the Kafka Broker and Schema Registry.

***

### molecule/mtls-java11-ubuntu

#### Scenario mtls-java11-ubuntu test's the following:

Installation of Confluent Platform on Ubuntu1804.

MTLS enabled.

Java 11.

#### Scenario mtls-java11-ubuntu verify test's the following:

Validates that Java 11 is in use.

***

### molecule/rbac-mds-mtls-custom-kerberos-rhel

#### Scenario rbac-mds-mtls-custom-kerberos-rhel test's the following:

Installs two Confluent Platform Clusters on CentOS7.

RBAC enabled.

Remote MDS from Cluster2 to Cluster1 (MDS).

Custom TLS certificates.

Kafka Broker Customer Listener.

RBAC Additional System Admin.

Kerberos enabled on Cluster2.

MTLS enabled on Cluster2.

#### Scenario rbac-mds-mtls-custom-kerberos-rhel verify test's the following:

Validates that TLS is setup correctly.

Validates that regular user cannot access topics, while super user can.

Validates that MDS is HTTP on Cluster1 (MDS).

Validates that all components on Cluster2 are pointing to the MDS on Cluster1.

***

### molecule/plaintext-basic-rhel

#### Scenario plaintext-basic-rhel test's the following:

Installation of Confluent Platform on CentOS7.

Kafka Rest API Basic Auth.

#### Scenario plaintext-basic-rhel verify test's the following:

Validates that each component has a unique auth user.

Validates that Rest Proxy has correct auth property.

***

### molecule/rbac-mds-kerberos-mtls-custom-rhel

#### Scenario rbac-mds-kerberos-mtls-custom-rhel test's the following:

Installs two Confluent Platform Clusters on CentOS7.

RBAC enabled.

Remote MDS from Cluster2 to Cluster1 (MDS).

Custom TLS certificates.

Kafka Broker Customer Listener.

RBAC Additional System Admin.

Kerberos enabled on Cluster1.

MTLS enabled on Cluster2.

Audit logs enabled on Cluster2, to ship to Cluster1 (MDS).

#### Scenario rbac-mds-kerberos-mtls-custom-rhel verify test's the following:

Validates that Audit logs are working on topic creation.

Validates that keystores are in place.

Validates that regular user cannot access topics, while super user can.

Validates that MDS is HTTP on Cluster1 (MDS).

Validates that all components on Cluster2 are pointing to the MDS on Cluster1.

***

### molecule/plain-erp-tls-rhel

#### Scenario plain-erp-tls-rhel test's the following:

Installation of Confluent Platform on CentOS7.

SASL Plain enabled.

TLS enabled on ERP only.

#### Scenario plain-erp-tls-rhel verify test's the following:

Validates that SASL protocol is PLAIN on all components.

Validates that ERP is accessible over HTTPS.

Validates that Control Center is avaiable over HTTP.

Validates that Control Center has truststore in place.

***

### molecule/mtls-ubuntu

#### Scenario mtls-ubuntu test's the following:

Installation of Confluent Platform on CentOS7.

MTLS enabled.

#### Scenario mtls-ubuntu verify test's the following:

Validates that protocol is set to SSl across all components.

***

### molecule/zookeeper-kerberos-rhel

#### Scenario zookeeper-kerberos-rhel test's the following:

Installs Confluent Platform on CentOS7

Enables Kerberos on Zookeeper.

SASL SCRAM enabled on all components except Zookeeper.

#### Scenario zookeeper-kerberos-rhel verify test's the following:

Validates Zookeeper sasl mechanism.

Validates Kafka Broker and Schema Registry is set to SCRAM.

***

### molecule/custom-user-plaintext-rhel

#### Scenario custom-user-plaintext-rhel test's the following:

Installation of Confluent Platform on CentOS7.

Custom user set on each component.

Custom log appender path on each component.

#### Scenario custom-user-plaintext-rhel verify test's the following:

Creates custom user for Zookeeper.

Creates custom log directory for zookeeper.

Restarts Zookeeper and runs health check to validate changes.

Validates that each component is running with the correct custom user.

Validates that each component is running with the correct custom logging path.

***

### molecule/archive-plain-ubuntu

#### Scenario archive-plain-ubuntu test's the following:

Archive Installation of Confluent Platform on Ubuntu1804.

SASL Plain protocol.

SSL Enabled.

Kafka Connect Confluent Hub Plugins logic (Installs jcustenborder/kafka-connect-spooldir:2.0.43).

Custom log dirs for all components.

#### Scenario archive-plain-ubuntu verify test's the following:

Validates that protocol is set to sasl plain.

Validates that protocol is set to SASL SSL.

Validates log4j config.

***

### molecule/rbac-mds-scram-custom-rhel

#### Scenario rbac-mds-scram-custom-rhel test's the following:

Installs two Confluent Platform Clusters on CentOS7.

RBAC enabled.

Remote MDS from Cluster2 to Cluster1 (MDS).

Custom TLS certificates.

SASL SCRAM enabled on both clusters.

Kafka Broker Customer Listener.

RBAC Additional System Admin.

#### Scenario rbac-mds-scram-custom-rhel verify test's the following:

Validates that protocol is sasl scram.

Validates that MDS is HTTPs on Cluster1 (MDS).

Validates that all components on Cluster2 are pointing to the MDS on Cluster1.

***

### molecule/mtls-customcerts-rhel

#### Scenario mtls-customcerts-rhel test's the following:

Installation of Confluent Platform on CentOS7.

MTLS enabled with custom certificates.

#### Scenario mtls-customcerts-rhel verify test's the following:

Verifies that keystore is present on all components.

Validates the ERP returns values over MTLS.

***

### molecule/archive-plain-rhel

#### Scenario archive-plain-rhel test's the following:

Archive Installation of Confluent Platform on CentOS7.

SASL Plain protocol.

Custom MDS Port.

SSL Enabled.

FIPS Disabled.

Kafka Connect Confluent Hub Plugins logic (Installs jcustenborder/kafka-connect-spooldir:2.0.43).

Custom log dirs for all components.

Logredactor enabled for all components.

#### Scenario archive-plain-rhel verify test's the following:

Validates that SASL SSL protocol is set across all components.

Validates that custom log4j configuration is in place.

Validates that FIPS security is enabled on the Brokers.

Validates that logredactor is functioning properly for all components as per the rule file.

***

### molecule/rbac-mds-kerberos-debian

#### Scenario rbac-mds-kerberos-debian test's the following:

Installs two Confluent Platform Clusters on Debian9.

RBAC enabled.

Remote MDS from Cluster2 to Cluster1 (MDS).

Custom TLS certificates.

Kafka Broker Customer Listener

RBAC Additional System Admin.

#### Scenario rbac-mds-kerberos-debian verify test's the following:

Validates that GSSAPI protocol is set on Cluster2.

Validates that MDS is HTTP on Cluster1 (MDS).

Validates that all components on Cluster2 are pointing to the MDS on Cluster1.

***

### molecule/rbac-kafka-connect-replicator-kerberos-mtls-custom-ubuntu2004

#### Scenario rbac-kafka-connect-replicator-kerberos-mtls-custom-ubuntu2004 test's the following:

Installation of Confluent Platform on Ubuntu2004.

RBAC Enabled.

Customer RBAC system admins.

Kerberos enabled on Cluster1(mds).

MTLS Customer certs enabled on cluster2.

Replicator Configured with Kerberos and MTLS.

#### Scenario rbac-kafka-connect-replicator-kerberos-mtls-custom-ubuntu2004 verify test's the following:

Validates that the Console Consumer can consume data from cluster2, proving that data has been replicated from cluster1 (MDS).

Validates that Replicator is using MTLS with RBAC to Produce data to Cluster2.

Validates that Replicator is using Kerberos with RBAC to Consume from Cluster1 (MDS).

Validates that client ID's are set correctly on Replicator.

Validates that Replicator logging path is valid.

Validates client packages.

***

### molecule/rbac-mtls-rhel8

#### Scenario rbac-mtls-rhel8 test's the following:

Installs Confluent Platform Cluster on CentOS8.

RBAC enabled.

MTLS enabled.

Kafka Broker Customer Listener.

#### Scenario rbac-mtls-rhel8 verify test's the following:

Validates TLS keysizes across all components.

***

### molecule/archive-plain-debian10

#### Scenario archive-plain-debian10 test's the following:

Archive installation of Confluent Platform on Debian 9.

SASL Protocol Plain.

SSL Enabled.

Kafka Connect Confluent Hub Plugins logic (Installs jcustenborder/kafka-connect-spooldir:2.0.43).

Custom log dirs for all components.

#### Scenario archive-plain-debian10 verify test's the following:

Validates that SASL SSL protocol is set across all components.

Validates that custom log4j configuration is in place.

***

### molecule/multi-ksql-connect-rhel

#### Scenario multi-ksql-connect-rhel test's the following:

Installation of Confluent Platform on CentOS7.

MTLS enabled.

Installs Three unique Kafka Connect Clusters with unique connectors.

Installs two unique KSQL Clusters.

#### Scenario multi-ksql-connect-rhel verify test's the following:

Validates that Kafka Connect Cluster1 is running with a valid connector.

Validates that Kafka Connect Cluster2 is running with a valid connector.

Validates that Kafka Connect Cluster3 is running without any connectors.

Validates that two KSQL clusters are running.

Validates that Control Center can connect to each Kafka Connect Cluster.

Validates that Control Center Can connect to each KSQL cluster.

***

### molecule/rbac-kafka-connect-replicator-kerberos-mtls-custom-debian10

#### Scenario rbac-kafka-connect-replicator-kerberos-mtls-custom-debian10 test's the following:

Installation of Confluent Platform on CentOS7.

RBAC Enabled.

Customer RBAC system admins.

Kerberos enabled on Cluster1(mds).

MTLS Customer certs enabled on cluster2.

Replicator Configured with Kerberos and MTLS.

#### Scenario rbac-kafka-connect-replicator-kerberos-mtls-custom-debian10 verify test's the following:

Validates that the Console Consumer can consume data from cluster2, proving that data has been replicated from cluster1 (MDS).

Validates that Replicator is using MTLS with RBAC to Produce data to Cluster2.

Validates that Replicator is using Kerberos with RBAC to Consume from Cluster1 (MDS).

Validates that client ID's are set correctly on Replicator.

Validates that Replicator logging path is valid.

Validates client packages.

***

### molecule/rbac-mtls-rhel

#### Scenario rbac-mtls-rhel test's the following:

Installs Confluent Platform Cluster on CentOS7.

RBAC enabled.

MTLS enabled.

Secrets protection disabled

Kafka Broker Customer Listener.

RBAC Additional System Admin.

Provided SSL Principal Mapping rule

#### Scenario rbac-mtls-rhel verify test's the following:

Validates TLS version across all components.

Validates super users are present.

Validates that secrets protection is masking the correct properties.

Validates Kafka Connect secrets registry.

Validates Cluster Registry.

Validates the filter resolve_principal with different ssl.mapping.rule

***

### molecule/connect-scale-up

#### Scenario connect-scale-up test's the following:

connect-scale-up

#### Scenario connect-scale-up verify test's the following:

connect-scale-up verify

***

### molecule/zookeeper-mtls-rhel

#### Scenario zookeeper-mtls-rhel test's the following:

Installs Confluent Platform on CentOS7

Enables MTLS Auth on Zookeeper.

SASL SCRAM enabled on all components except Zookeeper.

Customer zookeeper root.

Secrets Protection enabled.

#### Scenario zookeeper-mtls-rhel verify test's the following:

Validates that Confluent CLI is installed.

Validates that Zookeeper is using MTLS for auth.

Validates that other components are using SCRAM for auth.

Validates that Secrets protection is applied to the correct properties.

***

### molecule/ccloud

#### Scenario ccloud test's the following:

Simulates linking an on prem cluster to Confluent Cloud on CentOS7.

TLS Enabled.

SASL Plain Enabled.

Schema Registry uses Basic Auth.

#### Scenario ccloud verify test's the following:

Validates that Schema Registry SASL Plain configs are correct.

Validates that Replication Factor is 3.

Validates that all components connect to Confluent Cloud.

***

### molecule/kafka-connect-replicator-mtls-scram-rhel

#### Scenario kafka-connect-replicator-mtls-scram-rhel test's the following:

Installation of Confluent Platform on CentOS7 with two distinct clusters.

Installation of Confluent Replicator.

Cluster1 (MDS) is running MTLS with Custom Certs.

Cluster2 is running SCRAM with TLS enabled.

Replicator consumes from Cluster1 (MDS) using MTLS with Custom Certs for TLS.

Replicator Produces to Cluster2 using SCRAM with Custom Certs for TLS.

Tests default values for replicator configuration works.

#### Scenario kafka-connect-replicator-mtls-scram-rhel verify test's the following:

Validates that the Console Consumer can consume data from cluster2, proving that data has been replicated from cluster1 (MDS).

Validates that Replicator is using SCRAM and TLS to Produce to cluster2.

Validates that Replicator is using MTLS to Consume from Cluster1 (MDS).

Validates that client ID's are set correctly on Replicator.

***

### molecule/rbac-kafka-connect-replicator-kerberos-mtls-custom-rhel

#### Scenario rbac-kafka-connect-replicator-kerberos-mtls-custom-rhel test's the following:

Installation of Confluent Platform on CentOS7 with RBAC and Confluent Replicator.

RBAC enabled.

RBAC additional system admin user.

TLS custom certificates.

Kafka Broker Customer listener.

Kafka clusters are using names for cluster registry.

Kerberos enabled on cluster1 (MDS), no TLS.

MTLS enabled on cluster2.

External MDS enabled on cluster2.

Kafka Connect Replicator with OAUTH for Authorization to Cluster1 (MDS).

Kafka Connect Replicator Consumes with kerberos from Cluster1 (MDS).

Kafka Connect Replicator Produces to Cluster2 using MTLS.

Kafka Connect Replicator uses default values for Monitoring Interceptors.

#### Scenario rbac-kafka-connect-replicator-kerberos-mtls-custom-rhel verify test's the following:

Validates that the Console Consumer can consume data from cluster2, proving that data has been replicated from cluster1 (MDS).

Validates that Replicator is using MTLS with RBAC to Produce data to Cluster2.

Validates that Replicator is using Kerberos with RBAC to Consume from Cluster1 (MDS).

Validates that client ID's are set correctly on Replicator.

Validates that Replicator logging path is valid.

***

### molecule/kafka-connect-replicator-plain-kerberos-rhel

#### Scenario kafka-connect-replicator-plain-kerberos-rhel test's the following:

Installation of Confluent Platform on CentOS7 with two distinct clusters.

Installation of Confluent Replicator.

Cluster1 (MDS) is running SASL Plain with Custom Certs.

Cluster2 is running Kerberos with TLS enabled.

Replicator consumes from Cluster1 (MDS) using SASL Plain with Custom Certs for TLS.

Replicator Produces to Cluster2 using Kerberos with Custom Certs for TLS.

Tests custom client IDs for Replicator.

#### Scenario kafka-connect-replicator-plain-kerberos-rhel verify test's the following:

Validates that the Console Consumer can consume data from cluster2, proving that data has been replicated from cluster1 (MDS).

Validates that Replicator is using Kerberos and TLS to Produce data to Cluster2.

Validates that Replicator is using SASL PLAIN with TLS to Consume from Cluster1 (MDS).

Validates that client ID's are set correctly on Replicator.

***

### molecule/plaintext-rhel

#### Scenario plaintext-rhel test's the following:

Installation of Confluent Platform on CentOS7.

Copying local JMX agent.

Copying local files.

#### Scenario plaintext-rhel verify test's the following:

Validates Package version installed.

Validates log4j configuration.

Validates all components are running with plaintext.

Validates that copied files are present.

Validates that JMX exporter was copied and is running.

***

### molecule/archive-scram-rhel

#### Scenario archive-scram-rhel test's the following:

Archive Installation of Confluent Platform on CentOS7.

SASL SCRAM protocol.

TLS Enabled.

Secrets Protection.

Custom Archive owner.

#### Scenario archive-scram-rhel verify test's the following:

Validates that customer user and group on archive are set.

Validates that SASL SCRAM is Protocol is set.

Validates that TLS is configured properly.

***

### molecule/archive-plain-ubuntu2004

#### Scenario archive-plain-ubuntu2004 test's the following:

Archive Installation of Confluent Platform on Ubuntu2004.

SASL Plain protocol.

SSL Enabled.

Kafka Connect Confluent Hub Plugins logic (Installs jcustenborder/kafka-connect-spooldir:2.0.43).

Custom log dirs for all components.

#### Scenario archive-plain-ubuntu2004 verify test's the following:

Validates that protocol is set to sasl plain.

Validates that protocol is set to SASL SSL.

Validates log4j config.

***

### molecule/zookeeper-tls-rhel

#### Scenario zookeeper-tls-rhel test's the following:

Installs Confluent Platform on CentOS7

Enables SASL SCRAM Auth on Zookeeper.

TLS enabled.

Customer zookeeper root.

Secrets Protection enabled.

Jolokia has TLS disabled.

#### Scenario zookeeper-tls-rhel verify test's the following:

Validates that Zookeeper is using TLS.

Validates that other components are using SCRAM for auth.

***

### molecule/kerberos-rhel

#### Scenario kerberos-rhel test's the following:

Installation of Confluent Platform on CentOS7.

Kerberos enabled.

#### Scenario kerberos-rhel verify test's the following:

Validates that Kerberos is enabled across all components.

Validates that SASL SSL Plaintext is enabled across all components.

***

### molecule/mtls-custombundle-rhel

#### Scenario mtls-custombundle-rhel test's the following:

Installation of Confluent Platform Edition on CentOS7.

MTLS Enabled with custom certificates.

Tests custom filtering properties for Secrets Protection.

TLS is disabled for Zookeeper.

#### Scenario mtls-custombundle-rhel verify test's the following:

Validates that Keystore is present.

***

### molecule/mtls-java11-debian

#### Scenario mtls-java11-debian test's the following:

Installation of Confluent Platform on Debian9.

MTLS enabled.

Java 11.

#### Scenario mtls-java11-debian verify test's the following:

Validates that Java 11 is in use.

***

### molecule/rbac-scram-custom-rhel

#### Scenario rbac-scram-custom-rhel test's the following:

Installs Confluent Platform Cluster on CentOS7.

RBAC enabled.

SCRAM enabled.

TLS with custom certs enabled.

Additional System Admins added.

Additional Scram Users added.

Kafka Connect Custom arguments.

#### Scenario rbac-scram-custom-rhel verify test's the following:

Validates keystore is present across all components.

Validates that ldap is configured.

Validates that Confluent Balancer is enabled.

Validates total number of clusters for user2.

Validates truststore across all components.

***

### molecule/mtls-java11-rhel

#### Scenario mtls-java11-rhel test's the following:

Installation of Confluent Platform on CentOS7.

MTLS enabled.

Java 11.

#### Scenario mtls-java11-rhel verify test's the following:

Validates that Java 11 is in use.

***

### molecule/ksql-scale-up

#### Scenario ksql-scale-up test's the following:

Installation of Confluent Platform on CentOS7.

MTLS enabled.

Installs two unique KSQL Clusters, each having 1 node.

Scales it later to 4 nodes, adding 1 node to each of the KSQL clusters

#### Scenario ksql-scale-up verify test's the following:

Validates that 2 new ksql nodes are added properly

Validates that two KSQL clusters are running

Validates that ksql3 is added to KSQL cluster

Validates that ksql4 is added to KSQL cluster

Validates that Control Center Can connect to each KSQL cluster

***

### molecule/provided-rhel

#### Scenario provided-rhel test's the following:

Installation of Confluent Platform on CentOS7.

TLS enabled.

Customer keystore alias.

#### Scenario provided-rhel verify test's the following:

Validates that keystores are in place across all components.

***

### molecule/rbac-mds-plain-custom-rhel

#### Scenario rbac-mds-plain-custom-rhel test's the following:

Installs two Confluent Platform Clusters on CentOS7.

RBAC enabled.

Remote MDS from Cluster2 to Cluster1 (MDS).

Custom TLS certificates.

SASL PLAIN enabled on both clusters.

Kafka Broker Customer Listener.

RBAC Additional System Admin.

#### Scenario rbac-mds-plain-custom-rhel verify test's the following:

Validates that protocol is sasl plain.

Validates that MDS is HTTPs on Cluster1 (MDS).

Validates that all components on Cluster2 are pointing to the MDS on Cluster1.

***

### molecule/zookeeper-mtls-secrets-rhel

#### Scenario zookeeper-mtls-secrets-rhel test's the following:

Installs Confluent Platform on CentOS7

Enables SASL SCRAM Auth on Zookeeper.

TLS enabled.

Customer zookeeper root.

Secrets Protection enabled.

Jolokia has TLS disabled.

#### Scenario zookeeper-mtls-secrets-rhel verify test's the following:

Validates that Confluent CLI is installed.

Validates that Zookeeper is using SCRAM for auth.

Validates that other components are using SCRAM for auth.

Validates that Secrets protection is applied to the correct properties.

***

### molecule/mtls-ubuntu-acl

#### Scenario mtls-ubuntu-acl test's the following:

Installation of Confluent Platform on Ubuntu1804.

MTLS enabled.

ACL authorization.

#### Scenario mtls-ubuntu-acl verify test's the following:

Validates that MTLS is enabled.

Validates mapping rules for ACLs.

Validates ACL users.

***

### molecule/cp-kafka-plain-rhel

#### Scenario cp-kafka-plain-rhel test's the following:

Installation of Confluent Community Edition on CentOS7.

SASL Plain Auth.

#### Scenario cp-kafka-plain-rhel verify test's the following:

Validates that SASL Plaintext protocol is set.

***

### molecule/rbac-mtls-provided-ubuntu

#### Scenario rbac-mtls-provided-ubuntu test's the following:

Installs Confluent Platform Cluster on CentOS7.

RBAC enabled.

Provided Custom Keystore and Truststore for TLS..

MTLS enabled.

Kafka Broker Customer Listener.

RBAC Additional System Admin.

#### Scenario rbac-mtls-provided-ubuntu verify test's the following:

Validates that keystores are present on all components.

Validates that LDAPS is working.

Validates that TLS CN is being registered as super user.

***

### molecule/mtls-debian

#### Scenario mtls-debian test's the following:

Installation of Confluent Platform on Debian9.

MTLS Enabled.

ERP Disabled.

Kafka Connect Confluent Hub Plugins logic (Installs jcustenborder/kafka-connect-spooldir:2.0.43).

Default replication factor set to 4.

Jolokia Enabled.

Confluent CLI Download enabled.

Schema Validation is enabled.

#### Scenario mtls-debian verify test's the following:

Validates that SSL Protocol is set.

Validates that replication factor is 4.

Validates that Jolokia end point is reachable.

Validates that Schema Validation is working.

Validates that CLI is present.

***

### molecule/archive-community-plaintext-rhel

#### Scenario archive-community-plaintext-rhel test's the following:

Archive Installation of Confluent Community Edition on CentOS7

JAVA 17.

Custom Package Repository for Confluent Platform.

Custom Package Repository for Confluent CLI.

Control Center is not included in the Confluent Community Edition.

#### Scenario archive-community-plaintext-rhel verify test's the following:

Validates that Confluent CLI is installed.

***

### molecule/archive-plain-debian

#### Scenario archive-plain-debian test's the following:

Archive installation of Confluent Platform on Debian 9.

SASL Protocol Plain.

SSL Enabled.

Kafka Connect Confluent Hub Plugins logic (Installs jcustenborder/kafka-connect-spooldir:2.0.43).

Custom log dirs for all components.

#### Scenario archive-plain-debian verify test's the following:

Validates that SASL SSL protocol is set across all components

Validates that custom log4j configuration is in place.

Validates that Confluent CLI is installed.

***

### molecule/rbac-kerberos-debian

#### Scenario rbac-kerberos-debian test's the following:

Installation of Confluent Platform on Debian9.

RBAC enabled.

Kerberos enabled.

Kafka broker custom listener.

RBAC additional system admin user.

#### Scenario rbac-kerberos-debian verify test's the following:

Validates that protocol set to GSSAPI.

Validates that a regular user cannot access topics.

Validates that a super user can access topics.

Validates that all components are pointing to the MDS for authorization.

***

### molecule/plain-rhel

#### Scenario plain-rhel test's the following:

Installation of Confluent Platform on CentOS7.

SASL Plain enabled.

Control Plane listener enabled.

Kafka Connect Confluent Hub Plugins logic (Installs jcustenborder/kafka-connect-spooldir:2.0.43).

Custom Service Unit overrides.

Custom log4j appender names.

#### Scenario plain-rhel verify test's the following:

Validates that custom log4j appenders are present on each component.

Validates that Service Description has been overridden.

Validates that SASL Plaintext protocol is set across components.

Validates that Connectors are present on Kafka Connect.

***

