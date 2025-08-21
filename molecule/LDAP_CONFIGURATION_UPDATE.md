# LDAP Configuration Update for SR Automation

## ✅ Updated LDAP Configuration to Follow Standard Molecule Patterns

The SR automation LDAP scenario has been updated to align with the established patterns used in other molecule scenarios in the codebase.

## 🔄 Changes Made

### 1. **Base Template Updates**
- **File**: `molecule/base_templates/sr_automation_prepare_base.yml`
- **Changes**:
  - Added proper naming for LDAP server provisioning step
  - Added IPv6 configuration import
  - Added DNS setup import
  - Now follows the same pattern as `rbac-mds-kerberos-debian/prepare.yml`

```yaml
- name: Configure IPv6 Preference
  import_playbook: ../configure_ipv6.yml

- name: Setup VM DNS
  import_playbook: ../dns.yml

- name: Provision LDAP Server
  import_playbook: ../ldap.yml
  when: ldap_enabled | default(false)
```

### 2. **LDAP Scenario Configuration**
- **File**: `molecule/sr-automation-ldap-mtls/molecule.yml`
- **Changes**:
  - Updated LDAP server configuration to use standard pattern
  - Added proper LDAP user provisioning
  - Updated LDAP connection parameters to match other scenarios
  - Added group configuration for `ldap_server`

**Before**: Manual LDAP setup with basic configuration
**After**: Standard LDAP provisioning using `confluent.test.ldap` role

### 3. **LDAP Server Configuration**
```yaml
ldap_server:
  ldaps_enabled: true
  ldaps_custom_certs: true
  ssl_custom_certs: true
  ldap_admin_password: "admin-password"
  ldap_rbac_group: "rbac"
  ldap_dc: "confluent"
  ldap_dc_extension: "local"
  
  # SR automation specific LDAP users
  ldap_users:
    - username: "sr-admin"
      password: "admin-password" 
      uid: 9998
      guid: 98
    - username: "sr-user"
      password: "user-password"
      uid: 9997
      guid: 97
    - username: "sr-exporter"
      password: "exporter-password"
      uid: 9996
      guid: 96
    - username: "sr-importer"
      password: "importer-password"
      uid: 9995
      guid: 95
    - username: "mds-user"
      password: "mds-password"
      uid: 9994
      guid: 94
```

### 4. **Schema Registry LDAP Properties**
Updated to use standard LDAP authentication pattern:

```yaml
schema_registry_custom_properties:
  # LDAP authentication - using standard pattern
  authentication.method: LDAP
  ldap.java.naming.factory.initial: "com.sun.jndi.ldap.LdapCtxFactory"
  ldap.com.sun.jndi.ldap.read.timeout: "3000"
  ldap.java.naming.provider.url: "{{ ldap_url }}"
  ldap.java.naming.security.protocol: "SSL"
  ldap.ssl.truststore.location: "/var/ssl/private/schema_registry.truststore.jks"
  ldap.ssl.truststore.password: "confluenttruststorepass"
  ldap.user.search.base: "{{ ldap_search_base }}"
  ldap.group.search.base: "{{ ldap_search_base }}"
  ldap.user.name.attribute: "uid"
  ldap.user.object.class: "account"
```

### 5. **Preparation Playbook Cleanup**
- **File**: `molecule/sr-automation-ldap-mtls/prepare.yml`
- **Changes**:
  - Removed manual LDAP user creation
  - Now relies on proper LDAP provisioning from `confluent.test.ldap` role
  - Added information about provisioned users
  - Improved status reporting

### 6. **Verification Enhancements**
- **File**: `molecule/sr-automation-ldap-mtls/verify.yml`
- **Changes**:
  - Added LDAP user authentication test
  - Updated summary to reflect standard LDAP user provisioning
  - Added verification for provisioned LDAP users

## 🎯 Benefits of the Update

### ✅ **Consistency**
- Now follows the same pattern as other molecule scenarios (`rbac-mds-kerberos-debian`, `oauth-rbac-mtls-provided-ubuntu`, etc.)
- Uses the established `confluent.test.ldap` role for LDAP provisioning

### ✅ **Reliability**
- Leverages tested LDAP setup code instead of custom implementation
- Proper LDAP server configuration with SSL/TLS support
- Standard certificate handling

### ✅ **Maintainability**
- Uses shared infrastructure code
- Consistent LDAP configuration across all scenarios
- Easier to troubleshoot and update

### ✅ **Functionality**
- Proper LDAP user provisioning with UIDs and GUIDs
- Standard LDAP authentication properties
- SSL/TLS enabled LDAP connections
- Integration with RBAC and mTLS

## 🔧 LDAP Users Created

The standard LDAP provisioning now creates these SR automation-specific users:

| Username | Purpose | UID | Password |
|----------|---------|-----|----------|
| `sr-admin` | Schema Registry admin | 9998 | `admin-password` |
| `sr-user` | Schema Registry user | 9997 | `user-password` |
| `sr-exporter` | Schema exporter service | 9996 | `exporter-password` |
| `sr-importer` | Schema importer service | 9995 | `importer-password` |
| `mds-user` | MDS service user | 9994 | `mds-password` |

## 🚀 Usage

The LDAP scenario now works exactly like other molecule LDAP scenarios:

```bash
# Test LDAP + mTLS SR automation
molecule test -s sr-automation-ldap-mtls

# The LDAP server will be properly provisioned with:
# - OpenLDAP server with SSL/TLS
# - All required test users
# - Proper DN structure: OU=rbac,DC=confluent,DC=local
# - SSL certificates for secure LDAP connections
```

## 📋 Integration Points

### With Existing Codebase
- ✅ Uses `molecule/ldap.yml` playbook
- ✅ Uses `confluent.test.ldap` role  
- ✅ Follows same certificate patterns
- ✅ Consistent with other scenarios

### With SR Automation Workflow
- ✅ LDAP users ready for automation testing
- ✅ Service users for exporters/importers
- ✅ RBAC integration with MDS
- ✅ mTLS certificate authentication

---

**Status**: ✅ **COMPLETE** - LDAP configuration now follows standard molecule patterns and is fully integrated with the existing LDAP infrastructure code.