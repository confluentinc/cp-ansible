# Schema Registry Automation Workflow Testing with Molecule

This document describes the molecule test scenarios for Schema Registry (SR) automation workflow testing across different security configurations.

## Overview

The SR automation testing framework provides comprehensive testing for:
- **Schema Exporters** - Export schemas from CP SR to CC SR
- **Schema Importers** - Import schemas from CC SR to CP SR (reverse sync)
- **Switchover Workflow** - Complete automation workflow from CP to CC
- **Security Integration** - Testing across different authentication/authorization modes

## Available Test Scenarios

### 1. `sr-automation-plaintext/` - No Authentication
**Use Case**: Basic functionality testing, development environments
- **Security**: No SSL/TLS, no authentication
- **Communication**: HTTP plaintext
- **Best For**: Core automation logic testing, CI/CD pipelines

```bash
molecule test -s sr-automation-plaintext
```

### 2. `sr-automation-mtls/` - Mutual TLS Authentication
**Use Case**: Certificate-based security, production-like testing
- **Security**: SSL/TLS with mutual authentication
- **Communication**: HTTPS with client certificates
- **Best For**: Certificate management testing, secure environments

```bash
molecule test -s sr-automation-mtls
```

### 3. `sr-automation-oauth-rbac/` - OAuth + RBAC Authorization
**Use Case**: Modern enterprise authentication, cloud-native environments
- **Security**: OAuth 2.0 + Role-Based Access Control
- **Communication**: HTTPS with OAuth tokens
- **Best For**: Token-based auth testing, enterprise integration

```bash
molecule test -s sr-automation-oauth-rbac
```

### 4. `sr-automation-ldap-mtls/` - LDAP/RBAC + mTLS
**Use Case**: Enterprise directory integration with certificate security
- **Security**: LDAP authentication + RBAC + mutual TLS
- **Communication**: HTTPS with client certs + LDAP directory
- **Best For**: Enterprise directory testing, maximum security scenarios

```bash
molecule test -s sr-automation-ldap-mtls
```

## Test Architecture

Each scenario includes:
- **Primary Schema Registry** (`schema-registry1`) - Simulates CP SR with various auth methods
- **Mock CC Schema Registry** (`mock-cc-schema-registry`) - Simulates Confluent Cloud SR target (always uses basic auth)
- **Kafka Cluster** - Controller + 2 brokers
- **Security Services** - LDAP/OAuth servers as needed

### Authentication Architecture
- **CP Schema Registry**: Uses the scenario-specific authentication (plaintext, mTLS, OAuth, LDAP)
- **Mock CC Schema Registry**: Always uses basic authentication (API key/secret) - matching real Confluent Cloud behavior
- **Exporters/Importers**: Use basic auth when connecting to mock CC SR, regardless of CP SR auth method

## Common Test Components

### Base Templates
- `sr_automation_prepare_base.yml` - Common environment setup
- `sr_automation_converge_base.yml` - Shared automation workflow testing
- `sr_automation_verify_base.yml` - Common validation checks

### Test Phases
1. **Prepare** - Environment setup, certificates, test data
2. **Converge** - Deploy SR automation configuration and test schemas
3. **Verify** - Validate automation features and security compliance

## Test Configuration

### Key Variables per Scenario

| Variable | Plaintext | mTLS | OAuth+RBAC | LDAP+mTLS |
|----------|-----------|------|------------|-----------|
| **CP SR Auth** | **None** | **mTLS** | **OAuth** | **LDAP+mTLS** |
| **Mock CC SR Auth** | **Basic** | **Basic** | **Basic** | **Basic** |
| `ssl_enabled` | `false` | `true` | `true` | `true` |
| `ssl_mutual_auth_enabled` | `false` | `true` | `false` | `true` |
| `oauth_enabled` | `false` | `false` | `true` | `false` |
| `ldap_enabled` | `false` | `false` | `false` | `true` |
| `rbac_enabled` | `false` | `false` | `true` | `true` |

**Note**: Mock CC SR always uses basic authentication (API key/secret) to simulate real Confluent Cloud behavior.

### Schema Registry Endpoints
- **Primary (CP SR)**: `https://schema-registry1:8081`
- **Mock CC SR**: `https://mock-cc-schema-registry:8081` (or `http://` for plaintext)

### Test Automation Components

#### Schema Exporters
Each scenario creates a test exporter:
- **Name**: `{scenario}-schema-exporter`
- **Subjects**: `["test.*", "automation.*"]`
- **Target**: Mock CC SR endpoint

#### Schema Importers  
Each scenario creates a test importer:
- **Name**: `{scenario}-schema-importer`
- **Subjects**: `["*"]` (all subjects)
- **Source**: Mock CC SR endpoint

#### Test Schemas
- `test.user-value` - User record schema
- `automation.workflow-value` - Automation workflow schema

## Usage Examples

### Run Full Test Suite
```bash
# Test all scenarios
for scenario in plaintext mtls oauth-rbac ldap-mtls; do
  molecule test -s sr-automation-$scenario
done
```

### Test Specific Components
```bash
# Test only schema exporter setup
molecule converge -s sr-automation-plaintext
molecule verify -s sr-automation-plaintext

# Test complete switchover workflow (when ready)
ANSIBLE_TAGS=switchover_to_cc molecule test -s sr-automation-mtls
```

### Debug Mode
```bash
# Run with detailed logging
MOLECULE_DEBUG=1 molecule test -s sr-automation-oauth-rbac
```

### Cleanup
```bash
# Destroy test environment
molecule destroy -s sr-automation-ldap-mtls
```

## Validation Checks

### Common Validations (All Scenarios)
- ✅ Schema Registry automation properties configured
- ✅ Password encoder secret set
- ✅ USM endpoint configured
- ✅ Schema exporter/importer APIs accessible
- ✅ Test schemas created successfully

### Security-Specific Validations

#### mTLS Scenarios
- ✅ Client certificates present
- ✅ mTLS authentication enforced
- ✅ Certificate-based API access

#### OAuth Scenarios  
- ✅ OAuth configuration properties
- ✅ Token endpoint accessibility
- ✅ Bearer token authentication

#### LDAP Scenarios
- ✅ LDAP server connectivity
- ✅ Directory authentication configuration
- ✅ User/group mappings

#### RBAC Scenarios
- ✅ RBAC authorizer configured
- ✅ MDS integration settings
- ✅ Role-based access controls

## Integration with SR Switchover Workflow

These molecule tests integrate with the main SR automation playbook:
- **Playbook**: `playbooks/primary_sr_switchover_cp_to_cc.yml`
- **Inventory**: Based on `docs/sample_inventories/sr_switchover_cp_to_cc.yml`
- **Tags**: `schema_exporter`, `forward_to_cc`, `schema_importer`, `switchover_to_cc`

### Test Tags Usage
```bash
# Test only exporter functionality
ansible-playbook playbooks/primary_sr_switchover_cp_to_cc.yml --tags schema_exporter

# Test complete switchover workflow
ansible-playbook playbooks/primary_sr_switchover_cp_to_cc.yml --tags switchover_to_cc
```

## Troubleshooting

### Common Issues
1. **Certificate Problems** (mTLS scenarios)
   - Check `ssl_file_dir_final` path
   - Verify certificate generation in prepare phase

2. **OAuth Token Issues** (OAuth scenarios)
   - Check OAuth server accessibility
   - Verify client credentials configuration

3. **LDAP Connection Issues** (LDAP scenarios)  
   - Check LDAP server connectivity
   - Verify LDAP URL and credentials

4. **Port Conflicts**
   - Ensure Docker ports are available
   - Check for conflicting services

### Debug Commands
```bash
# Check molecule status
molecule list

# View container logs
molecule login -s sr-automation-mtls -h schema-registry1

# Check service status
molecule exec -s sr-automation-plaintext -- systemctl status confluent-schema-registry
```

## CI/CD Integration

These molecule scenarios are designed for CI/CD integration:

```yaml
# Example GitHub Actions
- name: Test SR Automation - Plaintext
  run: molecule test -s sr-automation-plaintext

- name: Test SR Automation - mTLS  
  run: molecule test -s sr-automation-mtls
  
- name: Test SR Automation - OAuth RBAC
  run: molecule test -s sr-automation-oauth-rbac
  
- name: Test SR Automation - LDAP mTLS
  run: molecule test -s sr-automation-ldap-mtls
```

## Contributing

When adding new security configurations:
1. Create new scenario directory: `molecule/sr-automation-{config}/`
2. Add scenario-specific `molecule.yml`, `prepare.yml`, `converge.yml`, `verify.yml`
3. Import base templates for common functionality
4. Update this documentation

---

**Next Steps**: These molecule scenarios provide comprehensive testing for SR automation workflows across different security configurations, enabling confident deployment and validation of schema registry automation features.