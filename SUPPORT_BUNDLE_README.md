# Support Bundle Collection Playbook

## Overview

The support bundle collection playbook (`playbooks/support_bundle.yml`) provides comprehensive diagnostic data collection from Confluent Platform deployments. This tool is designed for troubleshooting customer issues by gathering all necessary information for support teams in a single, organized archive.

## What's Collected

### Configuration Files
- Main component configs (server.properties, schema-registry.properties, etc.)
- JAAS configuration files
- Log4j configuration files
- Systemd service files and overrides
- Client configuration files (where applicable)
- **Security**: All configs are automatically sanitized by default (passwords/secrets redacted)

### Log Files
- All component log files from the configured log directory

### SSL/TLS Metadata
- Certificate expiry dates, subjects, and issuers
- Keystore and truststore file permissions
- **Security**: Only metadata collected, never actual keystore/key files

### System Information
- OS information (uname, /etc/os-release)
- Java version and JAVA_HOME
- Memory information (free, /proc/meminfo)
- Disk information (df, lsblk)
- Network configuration (ip addr, routes)
- Hostname and DNS configuration
- Environment variables (filtered for JAVA/KAFKA/CONFLUENT, secrets excluded)
- Ansible facts

### Runtime Diagnostics
- Service status (systemctl status)
- Journalctl logs (configurable number of lines)
- Process information (ps, pgrep)
- Listening ports (ss or netstat)
- Open files (lsof)
- Ulimit settings (for service user)
- Kernel parameters (sysctl)

### Ansible Context
- Ansible version
- Python version
- Inventory structure (sanitized)
- Execution context (groups, host counts)

## Security Features

### Three-Tier Security Approach

#### Tier 1: Never Collected
These files are **NEVER** copied to the bundle:
- Private keys (`*.key`, PEM private keys)
- Keystore/truststore files (`*.jks`, `*.p12`, `*.pfx`, `*.bcfks`)
- Password files (`password.properties`)

#### Tier 2: Collected But Sanitized (Default)
Configuration files are collected but automatically sanitized:
- `.properties` files: passwords, secrets, keys, tokens redacted
- JAAS files: password fields redacted
- Systemd override files: sensitive environment variables redacted

Sanitized patterns include:
- `password`, `secret`, `key`, `token`, `credential`
- `keystore.password`, `truststore.password`, `ssl.key.password`
- `sasl.jaas.config`, `ldap.*password`
- `CONFLUENT_SECURITY_MASTER_KEY`

#### Tier 3: Metadata Only
SSL certificates collected as metadata only:
- Certificate expiry dates, subjects, issuers
- File permissions and sizes
- Never the actual certificate files

### Configuration Options

**Default (Recommended - Balanced Security)**:
```yaml
support_bundle_sanitize_configs: true
support_bundle_skip_configs: false
```
Collects configs with automatic sanitization.

**Most Secure (High-Security Environments)**:
```yaml
support_bundle_skip_configs: true
```
Only collects metadata about config files, no content.

**Least Secure (Not Recommended)**:
```yaml
support_bundle_sanitize_configs: false
```
Collects raw configs - **ONLY use in isolated/non-production environments**.

### Sanitization Report

Every bundle includes `configs/SANITIZATION_REPORT.txt` showing:
- Number of files sanitized
- Patterns that were redacted
- Warning to review before sharing

## Usage

### Basic Usage

```bash
# Collect support bundle from all components
ansible-playbook -i inventory.yml playbooks/support_bundle.yml
```

### Specific Component Only

```bash
# Collect only from Kafka brokers
ansible-playbook -i inventory.yml playbooks/support_bundle.yml --tags kafka_broker

# Collect only from ZooKeeper and Kafka
ansible-playbook -i inventory.yml playbooks/support_bundle.yml --tags zookeeper,kafka_broker
```

### Custom Configuration

```bash
# Custom cluster name and output path
ansible-playbook -i inventory.yml playbooks/support_bundle.yml \
  -e support_bundle_cluster_name=production_kafka \
  -e support_bundle_output_path=/var/support_bundles

# Collect more journalctl lines
ansible-playbook -i inventory.yml playbooks/support_bundle.yml \
  -e support_bundle_journalctl_lines=5000

# Skip config collection (most restrictive)
ansible-playbook -i inventory.yml playbooks/support_bundle.yml \
  -e support_bundle_skip_configs=true
```

## Configuration Variables

Add to your inventory or `host_vars`/`group_vars`:

```yaml
### Support Bundle Collection Settings

# Output path for support bundles (on Ansible controller)
support_bundle_output_path: "{{ playbook_dir }}"

# Cluster name to include in bundle filename
support_bundle_cluster_name: cp_cluster

# Number of journalctl log lines to collect per service
support_bundle_journalctl_lines: 1000

# Base path on remote hosts for temporary bundle staging
support_bundle_base_path: /tmp

# Whether to sanitize config files before collection (STRONGLY RECOMMENDED)
support_bundle_sanitize_configs: true

# Whether to skip config file collection entirely (most restrictive)
support_bundle_skip_configs: false
```

## Output Structure

```
support_bundle_<timestamp>_<cluster_name>.tar.gz
├── ansible/
│   ├── inventory_sanitized.yml
│   ├── ansible_version.txt
│   └── execution_context.yml
├── bundle_manifest.yml
└── <hostname>/
    ├── configs/
    │   ├── <component>.properties (sanitized)
    │   ├── <component>_jaas.conf (sanitized)
    │   ├── log4j.properties
    │   ├── <service>.service
    │   ├── override.conf (sanitized)
    │   └── SANITIZATION_REPORT.txt
    ├── logs/
    │   └── <component log files>
    ├── ssl/
    │   ├── certificates_info.txt
    │   └── file_permissions.txt
    ├── system/
    │   ├── os_info.txt
    │   ├── java_version.txt
    │   ├── memory.txt
    │   ├── disk.txt
    │   ├── network.txt
    │   ├── hostname.txt
    │   ├── environment.txt
    │   └── ansible_facts.txt
    ├── diagnostics/
    │   ├── service_status.txt
    │   ├── journalctl.log
    │   ├── processes.txt
    │   ├── ports.txt
    │   ├── open_files.txt
    │   ├── ulimit.txt
    │   └── sysctl.txt
    └── host_manifest.yml
```

## Pre-Upload Security Verification

**ALWAYS** run these checks before uploading to support:

```bash
# Extract the bundle
tar -xzf support_bundle_*.tar.gz
cd support_bundle_*/

# 1. Verify no keystore/key files (should be empty)
find . -name "*.jks" -o -name "*.p12" -o -name "*.key" -o -name "*.pfx"

# 2. Check for password patterns (should only be in metadata or SANITIZATION_REPORT)
grep -r "password=" . | grep -v -E "REDACTED|SANITIZATION_REPORT|metadata"

# 3. Verify sanitization report exists
find . -name "SANITIZATION_REPORT.txt"
cat */configs/SANITIZATION_REPORT.txt

# 4. Check sanitization headers in config files
head -1 */configs/*.properties
head -1 */configs/*jaas.conf

# 5. Check for accidental password.properties inclusion (should be empty)
find . -name "*password.properties"
```

## Available Tags

- `zookeeper` - ZooKeeper hosts only
- `kafka_controller` - Kafka Controller hosts only
- `kafka_broker` - Kafka Broker hosts only
- `schema_registry` - Schema Registry hosts only
- `kafka_connect` - Kafka Connect hosts only
- `kafka_connect_replicator` - Kafka Connect Replicator hosts only
- `ksql` - KSQL hosts only
- `kafka_rest` - Kafka REST Proxy hosts only
- `control_center` - Control Center hosts only
- `control_center_next_gen` - Control Center Next Gen hosts only

## Implementation Files

### Playbook
- `playbooks/support_bundle.yml` - Main playbook entry point

### Task Files
- `roles/common/tasks/collect_support_bundle.yml` - Core collection orchestrator
- `roles/common/tasks/collect_system_info.yml` - System information collection
- `roles/common/tasks/collect_diagnostics.yml` - Runtime diagnostics collection
- `roles/common/tasks/collect_ssl_metadata.yml` - SSL certificate metadata extraction
- `roles/common/tasks/sanitize_config_files.yml` - Config file sanitization

### Templates
- `roles/common/templates/host_manifest.yml.j2` - Per-host manifest
- `roles/common/templates/bundle_manifest.yml.j2` - Overall bundle manifest

### Variables
- `roles/variables/defaults/main.yml` - Default configuration variables

## Error Handling

The playbook uses `ignore_errors: true` on most collection tasks to ensure:
- Partial bundles are still created if some data is unavailable
- Collection continues even if services are stopped
- Permission issues on individual files don't fail the entire collection

## Troubleshooting

### Bundle Not Created
- Check Ansible controller has write permissions to `support_bundle_output_path`
- Ensure sufficient disk space on both controller and remote hosts
- Check `/tmp` space on remote hosts (used for staging)

### Missing Data in Bundle
- Some data may be unavailable if services are stopped (expected)
- Permission issues may prevent collection of certain files (check logs)
- SSL metadata only collected if `ssl_enabled: true` in variables

### Large Bundle Size
- Reduce `support_bundle_journalctl_lines` to collect fewer log lines
- Use tags to collect only specific components
- Consider setting `support_bundle_skip_configs: true` to exclude configs

## Best Practices

1. **Run on stable systems**: Avoid running during active deployments or upgrades
2. **Review before sharing**: Always verify sanitization before uploading to support
3. **Use descriptive cluster names**: Helps identify bundles when managing multiple clusters
4. **Test on non-production first**: Verify the playbook works in your environment
5. **Store bundles securely**: Bundles contain diagnostic data about your infrastructure

## Support

For issues or questions about the support bundle playbook:
1. Check the troubleshooting section above
2. Review the sanitization report in the bundle
3. Contact Confluent Support with specific error messages
