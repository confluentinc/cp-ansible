# SEC-03: Upgrade + Auto-Generated Key + FORCE REGENERATION (Divergence Bug Test)

## Purpose

This Molecule scenario validates that the **master key divergence bug is FIXED**, even with **force regeneration**.

**Configuration (dynamically set):**
- **Run 1:** `force_regenerate_masterkey: false` (idempotent - generate once)
- **Run 2:** `force_regenerate_masterkey: true` (force regenerate - the dangerous case!)

This is the **STRONGEST test** - it tests the transition from idempotent to force regeneration in serial mode, which is the most realistic and challenging scenario!

### The Bug

**Without the fix:**
- Run 1 (parallel, force_regenerate: false): All hosts get same master key "abc123" ✅
- Run 2 (serial, force_regenerate: true): Each host generates **DIFFERENT** master key ❌ **DIVERGENCE**
  - Host 1: "aaa111"
  - Host 2: "bbb222" (DIFFERENT!)
  - Host 3: "ccc333" (DIFFERENT!)

**Why it happens:**
- `run_once: true` at role level executes **once per batch** in serial mode
- Each host is a separate batch when `serial: 1`
- Each batch generates a NEW key with `force_regenerate_masterkey: true`

### The Fix

**With the fix (fact-based coordination):**
- Master key generation moved to **playbook level** (before parallel/serial split)
- `run_once: true` at playbook level = executes **ONCE total** across all hosts
- Fact `masterkey_generated_at_all_level` prevents component playbooks from regenerating
- Even with `force_regenerate_masterkey: true` on Run 2, all hosts get SAME new key

**Result:**
- Run 1 (force_regenerate: false): Generates master key "abc123" once ✅
- Run 2 (force_regenerate: true): Generates NEW key "xyz789" ✅
- **All hosts get SAME new key "xyz789"** ✅
- **NO DIVERGENCE** ✅

---

## Test Execution

### Run Test

```bash
cd molecule/secrets-upgrade-auto
molecule test
```

### Test Sequence

1. **First Converge**: Fresh install (force_regenerate: **false**)
   - Service not running → parallel deployment strategy
   - `force_regenerate_masterkey: false` (idempotent behavior)
   - Master key generated once: "abc123"
   - All 3 hosts get same key

2. **First Verify**: Validate single key created
   - Check all hosts have same key "abc123"
   - Check key file created on Ansible controller

3. **Second Converge**: Upgrade (force_regenerate: **true**) - **CRITICAL**
   - Service running → serial deployment strategy
   - `force_regenerate_masterkey: true` (dynamically set in converge.yml!)
   - Generates NEW key: "xyz789"
   - **WITHOUT FIX**: Would generate DIFFERENT new key per host (divergence)
   - **WITH FIX**: All hosts get SAME new key "xyz789" (fact coordination)

4. **Second Verify**: Validate NO divergence despite force regeneration
   - ✅ All hosts have same key (critical!)
   - ✅ Key IS different from Run 1 "abc123" → "xyz789" (expected with force_regenerate)
   - ✅ Passwords encrypted
   - ✅ Kafka running

---

## Expected Results

### ✅ Success (Fix Working)

```
✅ CRITICAL TEST PASSED: No divergence detected
✅ Key WAS regenerated (different from original) - EXPECTED with force_regenerate
✅ VALIDATION PASSED: Passwords encrypted
✅ VALIDATION PASSED: Kafka brokers running

THE MASTER KEY DIVERGENCE BUG IS FIXED!

Even with force_regenerate_masterkey: true, all hosts get the SAME key.
This proves fact-based coordination works!
```

### ❌ Failure (Bug Present)

```
❌ CRITICAL FAILURE - DIVERGENCE DETECTED

Master keys are DIFFERENT across hosts!
- kafka-broker-01: aaa111
- kafka-broker-02: bbb222
- kafka-broker-03: ccc333

This indicates the DIVERGENCE BUG is NOT FIXED!
```

---

## What This Tests

| Test | Description | Pass Criteria |
|------|-------------|---------------|
| **Divergence Detection** ⭐ | All hosts have same master key (CRITICAL) | `all_master_keys \| unique \| length == 1` |
| **Force Regeneration** | With `force_regenerate: true`, key changes | `current_key != original_key` (expected) |
| **Fact Coordination** ⭐ | Even with force regeneration, no divergence | All hosts get SAME new key |
| **Encryption** | Passwords encrypted in configs | `grep '${securepass:' \| wc -l > 0` |
| **Service Status** | Kafka running on all hosts | `systemctl is-active == "active"` |

⭐ = Critical tests for divergence fix
| **File Presence** | security.properties exists | File exists on all hosts |

---

## Debugging

### Check Master Keys Manually

```bash
# Login to each container
molecule login -s secrets-upgrade-auto -h kafka-broker1.confluent
systemctl cat confluent-kafka | grep CONFLUENT_SECURITY_MASTER_KEY

molecule login -s secrets-upgrade-auto -h kafka-broker2.confluent
systemctl cat confluent-kafka | grep CONFLUENT_SECURITY_MASTER_KEY

molecule login -s secrets-upgrade-auto -h kafka-broker3.confluent
systemctl cat confluent-kafka | grep CONFLUENT_SECURITY_MASTER_KEY

# Compare - should all be IDENTICAL
```

### Check Master Key File

```bash
# On Ansible controller (from molecule directory)
cat generated_ssl_files/masterkey
```

### View Kafka Logs

```bash
molecule login -s secrets-upgrade-auto -h kafka-broker1.confluent
journalctl -u confluent-kafka -n 100
```

---

## Files

- `molecule.yml` - Scenario configuration (3 Docker containers using CP Ansible standards)
- `converge.yml` - Deployment playbook (runs twice to simulate upgrade)
- `verify.yml` - Validation tests (critical divergence assertions)
- `README.md` - This file

## Standards Alignment

This scenario follows CP Ansible Molecule testing standards:
- Uses ubuntu1804 base image with Dockerfile template
- Hostnames use .confluent domain convention
- Network named "confluent"
- Standard provisioner configuration with hash_behaviour: merge

---

## Related Documentation

- Fix Proposal: `docs/master_key_divergence_fix_proposal.md`
- Scenario Validation: `docs/master_key_fix_scenario_validation.md`
- Testing Plan: `docs/master_key_divergence_testing_plan.md`
- Execution Flows: `docs/secrets_protection_execution_flows.md`
