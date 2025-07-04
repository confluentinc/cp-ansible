### molecule/archive-community-plaintext-rhel

#### Scenario archive-community-plaintext-rhel test's the following:

Archive Installation of Confluent Community Edition on Oracle Linux 9.

JAVA 17.

Custom Package Repository for Confluent Platform.

Custom Package Repository for Confluent CLI.

Control Center is not included in the Confluent Community Edition.

#### Scenario archive-community-plaintext-rhel verify test's the following:

Validates that Confluent CLI is installed.

***

### molecule/archive-plain-debian

#### Scenario archive-plain-debian test's the following:

Archive installation of Confluent Platform on Debian 12.

SASL Protocol Plain.

SSL Enabled.

Kafka Connect Confluent Hub Plugins logic (Installs jcustenborder/kafka-connect-spooldir:2.0.43).

Custom log dirs for all components.

#### Scenario archive-plain-debian verify test's the following:

Validates that SASL SSL protocol is set across all components

Validates that custom log4j configuration is in place.

Validates that Java 17 is in Use

Validates that Confluent CLI is installed.

***

### molecule/archive-plain-rhel-fips

#### Scenario archive-plain-rhel-fips test's the following:

Archive Installation of Confluent Platform on RHEL9.

SASL Plain protocol.

Custom MDS Port.

SSL Enabled.

FIPS Enabled.

Kafka Connect Confluent Hub Plugins logic (Installs jcustenborder/kafka-connect-spooldir:2.0.43).

Custom log dirs for all components.

Logredactor enabled for all components.

#### Scenario archive-plain-rhel-fips verify test's the following:

Validates that SASL SSL protocol is set across all components.

Validates that custom log4j configuration is in place.

Validates that FIPS security is enabled on the Brokers.

Validates that logredactor is functioning properly for all components as per the rule file.

Validates that FIPS is in use in OpenSSL.

***

### molecule/archive-plain-ubuntu

#### Scenario archive-plain-ubuntu test's the following:

Archive Installation of Confluent Platform on Ubuntu2404.

SASL Plain protocol.

SSL Enabled.

Kafka Connect Confluent Hub Plugins logic (Installs jcustenborder/kafka-connect-spooldir:2.0.43).

Custom log dirs for all components.

#### Scenario archive-plain-ubuntu verify test's the following:

Validates that protocol is set to sasl plain.

Validates that protocol is set to SASL SSL.

Validates log4j config.

***

### molecule/archive-scram-rhel

#### Scenario archive-scram-rhel test's the following:

Archive Installation of Confluent Platform on Oracle Linux 8.

SASL SCRAM protocol.

TLS Enabled.

Custom Archive owner.

#### Scenario archive-scram-rhel verify test's the following:

Validates that customer user and group on archive are set.

Validates that SASL SCRAM is Protocol is set.

Validates that TLS is configured properly.

***

### molecule/broker-scale-up

#### Scenario broker-scale-up test's the following:

Installation of Confluent Platform on RHEL8.

MTLS enabled.

Installs Three unique Kafka Connect Clusters with unique connectors.

Installs two unique KSQL Clusters.

#### Scenario broker-scale-up verify test's the following:

***

### molecule/ccloud

#### Scenario ccloud test's the following:

Simulates linking an on prem cluster to Confluent Cloud on RHEL8.

TLS Enabled.

SASL Plain Enabled.

Schema Registry uses Basic Auth.

#### Scenario ccloud verify test's the following:

Validates that Schema Registry SASL Plain configs are correct.

Validates that Replication Factor is 3.

Validates that all components connect to Confluent Cloud.

***

### molecule/confluent-kafka-kerberos-customcerts-rhel

#### Scenario confluent-kafka-kerberos-customcerts-rhel test's the following:

Installation of Confluent Community Edition on RHEL8.

Kerberos protocol.

TLS Enabled.

Custom TLS certificates.

#### Scenario confluent-kafka-kerberos-customcerts-rhel verify test's the following:

Validates GSSAPI Protocol for Kerberos is set.

Validates that SASL_SSL is Protocol is set.

Validates that Confluent Community Packages are used.

***

### molecule/connect-scale-up

#### Scenario connect-scale-up test's the following:

connect-scale-up

#### Scenario connect-scale-up verify test's the following:

connect-scale-up verify

***

### molecule/cp-kafka-plain-rhel

#### Scenario cp-kafka-plain-rhel test's the following:

Installation of Confluent Community Edition on RHEL8.

SASL Plain Auth.

Broker and Kraft Controller co-located while Migration

Kafka broker has custom listener at port 9093

Kraft Controller is running at port 9094

#### Scenario cp-kafka-plain-rhel verify test's the following:

Validates that SASL Plaintext protocol is set.

***

### molecule/custom-user-plaintext-rhel

#### Scenario custom-user-plaintext-rhel test's the following:

Installation of Confluent Platform on RHEL8.

Custom user set on each component.

Custom log appender path on each component.

Controller and Broker co-located while migration

#### Scenario custom-user-plaintext-rhel verify test's the following:

Creates custom user for kafka controller.

Creates custom log directory for kafka controller.

Restarts kafka controller and runs health check to validate changes.

Validates that each component is running with the correct custom user.

Validates that each component is running with the correct custom logging path.

***

### molecule/kafka-connect-replicator-plain-kerberos-rhel-fips

#### Scenario kafka-connect-replicator-plain-kerberos-rhel-fips test's the following:

Installation of Confluent Platform on RHEL8 with two distinct clusters.

Installation of Confluent Replicator.

Cluster1 (MDS) is running SASL Plain with Custom Certs.

Cluster2 is running Kerberos with TLS enabled.

Replicator consumes from Cluster1 (MDS) using SASL Plain with Custom Certs for TLS.

Replicator Produces to Cluster2 using Kerberos with Custom Certs for TLS.

Tests custom client IDs for Replicator.

FIPS enabled on both clusters.

#### Scenario kafka-connect-replicator-plain-kerberos-rhel-fips verify test's the following:

Validates that the Console Consumer can consume data from cluster2, proving that data has been replicated from cluster1 (MDS).

Validates that Replicator is using Kerberos and TLS to Produce data to Cluster2.

Validates that Replicator is using SASL PLAIN with TLS to Consume from Cluster1 (MDS).

Validates that client ID's are set correctly on Replicator.

Validates that FIPS is in use in OpenSSL.

***

### molecule/kerberos-customcerts-rhel

#### Scenario kerberos-customcerts-rhel test's the following:

Installation of Confluent Platform on RHEL8.

TLS Enabled with custom certs.

Kerberos enabled.

#### Scenario kerberos-customcerts-rhel verify test's the following:

Validates that Kerberos is enabled across all components.

Validates that SASL SSL Protocol is enabled across all components.

***

### molecule/kerberos-rhel

#### Scenario kerberos-rhel test's the following:

Installation of Confluent Platform on Oracle Linux 9.

Kerberos enabled with custom client config path

Creates a Connector in Connect cluster

#### Scenario kerberos-rhel verify test's the following:

Validates that Kerberos is enabled across all components.

Validates that SASL SSL Plaintext is enabled across all components.

Validates that Connector is running

***

### molecule/ksql-scale-up

#### Scenario ksql-scale-up test's the following:

Installation of Confluent Platform on Alma Linux 9.

MTLS enabled.

Installs two unique KSQL Clusters, each having 1 node.

Scales it later to 4 nodes, adding 1 node to each of the KSQL clusters

Use Java 8

#### Scenario ksql-scale-up verify test's the following:

Validates that 2 new ksql nodes are added properly

Validates that two KSQL clusters are running

Validates that ksql3 is added to KSQL cluster

Validates that ksql4 is added to KSQL cluster

Validates that Control Center Can connect to each KSQL cluster

***

### molecule/mini-setup-ext-mds-mtls

#### Scenario mini-setup-ext-mds-mtls test's the following:

Installs Confluent Platform Cluster on ubi9.

RBAC over mTLS enabled.

Centralized MDS.

File based login to C3 using overrides.

#### Scenario mini-setup-ext-mds-mtls verify test's the following:

Validates that SSL Protocol is set.

Validates ssl.client.authentication is set to REQUIRED.

***

### molecule/mini-setup-ldap-mtls-fips

#### Scenario mini-setup-ldap-mtls-fips test's the following:

Installs Confluent Platform Cluster on ubi9.

RBAC over mTLS+LDAP enabled.

MDS accepts LDAP credentials and mTLS certs.

LDAP based login to C3.

#### Scenario mini-setup-ldap-mtls-fips verify test's the following:

Validates that SSL Protocol is set.

Validates ssl.client.authentication is set to REQUIRED.

***

### molecule/mini-setup-mtls

#### Scenario mini-setup-mtls test's the following:

Installs Confluent Platform Cluster on ubi9.

RBAC over mTLS enabled.

File based login to C3 using overrides.

#### Scenario mini-setup-mtls verify test's the following:

Validates that SSL Protocol is set.

Validates ssl.client.authentication is set to REQUIRED.

***

### molecule/mini-setup-mtls-fips

#### Scenario mini-setup-mtls-fips test's the following:

Installs Confluent Platform Cluster on ubi9.

RBAC over mTLS enabled.

File based login to C3 using overrides.

#### Scenario mini-setup-mtls-fips verify test's the following:

Validates that SSL Protocol is set.

Validates ssl.client.authentication is set to REQUIRED.

***

### molecule/mini-setup-oauth-mtls

#### Scenario mini-setup-oauth-mtls test's the following:

Installs Confluent Platform Cluster on ubi9.

RBAC over mTLS+OAuth enabled.

SSO authentication using OIDC in Control center using Okta IdP.

#### Scenario mini-setup-oauth-mtls verify test's the following:

Validates that SSL Protocol is set.

Validates ssl.client.authentication is set to REQUIRED.

***

### molecule/mini-setup-out-ldap-in-mtls

#### Scenario mini-setup-out-ldap-in-mtls test's the following:

Installs Confluent Platform Cluster on ubi9.

RBAC over mTLS+LDAP enabled.

Outside CP to CP communication over LDAP.

Internal CP communication over mTLS.

LDAP based login to C3.

#### Scenario mini-setup-out-ldap-in-mtls verify test's the following:

Validates that SSL Protocol is set.

Validates ssl.client.authentication is set to REQUIRED.

***

### molecule/mini-setup-out-oauth-in-mtls

#### Scenario mini-setup-out-oauth-in-mtls test's the following:

Installs Confluent Platform Cluster on ubi9.

RBAC over mTLS+OAuth enabled.

Outside CP to CP communication over OAuth.

Internal CP communication over mTLS.

SSO authentication using OIDC in Control center using Okta IdP.

#### Scenario mini-setup-out-oauth-in-mtls verify test's the following:

Validates that SSL Protocol is set.

Validates ssl.client.authentication is set to REQUIRED.

***

### molecule/mini-setup-partial-mtls

#### Scenario mini-setup-partial-mtls test's the following:

Installs Confluent Platform Cluster on ubi9.

RBAC over mTLS enabled.

File based login to C3 using overrides.

#### Scenario mini-setup-partial-mtls verify test's the following:

***

### molecule/mini-setup-partial-mtls2

#### Scenario mini-setup-partial-mtls2 test's the following:

Installs Confluent Platform Cluster on ubi9.

RBAC over mTLS enabled.

File based login to C3 using overrides.

#### Scenario mini-setup-partial-mtls2 verify test's the following:

***

### molecule/mtls-custombundle-rhel-fips

#### Scenario mtls-custombundle-rhel-fips test's the following:

Installation of Confluent Platform Edition on RHEL9.

MTLS Enabled with custom certificates.

Tests custom filtering properties for Secrets Protection.

FIPS enabled

#### Scenario mtls-custombundle-rhel-fips verify test's the following:

Validates that Keystore is present.

***

### molecule/mtls-customcerts-rhel

#### Scenario mtls-customcerts-rhel test's the following:

Installation of Confluent Platform on RHEL8.

MTLS enabled with custom certificates.

#### Scenario mtls-customcerts-rhel verify test's the following:

Verifies that keystore is present on all components.

Validates the ERP returns values over MTLS.

***

### molecule/mtls-debian12

#### Scenario mtls-debian12 test's the following:

Installation of Confluent Platform on Debian 12.

MTLS Enabled.

ERP Disabled.

Kafka Connect Confluent Hub Plugins logic (Installs jcustenborder/kafka-connect-spooldir:2.0.43).

Default replication factor set to 4.

Jolokia Enabled.

Confluent CLI Download enabled.

Schema Validation is enabled.

#### Scenario mtls-debian12 verify test's the following:

Validates that SSL Protocol is set.

Validates that replication factor is 4.

Validates that Jolokia end point is reachable.

Validates that Schema Validation is working.

Validates that CLI is present.

Validates that Java 17 is in Use

***

### molecule/mtls-java17-ubuntu

#### Scenario mtls-java17-ubuntu test's the following:

Installation of Confluent Platform on Ubuntu2404.

MTLS enabled.

#### Scenario mtls-java17-ubuntu verify test's the following:

Validates that protocol is set to SSl across all components.

***

### molecule/mtls-java21-rhel-fips

#### Scenario mtls-java21-rhel-fips test's the following:

Installation of Confluent Platform on Alma Linux 9.

MTLS enabled.

Java 21.

FIPS enabled

#### Scenario mtls-java21-rhel-fips verify test's the following:

Validates that Java 21 is in use.

Validates that FIPS security is enabled on the Brokers.

Validates that FIPS is in use in OpenSSL.

***

### molecule/mtls-ubuntu

#### Scenario mtls-ubuntu test's the following:

Installation of Confluent Platform on Ubuntu2404.

MTLS enabled.

#### Scenario mtls-ubuntu verify test's the following:

Validates that protocol is set to SSl across all components.

***

### molecule/multi-ksql-connect-rhel

#### Scenario multi-ksql-connect-rhel test's the following:

Installation of Confluent Platform on RHEL8.

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

### molecule/oauth-archive-plain-ubuntu2004

#### Scenario oauth-archive-plain-ubuntu2004 test's the following:

Archive Installation of Confluent Platform on Ubuntu2004.

SASL Plain protocol.

SSL Enabled.

Kafka Connect Confluent Hub Plugins logic (Installs jcustenborder/kafka-connect-spooldir:2.0.43).

Custom log dirs for all components.

Deploy Connector on Connect Cluster.

#### Scenario oauth-archive-plain-ubuntu2004 verify test's the following:

Validates that protocol is set to sasl plain.

Validates that protocol is set to SASL SSL.

Validates log4j config.

Validates that Connector is Running.

***

### molecule/oauth-kafka-connect-replicator-mtls-rhel

#### Scenario oauth-kafka-connect-replicator-mtls-rhel test's the following:

Installation of Confluent Platform on RHEL8 with two distinct clusters.

Installation of Confluent Replicator.

Cluster1 (MDS) is running MTLS with Custom Certs.

Cluster2 is running OAuth with TLS enabled.

Replicator consumes from Cluster1 (MDS) using MTLS with Custom Certs for TLS.

Replicator Produces to Cluster2 using OAuth with Custom Certs for TLS.

Tests default values for replicator configuration works.

#### Scenario oauth-kafka-connect-replicator-mtls-rhel verify test's the following:

Validates that the Console Consumer can consume data from cluster2, proving that data has been replicated from cluster1 (MDS).

Validates that Replicator is using OAuth and TLS to Produce to cluster2.

Validates that Replicator is using MTLS to Consume from Cluster1 (MDS).

Validates that client ID's are set correctly on Replicator.

***

### molecule/oauth-mtls-debian

#### Scenario oauth-mtls-debian test's the following:

Installation of Confluent Platform on Debian10.

MTLS enabled.

#### Scenario oauth-mtls-debian verify test's the following:

Validates that Java 11 is in use.

***

### molecule/oauth-mtls-ubuntu-acl

#### Scenario oauth-mtls-ubuntu-acl test's the following:

Installation of Confluent Platform on Ubuntu2404.

MTLS enabled.

ACL authorization.

#### Scenario oauth-mtls-ubuntu-acl verify test's the following:

Validates that MTLS is enabled.

Validates mapping rules for ACLs.

Validates ACL users.

Validated ACL creation.

***

### molecule/oauth-plain-archive

#### Scenario oauth-plain-archive test's the following:

Installation of Confluent Platform on RHEL9.

SASL Plain enabled.

Control Plane listener enabled.

Kafka Connect Confluent Hub Plugins logic (Installs jcustenborder/kafka-connect-spooldir:2.0.43).

Custom Service Unit overrides.

Custom log4j appender names.

#### Scenario oauth-plain-archive verify test's the following:

Validates that custom log4j appenders are present on each component.

Validates that Service Description has been overridden.

Validates that SASL Plaintext protocol is set across components.

Validates that Connectors are present on Kafka Connect.

***

### molecule/oauth-plain-debian12

#### Scenario oauth-plain-debian12 test's the following:

Installation of Confluent Platform on Debian12.

SASL Plain enabled.

Control Plane listener enabled.

Kafka Connect Confluent Hub Plugins logic (Installs jcustenborder/kafka-connect-spooldir:2.0.43).

Custom Service Unit overrides.

Custom log4j appender names.

#### Scenario oauth-plain-debian12 verify test's the following:

Validates that custom log4j appenders are present on each component.

Validates that Service Description has been overridden.

Validates that SASL Plaintext protocol is set across components.

Validates that Connectors are present on Kafka Connect.

***

### molecule/oauth-plain-rhel

#### Scenario oauth-plain-rhel test's the following:

Installation of Confluent Platform on RHEL9.

SASL Plain enabled.

Control Plane listener enabled.

Kafka Connect Confluent Hub Plugins logic (Installs jcustenborder/kafka-connect-spooldir:2.0.43).

Custom Service Unit overrides.

Custom log4j appender names.

#### Scenario oauth-plain-rhel verify test's the following:

Validates that custom log4j appenders are present on each component.

Validates that Service Description has been overridden.

Validates that SASL Plaintext protocol is set across components.

Validates that Connectors are present on Kafka Connect.

***

### molecule/oauth-rbac-kafka-connect-replicator-kerberos-mtls-custom-rhel

#### Scenario oauth-rbac-kafka-connect-replicator-kerberos-mtls-custom-rhel test's the following:

Installation of Confluent Platform on RHEL8 with RBAC and Confluent Replicator.

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

#### Scenario oauth-rbac-kafka-connect-replicator-kerberos-mtls-custom-rhel verify test's the following:

Validates that the Console Consumer can consume data from cluster2, proving that data has been replicated from cluster1 (MDS).

Validates that Replicator is using MTLS with RBAC to Produce data to Cluster2.

Validates that Replicator is using Kerberos with RBAC to Consume from Cluster1 (MDS).

Validates that client ID's are set correctly on Replicator.

Validates that Replicator logging path is valid.

***

### molecule/oauth-rbac-mds-kerberos-debian

#### Scenario oauth-rbac-mds-kerberos-debian test's the following:

Installs two Confluent Platform Clusters on Debian10.

RBAC enabled.

Remote MDS from Cluster2 to Cluster1 (MDS).

Custom TLS certificates.

Kafka Broker Customer Listener

RBAC Additional System Admin.

SSO authentication using OIDC in Control center using Azure IdP

#### Scenario oauth-rbac-mds-kerberos-debian verify test's the following:

Validates that OAUTHBEARER protocol is set on Cluster2.

Validates that MDS is HTTP on Cluster1 (MDS).

Validates that all components on Cluster2 are pointing to the MDS on Cluster1.

Validates that Java 17 is in Use

Validates OIDC authenticate api for SSO in Control Center

***

### molecule/oauth-rbac-mds-scram-custom-rhel

#### Scenario oauth-rbac-mds-scram-custom-rhel test's the following:

Installs two Confluent Platform Clusters on Rocky Linux 9.

RBAC enabled.

Remote MDS from Cluster2 to Cluster1 (MDS).

Custom TLS certificates.

SASL SCRAM enabled on both clusters.

Kafka Broker Customer Listener.

RBAC Additional System Admin.

#### Scenario oauth-rbac-mds-scram-custom-rhel verify test's the following:

Validates that protocol is sasl scram.

Validates that MDS is HTTPs on Cluster1 (MDS).

Validates that all components on Cluster2 are pointing to the MDS on Cluster1.

***

### molecule/oauth-rbac-mtls-provided-ubuntu

#### Scenario oauth-rbac-mtls-provided-ubuntu test's the following:

Installs Confluent Platform Cluster on Ubuntu2404.

RBAC enabled.

Provided Custom Keystore and Truststore for TLS..

MTLS enabled.

Kafka Broker Customer Listener.

RBAC Additional System Admin.

#### Scenario oauth-rbac-mtls-provided-ubuntu verify test's the following:

Validates that keystores are present on all components.

Validates that LDAPS is working.

Validates that TLS CN is being registered as super user.

***

### molecule/oauth-rbac-plain-provided-debian12

#### Scenario oauth-rbac-plain-provided-debian12 test's the following:

Installs Confluent Platform Cluster on Debian 12.

RBAC enabled.

SASL PLAIN enabled.

TLS with custom certs enabled.

Kafka Broker Customer Listener.

Secrets protection enabled.

Control Center disabled, metrics reporters enabled.

LdapAuthenticateCallbackHandler for AuthN

Creates two unique Connectors in Connect cluster

#### Scenario oauth-rbac-plain-provided-debian12 verify test's the following:

Validates Metrics reporter without C3.

Validates that secrets protection is enabled on correct properties.

Validates truststore is present across components.

Validates that Java 17 is in Use

Validates LDAP authentication

***

### molecule/oauth-rbac-plain-rhel8

#### Scenario oauth-rbac-plain-rhel8 test's the following:

Installs Confluent Platform Cluster on Oracle Linux 8.

RBAC enabled.

Kafka Broker Custom Listener.

OAuth using keycloak idp on all cp components

SSO authentication using OIDC in Control center using Okta IdP

#### Scenario oauth-rbac-plain-rhel8 verify test's the following:

Validates TLS keysizes across all components.

Validates OIDC authenticate api for SSO in Control Center

***

### molecule/plain-customcerts-rhel-fips

#### Scenario plain-customcerts-rhel-fips test's the following:

Installation of Confluent Platform on Oracle Linux 8.

TLS enabled.

SASL Plain enabled.

Custom certificates on remote host

FIPS enabled

#### Scenario plain-customcerts-rhel-fips verify test's the following:

Validates that keystores are present on all components.

Validates that SASL mechanism is set to PLAIN on all components.

Validates that FIPS is in use in OpenSSL.

***

### molecule/plain-erp-tls-rhel

#### Scenario plain-erp-tls-rhel test's the following:

Installation of Confluent Platform on RHEL8.

SASL Plain enabled.

TLS enabled on ERP only.

#### Scenario plain-erp-tls-rhel verify test's the following:

Validates that SASL protocol is PLAIN on all components.

Validates that ERP is accessible over HTTPS.

Validates that Control Center is avaiable over HTTP.

Validates that Control Center has truststore in place.

***

### molecule/plaintext-basic-rhel

#### Scenario plaintext-basic-rhel test's the following:

Installation of Confluent Platform on RHEL9.

Kafka Rest API Basic Auth.

#### Scenario plaintext-basic-rhel verify test's the following:

Validates that each component has a unique auth user.

Validates that Rest Proxy has correct auth property.

Validates that Java 17 is in Use

***

### molecule/plaintext-rhel-customrepo

#### Scenario plaintext-rhel-customrepo test's the following:

Installation of Confluent Platform on RHEL8.

Copying local JMX agent.

Copying local files.

Custom yum Repository

#### Scenario plaintext-rhel-customrepo verify test's the following:

Validates Package version installed.

Validates log4j configuration.

Validates all components are running with plaintext.

Validates that copied files are present.

Validates that JMX exporter was copied and is running.

***

### molecule/provided-rhel

#### Scenario provided-rhel test's the following:

Installation of Confluent Platform on RHEL8.

TLS enabled.

Customer keystore alias.

#### Scenario provided-rhel verify test's the following:

Validates that keystores are in place across all components.

***

### molecule/rbac-kafka-connect-replicator-kerberos-mtls-custom-debian

#### Scenario rbac-kafka-connect-replicator-kerberos-mtls-custom-debian test's the following:

Installation of Confluent Platform on Debian10.

RBAC Enabled.

Customer RBAC system admins.

Kerberos enabled on Cluster1(mds).

MTLS Customer certs enabled on cluster2.

Replicator Configured with Kerberos and MTLS.

#### Scenario rbac-kafka-connect-replicator-kerberos-mtls-custom-debian verify test's the following:

Validates that the Console Consumer can consume data from cluster2, proving that data has been replicated from cluster1 (MDS).

Validates that Replicator is using MTLS with RBAC to Produce data to Cluster2.

Validates that Replicator is using Kerberos with RBAC to Consume from Cluster1 (MDS).

Validates that client ID's are set correctly on Replicator.

Validates that Replicator logging path is valid.

Validates client packages.

***

### molecule/rbac-kafka-connect-replicator-kerberos-mtls-custom-ubuntu

#### Scenario rbac-kafka-connect-replicator-kerberos-mtls-custom-ubuntu test's the following:

Installation of Confluent Platform on Ubuntu2404.

RBAC Enabled.

Customer RBAC system admins.

Kerberos enabled on Cluster1(mds).

MTLS Customer certs enabled on cluster2.

Replicator Configured with Kerberos and MTLS.

#### Scenario rbac-kafka-connect-replicator-kerberos-mtls-custom-ubuntu verify test's the following:

Validates that the Console Consumer can consume data from cluster2, proving that data has been replicated from cluster1 (MDS).

Validates that Replicator is using MTLS with RBAC to Produce data to Cluster2.

Validates that Replicator is using Kerberos with RBAC to Consume from Cluster1 (MDS).

Validates that client ID's are set correctly on Replicator.

Validates that Replicator logging path is valid.

Validates client packages.

***

### molecule/rbac-kerberos-debian12

#### Scenario rbac-kerberos-debian12 test's the following:

Installation of Confluent Platform on Debian 12.

RBAC enabled.

Kerberos enabled.

Provided kerberos client config (kerberos_configure:false) file with custom location

Kafka broker custom listener.

RBAC additional system admin user.

Java 8

#### Scenario rbac-kerberos-debian12 verify test's the following:

Validates that protocol set to GSSAPI.

Validates that a regular user cannot access topics.

Validates that a super user can access topics.

Validates that all components are pointing to the MDS for authorization.

***

### molecule/rbac-mds-kerberos-debian

#### Scenario rbac-mds-kerberos-debian test's the following:

Installs two Confluent Platform Clusters on Debian10.

RBAC enabled.

Remote MDS from Cluster2 to Cluster1 (MDS).

Custom TLS certificates.

Kafka Broker Customer Listener

RBAC Additional System Admin.

SSO authentication using OIDC in Control center using Azure IdP

#### Scenario rbac-mds-kerberos-debian verify test's the following:

Validates that GSSAPI protocol is set on Cluster2.

Validates that MDS is HTTP on Cluster1 (MDS).

Validates that all components on Cluster2 are pointing to the MDS on Cluster1.

Validates that Java 17 is in Use

Validates OIDC authenticate api for SSO in Control Center

***

### molecule/rbac-mds-kerberos-mtls-custom-rhel

#### Scenario rbac-mds-kerberos-mtls-custom-rhel test's the following:

Installs two Confluent Platform Clusters on RHEL8.

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

### molecule/rbac-mds-mtls-custom-kerberos-rhel

#### Scenario rbac-mds-mtls-custom-kerberos-rhel test's the following:

Installs two Confluent Platform Clusters on Alma Linux 9.

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

### molecule/rbac-mds-mtls-custom-rhel-fips

#### Scenario rbac-mds-mtls-custom-rhel-fips test's the following:

Installs two Confluent Platform Clusters on RHEL8.

RBAC enabled.

Remote MDS from Cluster2 to Cluster1 (MDS).

Custom TLS certificates.

MTLS enabled on both clusters.

FIPS enabled on both clusters.

Kafka Broker Customer Listener.

RBAC Additional System Admin.

#### Scenario rbac-mds-mtls-custom-rhel-fips verify test's the following:

Validates that Audit logs are working on topic creation.

Validates that keystores are in place.

Validates that MDS is HTTP on Cluster1 (MDS).

Validates that all components on Cluster2 are pointing to the MDS on Cluster1.

Validates that FIPS is in use on both clusters.

***

### molecule/rbac-mds-mtls-existing-keystore-truststore-ubuntu

#### Scenario rbac-mds-mtls-existing-keystore-truststore-ubuntu test's the following:

Installs Confluent Platform Cluster on Ubuntu2404.

RBAC enabled.

Provided user supplied keystore and truststore already present on the host

MTLS enabled.

Kafka Broker Customer Listener.

RBAC Additional System Admin.

Use Java 11 package

Creates a Connector in connect cluster

#### Scenario rbac-mds-mtls-existing-keystore-truststore-ubuntu verify test's the following:

Validates that keystores are present on all components.

Validates that LDAPS is working.

Validates that TLS CN is being registered as super user.

***

### molecule/rbac-mds-plain-custom-rhel-fips

#### Scenario rbac-mds-plain-custom-rhel-fips test's the following:

Installs two Confluent Platform Clusters on RHEL9.

RBAC enabled.

Remote MDS from Cluster2 to Cluster1 (MDS).

Custom TLS certificates.

SASL PLAIN enabled on both clusters.

Kafka Broker Customer Listener.

RBAC Additional System Admin.

SSO authentication using OIDC in Control center using KeyCloak IdP

FIPS enabled on both clusters.

#### Scenario rbac-mds-plain-custom-rhel-fips verify test's the following:

Validates that protocol is sasl plain.

Validates that MDS is HTTPs on Cluster1 (MDS).

Validates that all components on Cluster2 are pointing to the MDS on Cluster1.

Validates OIDC authenticate api for SSO in Control Center

Validates that FIPS is in use on both clusters.

***

### molecule/rbac-mtls-rhel-fips

#### Scenario rbac-mtls-rhel-fips test's the following:

Installs Confluent Platform Cluster on Oracle Linux 9.

RBAC enabled.

MTLS enabled.

Secrets protection enabled

FIPS enabled.

Kafka Broker Customer Listener.

RBAC Additional System Admin.

Provided SSL Principal Mapping rule

Creates two unique Connectors in Connect cluster.

Broker and Kraft Controller co-located while Migration

Kafka broker has custom listener at port 9093

Kraft Controller is running at port 9095

#### Scenario rbac-mtls-rhel-fips verify test's the following:

Validates TLS version across all components.

Validates super users are present.

Validates that secrets protection is masking the correct properties.

Validates Kafka Connect secrets registry.

Validates Cluster Registry.

Validates the filter resolve_principal with different ssl.mapping.rule

Validates that FIPS is in use in OpenSSL.

***

### molecule/rbac-mtls-rhel8

#### Scenario rbac-mtls-rhel8 test's the following:

Installs Confluent Platform Cluster on Oracle Linux 8.

RBAC enabled.

MTLS enabled.

Kafka Broker Customer Listener.

SSO authentication using OIDC in Control center using Okta IdP

#### Scenario rbac-mtls-rhel8 verify test's the following:

Validates TLS keysizes across all components.

Validates OIDC authenticate api for SSO in Control Center

***

### molecule/rbac-replicator-mtls-custom-ubuntu

#### Scenario rbac-replicator-mtls-custom-ubuntu test's the following:

Installation of Confluent Platform on Ubuntu2204.

RBAC Enabled.

Customer RBAC system admins.

Kerberos enabled on Cluster1(mds).

MTLS Customer certs enabled on cluster2.

Replicator Configured with Kerberos and MTLS.

#### Scenario rbac-replicator-mtls-custom-ubuntu verify test's the following:

Validates that the Console Consumer can consume data from cluster2, proving that data has been replicated from cluster1 (MDS).

Validates that Replicator is using MTLS with RBAC to Produce data to Cluster2.

Validates that Replicator is using Kerberos with RBAC to Consume from Cluster1 (MDS).

Validates that client ID's are set correctly on Replicator.

Validates that Replicator logging path is valid.

Validates client packages.

***

### molecule/rbac-scram-custom-rhel-fips

#### Scenario rbac-scram-custom-rhel-fips test's the following:

Installs Confluent Platform Cluster on RHEL8.

RBAC enabled.

SCRAM enabled.

TLS with custom certs enabled.

Additional System Admins added.

Additional Scram Users added.

Kafka Connect Custom arguments.

SSO authentication using OIDC in Control center using Azure IdP

FIPS enabled

Installs Two unique Kafka Connect Clusters with unique connectors.

#### Scenario rbac-scram-custom-rhel-fips verify test's the following:

Validates keystore is present across all components.

Validates that ldap is configured.

Validates that Confluent Balancer is enabled.

Validates total number of clusters for user2.

Validates truststore across all components.

Validates OIDC authenticate api for SSO in Control Center

Validates that FIPS is in use in OpenSSL.

Validates that both the Connectors are Running

***

### molecule/scram-rhel

#### Scenario scram-rhel test's the following:

Installs Confluent Platform Cluster on RHEL8.

SCRAM enabled.

#### Scenario scram-rhel verify test's the following:

Validates that SCRAM is enabled on all components except kafka controller.

***

