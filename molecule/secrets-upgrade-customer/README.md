# SEC-04: Upgrade + Customer-Provided Key

## Purpose

This Molecule scenario validates that **customer-provided master keys are preserved during upgrades** with serial deployment strategy.

### What It Tests

This scenario ensures customer keys survive upgrades:
- First run: Customer's key used (parallel deployment)
- Second run: SAME customer key preserved (serial deployment)
- No divergence occurs
- No accidental regeneration

### Critical Validation

This test protects against a serious bug where:
- Role-level fact clearing could overwrite customer's key
- Upgrade deployments could ignore customer's key
- Serial deployment could cause divergence even with customer keys

---

## Test Execution

### Run Test

```bash
cd molecule/secrets-upgrade-customer
molecule test
```

### Test Sequence

1. **First Converge**: Fresh install (parallel deployment)
   - Service not running → parallel deployment strategy
   - Customer key used (no generation)
   - All 3 hosts get customer's key

2. **First Verify**: Validate customer key used
   - Check all hosts have customer's key

3. **Second Converge**: Upgrade (serial deployment) - **CRITICAL**
   - Service running → serial deployment strategy
   - **CRITICAL**: Customer key must NOT be cleared
   - **CRITICAL**: Customer key must be preserved

4. **Second Verify**: Validate NO divergence, customer key preserved
   - ✅ All hosts still have same key
   - ✅ Key is still customer's key (not regenerated)
   - ✅ Passwords encrypted
   - ✅ Kafka running

---

## Expected Results

### ✅ Success (Customer Key Preserved)

```
✅ CRITICAL TEST PASSED: No divergence detected
✅ CRITICAL TEST PASSED: Customer key preserved
✅ VALIDATION PASSED: Passwords encrypted
✅ VALIDATION PASSED: Kafka brokers running

CUSTOMER KEYS PRESERVED THROUGH UPGRADES!
```

### ❌ Failure (Customer Key Lost)

```
❌ FAILURE - Customer Key NOT Preserved

Expected (customer): Y3VzdG9tZXIta2V5LXVwZ3JhZGUtYWJjMTIz...
Found:               <different-key>...

This indicates the customer's key was overwritten or ignored!
```

---

## What This Tests

| Test | Description | Pass Criteria |
|------|-------------|---------------|
| **No Divergence** | All hosts have same key | `unique keys == 1` |
| **Customer Key** | Key is customer's (preserved) | `host_key == customer_key` |
| **Encryption** | Passwords encrypted | `grep '${securepass:' | wc -l > 0` |
| **Service** | Kafka running | `systemctl is-active == "active"` |
| **Files** | Security files exist | Files present on all hosts |

---

## Configuration

```yaml
secrets_protection_enabled: true
regenerate_masterkey: false  # Customer key
secrets_protection_masterkey: "Y3VzdG9tZXIta2V5LXVwZ3JhZGUtYWJjMTIz"  # Customer's key
```

This configuration triggers (across BOTH runs):
1. Playbook-level master key generation **SKIPPED** (customer key exists)
2. Role-level fact clearing **SKIPPED** (customer key exists)
3. All hosts use customer's key
4. Passwords encrypted with customer's key

---

## What Happens During the Test

### First Converge (Fresh Install)

```
1. Service check → NOT running
2. Deployment strategy → PARALLEL
3. Playbook-level generation:
   - Condition: not secrets_protection_masterkey → FALSE
   - Result: SKIP generation (customer provided key) ✅
4. All 3 hosts:
   - Role checks if should clear key → NO (customer key exists)
   - Uses customer's key: "Y3VzdG9tZXIta2V5LXVwZ3JhZGUtYWJjMTIz"
5. Result: All hosts use customer's key ✅
```

### Second Converge (Upgrade - CRITICAL TEST)

```
1. Service check → RUNNING
2. Deployment strategy → SERIAL (rolling)
3. Playbook-level generation:
   - Condition: not secrets_protection_masterkey → FALSE
   - Result: SKIP generation (customer key exists) ✅
4. Each host (serial):
   - Role checks if should clear key → NO (customer key exists)
   - Uses customer's key: "Y3VzdG9tZXIta2V5LXVwZ3JhZGUtYWJjMTIz"
5. Result: All hosts still use customer's key ✅ NO DIVERGENCE
```

**Without the fix:**
```
3. Playbook-level generation → SKIPPED (customer key)
4. Each host (serial):
   - Role CLEARS customer key (bug!)
   - Role generates NEW key per host (divergence!)
   - Host 1: "aaa111"
   - Host 2: "bbb222" (DIFFERENT!)
   - Host 3: "ccc333" (DIFFERENT!)
5. Result: CUSTOMER KEY LOST + DIVERGENCE ❌
```

---

## Debugging

### Check Master Keys

```bash
molecule login -s secrets-upgrade-customer -h kafka-broker1.confluent
systemctl cat confluent-kafka | grep CONFLUENT_SECURITY_MASTER_KEY

molecule login -s secrets-upgrade-customer -h kafka-broker2.confluent
systemctl cat confluent-kafka | grep CONFLUENT_SECURITY_MASTER_KEY

molecule login -s secrets-upgrade-customer -h kafka-broker3.confluent
systemctl cat confluent-kafka | grep CONFLUENT_SECURITY_MASTER_KEY

# All should be IDENTICAL: Y3VzdG9tZXIta2V5LXVwZ3JhZGUtYWJjMTIz
```

### View Kafka Logs

```bash
molecule login -s secrets-upgrade-customer -h kafka-broker1.confluent
journalctl -u confluent-kafka -n 100
```

---

## Files

- `molecule.yml` - Scenario configuration (aligned with CP Ansible standards)
- `converge.yml` - Deployment playbook (runs twice to simulate upgrade)
- `verify.yml` - Validation tests (critical customer key preservation checks)
- `README.md` - This file

---

## Standards Alignment

This scenario follows CP Ansible Molecule testing standards:
- Uses ubuntu1804 base image with Dockerfile template
- Hostnames use .confluent domain convention
- Network named "confluent"
- Standard provisioner configuration with hash_behaviour: merge

---

## Related Documentation

- Implementation Status: `docs/IMPLEMENTATION_STATUS.md`
- Fix Proposal: `docs/master_key_divergence_fix_proposal.md`
- Testing Plan: `docs/master_key_divergence_testing_plan.md`
- SEC-03 Test: `molecule/secrets-upgrade-auto/` (upgrade with auto-generated key)
