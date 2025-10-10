# Primary Schema Registry Switchover: CP to Confluent Cloud

## Overview

The `primary_sr_switchover_cp_to_cc.yml` playbook automates the process of switching a Confluent Platform (CP) Schema Registry from being the primary registry to using Confluent Cloud (CC) Schema Registry as the primary. This enables seamless migration of schema management from on-premises to cloud.

## Prerequisites

- Confluent Platform Schema Registry deployed and running
- Confluent Cloud Schema Registry accessible
- Unified Stream Manager (USM) configured
- Valid API credentials for Confluent Cloud

## Customer Scenarios

### ✅ Successful Scenarios

| **Scenario** | **Conditions** | **Result** | **Notes** |
|--------------|----------------|------------|-----------|
| **Basic Automation Flow** | • USM enabled<br/>• Exporter state = RUNNING<br/>• `sr_switch_over_exporter_name` defined | Automation triggers and completes successfully | Importer is created automatically |
| **Exporter Already Present** | • USM enabled<br/>• Exporter = RUNNING<br/>• `sr_switch_over_exporter_name` defined | Automation succeeds | Uses existing exporter, creates importer |
| **New/Blank CP Deployment** | • USM enabled<br/>• No exporter configured<br/>• No existing schemas | Automation completes successfully | Importer is created, no export needed |

### ⏳ Delayed Scenarios

| **Scenario** | **Conditions** | **Result** | **Notes** |
|--------------|----------------|------------|-----------|
| **Exporter is PAUSED** | • USM enabled<br/>• Exporter = PAUSED<br/>• `sr_switch_over_exporter_name` provided | Automation waits for exporter to reach RUNNING state | Importer creation is delayed until exporter is active |

### ❌ Failed Scenarios

| **Scenario** | **Conditions** | **Result** | **Notes** |
|--------------|----------------|------------|-----------|
| **Missing Exporter Name** | • USM enabled<br/>• Exporter = RUNNING<br/>• No `sr_switch_over_exporter_name` provided | **Fails in pre-checks** | Importer is not created |
| **Exporter URL Mismatch** | • Exporter's destination URL ≠ USM remote endpoint | **Fails in pre-checks** | Configuration error - URLs must match |
| **Importer Config Mismatch** | • Importer's source URL ≠ USM remote endpoint | **Fails in pre-checks** | Configuration error - URLs must match |
| **USM Not Configured** | • Exporter = RUNNING<br/>• USM not configured (`endpoint: none`) | **Fails in pre-checks** | USM remote endpoint must be set |
| **CC SR Mode Switch Failure** | • Automation fails to set CC SR to READWRITE | **Rollback triggered** | CP SR restored to READWRITE mode |

## Configuration Examples

### Mirror all schemas
```yaml
# Unified Stream Manager Configuration
unified_stream_manager:
  schema_registry_endpoint: "https://psrc-xyz.us-east-1.aws.confluent.cloud"
  authentication_type: basic
  basic_username: "your-cc-api-key"
  basic_password: "your-cc-api-secret"

# Schema Exporter Configuration
schema_exporters:
  - name: "cp-to-cc-exporter"
    subjects: [":*:"]
    context_type: "NONE"   # Copies the source context as-is, without prepending anything. This is useful to make an exact copy of the source Schema Registry in the destination.

# Schema Importer Configuration (for reverse sync)
schema_importers:
  - name: "cc-to-cp-importer"
    subjects: [":*:"]

# Specify exporter for switchover
sr_switch_over_exporter_name: "cp-to-cc-exporter"

password_encorder_secret: <secret>
```

### Sync Schemas to a specific context

1. exports default context in CP to site1 context in CC ,imports all schemas in site1 context in CC to default context in CP

```yaml
# When using contexts
unified_stream_manager:
  schema_registry_endpoint: "https://psrc-xyz.us-east-1.aws.confluent.cloud"
  authentication_type: basic
  basic_username: "your-cc-api-key"
  basic_password: "your-cc-api-secret"
  remote_context: "site1"

schema_exporters:
  - name: "production-exporter"
    subjects: ["*"]
    context_type: "CUSTOM"  # Prepends the source context with a custom context name, specified in context below.
    context: "site1"

schema_importers:
  - name: "production-importer"
    subjects: [":.site1:*"]
    context: "."

sr_switch_over_exporter_name: "production-exporter"

password_encorder_secret: <secret>
```

2. exports corp context in CP to site1 context in CC ,imports all schemas in site1.corp context in CC to corp context in CP

```yaml
# When using contexts
unified_stream_manager:
  schema_registry_endpoint: "https://psrc-xyz.us-east-1.aws.confluent.cloud"
  authentication_type: basic
  basic_username: "your-cc-api-key"
  basic_password: "your-cc-api-secret"
  remote_context: "site1"

schema_exporters:
  - name: "production-exporter-2"
    subjects: [":.corp:*"]
    context_type: "CUSTOM"
    context: "site1"

schema_importers:
  - name: "production-importer-2"
    subjects: [":.site1.corp:*"]
    context: "site1"

sr_switch_over_exporter_name: "production-exporter-2"

password_encorder_secret: <secret>
```

### Greenfield setup - enable forwarding and importer

```yaml
# When using contexts
unified_stream_manager:
  schema_registry_endpoint: "https://psrc-xyz.us-east-1.aws.confluent.cloud"
  authentication_type: basic
  basic_username: "your-cc-api-key"
  basic_password: "your-cc-api-secret"

schema_importers:
  - name: "production-importer-2"
    subjects: [":*:"]    #set according to scenario 1 or scenario 2

password_encorder_secret: <secret>

## Usage

### Default Run (Schema Exporter Setup Only)
```bash
ansible-playbook playbooks/primary_sr_switchover_cp_to_cc.yml
```
→ Runs schema exporter setup only

### Individual Phases
```bash
# Schema exporter setup only
ansible-playbook playbooks/primary_sr_switchover_cp_to_cc.yml --tags schema_exporter (same as default run)

# Forward to CC (pre-checks + forward mode)
ansible-playbook playbooks/primary_sr_switchover_cp_to_cc.yml --tags forward_to_cc

# Schema importer setup (reverse sync)
ansible-playbook playbooks/primary_sr_switchover_cp_to_cc.yml --tags schema_importer
```

### Full Switchover (Complete Migration)
```bash
ansible-playbook playbooks/primary_sr_switchover_cp_to_cc.yml --tags switchover_to_cc
```
→ Runs exporter + switchover + reverse sync


### Execution Flow by Tag

| Command | Phases Executed | Purpose |
|---------|----------------|---------|
| Default (no tags) | Schema Exporter Only | Safe initial setup - exports schemas to CC |
| `--tags switchover_to_cc` | Pre-checks → Exporter → Switchover → Importer | Complete migration workflow |
| `--tags schema_exporter` | Schema Exporter Only | Manual exporter setup |
| `--tags forward_to_cc` | Pre-checks → Forward Mode | Switch CP SR to forward mode only |
| `--tags schema_importer` | Schema Importer Only | Setup reverse sync from CC to CP |

## Pre-check Validations

The playbook performs comprehensive pre-checks before making any changes:

1. **USM Configuration Validation**
   - Ensures USM remote endpoint is configured (not `none`)
   - Validates endpoint format and accessibility

2. **URL Consistency Checks**
   - Exporter destination URL must match USM remote endpoint
   - Importer source URL must match USM remote endpoint

3. **Context Validation**
   - When USM `remote_context` is defined: qualified subjects must match
   - When USM `remote_context` is undefined: only unqualified subjects allowed

4. **Component State Validation**
   - Exporter must be in RUNNING state for switchover
   - Required exporters must be defined when specified

## Error Handling and Rollback

### Pre-check Failures
- **No rollback performed** (no changes made yet)
- **Immediate failure** with clear error messages
- **Configuration guidance** provided in error messages

### Switchover Failures
- **Automatic rollback** triggered
- **CP SR restored** to READWRITE mode
- **Clear failure messaging** with rollback status

## Troubleshooting

### Common Issues

#### USM Not Configured Error
```
USM remote endpoint must be configured. Current value: 'none'. 
Please set unified_stream_manager.schema_registry_endpoint to a valid Confluent Cloud Schema Registry URL.
```
**Solution**: Configure `unified_stream_manager.schema_registry_endpoint` with your CC SR URL.

#### URL Mismatch Error
```
Pre-check failed: Exporter and USM remote endpoints must match
```
**Solution**: Ensure exporter `config.schema_registry_endpoint` matches `unified_stream_manager.schema_registry_endpoint`.

#### Missing Exporter Name Error
```
Pre-check failed: sr_switch_over_exporter_name must be defined
```
**Solution**: Set `sr_switch_over_exporter_name` to match one of your configured exporters.

### Best Practices

1. **Test in non-production first** - Validate configuration in development environment
2. **Backup schemas** - Export schema registry data before switchover
3. **Monitor exporter state** - Ensure exporters are RUNNING before switchover
4. **Verify connectivity** - Test CC SR accessibility from CP environment
5. **Plan maintenance window** - Switchover involves brief write downtime

## Tags Reference

| Tag | Purpose | What Gets Executed | Safety Level |
|-----|---------|-------------------|--------------|
| **Default (no tags)** | Safe initial setup | Schema Exporter Only | ✅ **Safe** - No CP changes |
| `schema_exporter` | Manual exporter setup | Schema Exporter Only | ✅ **Safe** - No CP changes |
| `forward_to_cc` | Forward mode only | Pre-checks → CP SR → FORWARD mode | ⚠️ **Caution** - CP write downtime |
| `switchover_to_cc` | Complete migration | Pre-checks → Exporter → Switchover → Importer | ⚠️ **Caution** - Full migration |
| `schema_importer` | Reverse sync setup | Schema Importer Only | ✅ **Safe** - Adds reverse sync |

## Support

For issues or questions:
1. Check pre-check error messages for configuration guidance
2. Review this README for scenario-specific troubleshooting
3. Validate your configuration against the examples provided
4. Ensure all prerequisites are met before execution