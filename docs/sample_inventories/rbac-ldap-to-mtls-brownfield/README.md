# RBAC on LDAP to RBAC on mTLS Migration with SSO Integration

This directory contains sample inventory files demonstrating the step-by-step migration process from LDAP to mTLS (mutual TLS) authentication with SSO integration for Confluent Platform.

## Overview

The migration process consists of four main steps:

1. Initial LDAP Setup
2. Enable mTLS
3. Client Migration
4. Enforce mTLS
5. SSO Integration

## Prerequisites

- Confluent Platform cluster with RBAC enabled
- LDAP server configured and accessible
- SSL certificates for all components and their clients
- SSO provider (for step 4)

## Migration Steps

### Step 0: LDAP Setup
File: `step0_ldap_setup.yml`

This step sets up the initial Confluent Platform cluster with:
- RBAC enabled over LDAP
- Service accounts for CP components
- LDAP configuration for authentication
- Basic security settings

### Step 1: Enable mTLS
File: `step1_enable_mtls.yml`

This step enables mTLS in "requested" mode:
- Configures mTLS for MDS
- Sets up Kafka listeners with mTLS
- Configures CP components to use mTLS
- Configures CP components to MDS and Kafka communication over mTLS
- Can still talk to Kafka/CP components without mTLS using LDAP

### Step 2: Client Migration
File: `step2_client_migration.yml`

This step prepares for client migration:
- Ensures all clients have valid certificates
- Sets up role bindings for certificate principals

### Step 3: Enforce mTLS
File: `step3_required.yml`

This step enforces mTLS authentication:
- Changes mTLS mode from "requested" to "required"
- Updates all components to require mTLS

### Step 4: SSO Integration
File: `step4_ldap_to_sso.yml`

This step migrates Control Center from LDAP to SSO:
- Configures SSO provider settings
- Sets up OIDC authentication
- Removes LDAP dependency for Control Center

## Important Notes

1. Each step should be executed in sequence
2. Step3, Step4 can be executed together
3. Do all the upgrades in rolling fashion to avoid downtime.
4. Validate the cluster health after each step
5. Ensure all clients are ready before enforcing mTLS
6. All client certs should be given proper role bindings before disable other mechanism of authnz
7. Keep backup of configurations before each step
8. Test in non-production environment first

## Troubleshooting

Common issues and solutions:
1. Certificate or Keystores not present in clients thus causing issue when mTLS is in required mode on server.
2. Certificate principals may not have same RBAC roles as the LDAP principal thus causing Authorization issue.
3. Impersonation super users not defined thus throwing errors stating can't impersonate using xyz principal.


## Additional Resources

- [mTLS Configuration Guide in CP-Ansible](https://docs.confluent.io/ansible/current/ansible-authorize.html#role-based-access-control-using-mtls)
- [mTLS Guide in CP](https://docs.confluent.io/platform/8.0/security/authorization/rbac/mtls-rbac.html)
