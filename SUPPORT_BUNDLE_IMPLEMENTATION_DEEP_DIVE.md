# Support Bundle Implementation Deep Dive

**Date:** 2026-04-15  
**Purpose:** Technical architecture documentation for support bundle collection in CP-Ansible  
**Audience:** Developers, architects, reviewers

---

## Recent Updates (2026-04-15)

### ✅ **Automatic Collection on Failure - IMPLEMENTED**

**Implementation:** Ansible callback plugin approach

**What Changed:**
1. ✅ **Created** `callback_plugins/support_bundle_on_failure.py`
   - Monitors `all.yml` playbook execution
   - Reads `support_bundle_auto_collect_on_failure` from inventory
   - Auto-triggers `support_bundle.yml` on deployment failure
   - No command change required (still run `ansible-playbook all.yml`)

2. ✅ **Updated** `ansible.cfg` and `playbooks/ansible.cfg`
   - Enabled callback plugin: `callbacks_enabled=support_bundle_on_failure`
   - Added plugin path: `callback_plugins=./callback_plugins`

3. ✅ **Streamlined** diagnostics collection
   - **Removed:** `system/` directory (os_info, memory, disk, network, etc.)
   - **Removed:** Extra diagnostics (ports, open_files, ulimit, sysctl)
   - **Kept:** Essential only (service_status, journalctl, processes)
   - **Result:** 65-115 KB smaller per host, 7 seconds faster collection

4. ✅ **Component-First** directory structure maintained
   - Structure: `<component_name>/<hostname>/` 
   - Example: `kafka_broker/ec2-hostname/configs/`

**Usage:**
```yaml
# In inventory or group_vars
support_bundle_auto_collect_on_failure: true

# Run deployment normally
ansible-playbook -i inventory.yml playbooks/all.yml

# On failure → support bundle automatically collected!
```

**Files Modified:**
- `callback_plugins/support_bundle_on_failure.py` (NEW)
- `ansible.cfg`, `playbooks/ansible.cfg` (UPDATED)
- `playbooks/all.yml` (UPDATED - added comments)
- `roles/common/tasks/collect_diagnostics.yml` (UPDATED - streamlined)
- `roles/common/tasks/collect_support_bundle.yml` (UPDATED - removed system dir)
- `roles/variables/defaults/main.yml` (UPDATED - added flag)

**Documentation:**
- `AUTO_SUPPORT_BUNDLE_IMPLEMENTATION.md` (NEW)
- `STREAMLINE_DIAGNOSTICS_CHANGES.md` (NEW)
- `COMPONENT_FIRST_STRUCTURE_CHANGES.md` (EXISTING)

---

## 1. How is the bundle actually collected? (Task Execution Flow)

### **Playbook Entry Point**: `playbooks/support_bundle.yml`

**Phase 1: Setup (localhost only)**
```yaml
Play 1: "Support Bundle Setup" - hosts: localhost
├─ Task 1: Gather facts (setup module)
├─ Task 2: Import variables role
├─ Task 3: Generate bundle_timestamp (e.g., "20260415_172004")
├─ Task 4: Set bundle_name = "support_bundle_{{ timestamp }}_{{ cluster_name }}"
├─ Task 5: Set bundle_path = "{{ output_path }}/support_bundle_{{ timestamp }}_{{ cluster_name }}"
├─ Task 6: Create bundle directory structure
│   └─ Creates: bundle_path/ansible/
├─ Task 7: Save Ansible version info → bundle_path/ansible/ansible_version.txt
├─ Task 8: Save execution context → bundle_path/ansible/execution_context.yml
└─ Task 9: Save sanitized inventory → bundle_path/ansible/inventory_sanitized.yml
```

**Phase 2: Per-Component Collection (parallel across all components)**
```yaml
Play 2-11: One play per component type (zookeeper, kafka_broker, etc.)
For each component host:
  ├─ Runs on: component hosts (e.g., kafka_broker group)
  ├─ Gather facts: true
  ├─ Includes: roles/common/tasks/collect_support_bundle.yml
  │
  └─ collect_support_bundle.yml execution:
      │
      ├─ Step 1: Set host_bundle_dir = "{{ bundle_path }}/{{ component_name }}/{{ inventory_hostname }}"
      │
      ├─ Step 2: Create host directories on LOCALHOST (delegated)
      │   └─ Creates: configs/, logs/, system/, diagnostics/
      │
      ├─ Step 3: COLLECT CONFIG FILES (direct fetch from remote to localhost)
      │   ├─ fetch: config_file → host_bundle_dir/configs/
      │   ├─ fetch: jaas_file → host_bundle_dir/configs/
      │   ├─ fetch: log4j_file → host_bundle_dir/configs/
      │   ├─ fetch: systemd_file → host_bundle_dir/configs/
      │   ├─ fetch: systemd_override → host_bundle_dir/configs/
      │   └─ fetch: client_config_file → host_bundle_dir/configs/
      │   └─ (OR if skip_configs: create metadata file only)
      │
      ├─ Step 4: SANITIZE CONFIGS (on localhost, delegated)
      │   └─ include_tasks: sanitize_config_files_local.yml
      │       ├─ Find all .properties files
      │       ├─ sed -i: redact passwords/secrets (11 patterns)
      │       ├─ Find all JAAS files
      │       ├─ sed -i: redact password= values (3 patterns)
      │       ├─ Find systemd override files
      │       ├─ sed -i: redact env vars (6 patterns)
      │       └─ Generate SANITIZATION_REPORT.txt
      │
      ├─ Step 5: COLLECT LOG FILES
      │   ├─ find: search log_dir on remote host
      │   └─ loop: fetch each log file → host_bundle_dir/logs/
      │
      ├─ Step 6: COLLECT SYSTEM INFO
      │   └─ include_tasks: collect_system_info.yml
      │       ├─ shell: uname -a, /etc/os-release → /tmp/os_info_{{ hostname }}.txt
      │       ├─ fetch: /tmp/os_info_{{ hostname }}.txt → host_bundle_dir/system/os_info.txt
      │       ├─ shell: java -version → /tmp/java_version_{{ hostname }}.txt
      │       ├─ fetch: → host_bundle_dir/system/java_version.txt
      │       ├─ shell: free -h, /proc/meminfo → /tmp/memory_{{ hostname }}.txt
      │       ├─ fetch: → host_bundle_dir/system/memory.txt
      │       ├─ shell: df -h, lsblk → /tmp/disk_{{ hostname }}.txt
      │       ├─ fetch: → host_bundle_dir/system/disk.txt
      │       ├─ shell: ip addr, ip route → /tmp/network_{{ hostname }}.txt
      │       ├─ fetch: → host_bundle_dir/system/network.txt
      │       ├─ shell: hostname, /etc/hosts, /etc/resolv.conf → /tmp/hostname_{{ hostname }}.txt
      │       ├─ fetch: → host_bundle_dir/system/hostname.txt
      │       ├─ shell: env | grep (sanitized) → /tmp/environment_{{ hostname }}.txt
      │       ├─ fetch: → host_bundle_dir/system/environment.txt
      │       ├─ copy: ansible facts → host_bundle_dir/system/ansible_facts.txt (localhost)
      │       └─ file: cleanup all /tmp/*_{{ hostname }}.txt files
      │
      ├─ Step 7: COLLECT DIAGNOSTICS
      │   └─ include_tasks: collect_diagnostics.yml
      │       ├─ shell: systemctl status → /tmp/service_status_{{ hostname }}.txt
      │       ├─ fetch: → host_bundle_dir/diagnostics/service_status.txt
      │       ├─ shell: journalctl -u {{ service }} -n 1000 → /tmp/journalctl_{{ hostname }}.log
      │       ├─ fetch: → host_bundle_dir/diagnostics/journalctl.log
      │       ├─ shell: ps aux | grep → /tmp/processes_{{ hostname }}.txt
      │       ├─ fetch: → host_bundle_dir/diagnostics/processes.txt
      │       ├─ shell: ss -tulpn / netstat → /tmp/ports_{{ hostname }}.txt
      │       ├─ fetch: → host_bundle_dir/diagnostics/ports.txt
      │       ├─ shell: lsof -p → /tmp/open_files_{{ hostname }}.txt
      │       ├─ fetch: → host_bundle_dir/diagnostics/open_files.txt
      │       ├─ shell: ulimit -a → /tmp/ulimit_{{ hostname }}.txt
      │       ├─ fetch: → host_bundle_dir/diagnostics/ulimit.txt
      │       ├─ shell: sysctl -a | grep → /tmp/sysctl_{{ hostname }}.txt
      │       ├─ fetch: → host_bundle_dir/diagnostics/sysctl.txt
      │       └─ file: cleanup all /tmp/*_{{ hostname }}.txt files
      │
      └─ Step 8: GENERATE HOST MANIFEST
          └─ template: host_manifest.yml.j2 → host_bundle_dir/host_manifest.yml (localhost)
```

**Phase 3: Finalization (localhost only)**
```yaml
Play 12: "Finalize Support Bundle" - hosts: localhost
├─ Task 1: Generate bundle_manifest.yml (template)
│   └─ Creates: bundle_path/bundle_manifest.yml
├─ Task 2: Archive support bundle
│   ├─ Input: bundle_path/ (entire directory)
│   └─ Output: support_bundle_output_path/bundle_name.tar.gz
├─ Task 3: Remove uncompressed bundle directory
│   └─ Deletes: bundle_path/
├─ Task 4: Get archive stats
└─ Task 5: Display completion message
    └─ Shows: location and size in MB
```

### **Key Architecture Decisions**

**Direct Fetch Pattern** (per Comment #8):
```
Remote Host                         Ansible Controller
-----------                         ------------------
1. shell: cmd > /tmp/data.txt   →   
2.                              ←   fetch: /tmp/data.txt → bundle/host/dir/
3. file: rm /tmp/data.txt       →
```

**NOT** using remote staging:
```
Remote Host                         Ansible Controller
-----------                         ------------------
❌ mkdir /tmp/bundle/               (OLD fetch_logs approach)
❌ copy files to /tmp/bundle/
❌ archive /tmp/bundle/ → bundle.tar.gz
✅ fetch bundle.tar.gz → controller
```

---

## 2. What triggers it? (Trigger Mechanisms)

### **Current State**

**Trigger Method 1: MANUAL** ✅ **IMPLEMENTED**

```bash
# Standalone playbook execution
ansible-playbook -i inventory.yml playbooks/support_bundle.yml

# With component filtering
ansible-playbook -i inventory.yml playbooks/support_bundle.yml --tags kafka_broker,schema_registry

# With custom output path and Ansible log
ansible-playbook -i inventory.yml playbooks/support_bundle.yml \
  -e support_bundle_output_path=/var/bundles \
  -e support_bundle_cluster_name=prod_us_west \
  -e support_bundle_ansible_log_path=/path/to/ansible.log
```

**Trigger Method 2: AUTOMATIC ON PLAYBOOK FAILURE** ✅ **IMPLEMENTED**

Via Ansible callback plugin:

```bash
# Set in inventory
support_bundle_auto_collect_on_failure: true

# Run deployment normally - no command change needed!
ansible-playbook -i inventory.yml playbooks/all.yml

# On failure, callback plugin automatically:
# 1. Detects the failure (v2_playbook_on_stats hook)
# 2. Reads support_bundle_auto_collect_on_failure from inventory
# 3. Triggers: ansible-playbook support_bundle.yml
# 4. Shows completion message with bundle location
```

**Implementation:**
- ✅ Callback plugin: `callback_plugins/support_bundle_on_failure.py`
- ✅ Enabled in `ansible.cfg`: `callbacks_enabled=support_bundle_on_failure`
- ✅ Reads inventory variables via play context
- ✅ No command change required (still run `all.yml`)
- ✅ Automatic subprocess execution of support_bundle.yml

**Auto-Trigger - NOT YET IMPLEMENTED**:
- ❌ Integration with health checks (still using old fetch_logs.yml)
- ❌ pytest/molecule hooks

### **Callback Plugin Implementation Details**

**File**: `callback_plugins/support_bundle_on_failure.py`

**How It Works:**

```
Ansible Playbook Execution
         ↓
1. v2_playbook_on_start(playbook)
   • Captures: playbook_name, playbook_dir
   • Logs: "Support bundle callback loaded for playbook: all.yml"
         ↓
2. v2_playbook_on_play_start(play)  [Called for EACH play]
   • Resolves play.hosts (group names) to actual Host objects
   • For each host: gets all variables from variable_manager
   • Checks: support_bundle_auto_collect_on_failure
   • Sets: self.auto_collect_enabled = True (if found)
         ↓
3. Play execution...
         ↓
4. v2_playbook_on_stats(stats)  [Called on playbook completion]
   • Check: Is this all.yml or confluent.yml? (Skip other playbooks)
   • Check: Were there any failures?
   • Check: Is auto_collect_enabled == True?
         ↓
         YES → Collect bundle
         ↓
5. _collect_support_bundle()
   • Build command: ansible-playbook support_bundle.yml -i <inventory>
   • Execute via subprocess.run()
   • Display: "Support Bundle Collected Successfully"
         ↓
6. Playbook exits with original error
```

**Key Code Sections:**

```python
# Step 2: Read inventory variable from play context
def v2_playbook_on_play_start(self, play):
    variable_manager = play.get_variable_manager()
    inventory = variable_manager._inventory
    
    # Resolve groups to actual hosts
    actual_hosts = inventory.get_hosts(pattern=play.hosts)
    
    for host_obj in actual_hosts:
        all_vars = variable_manager.get_vars(play=play, host=host_obj)
        auto_collect = all_vars.get('support_bundle_auto_collect_on_failure', False)
        
        if auto_collect in [True, 'true', 'True', 'yes', '1']:
            self.auto_collect_enabled = True
            break

# Step 4: Detect failures
def v2_playbook_on_stats(self, stats):
    if self.playbook_name not in ['all.yml', 'confluent.yml']:
        return  # Skip non-main playbooks
    
    # Count failures
    for host in stats.processed.keys():
        summary = stats.summarize(host)
        if summary.get('failures', 0) > 0:
            self.deployment_failed = True
            
    if self.deployment_failed and self.auto_collect_enabled:
        self._collect_support_bundle()

# Step 5: Execute support bundle collection
def _collect_support_bundle(self):
    cmd = ['ansible-playbook', support_bundle_playbook]
    
    # Get inventory from context.CLIARGS
    inventory = context.CLIARGS.get('inventory')
    cmd.extend(['-i', str(inventory[0])])
    
    subprocess.run(cmd, cwd=self.playbook_dir)
```

**Critical Bug Fixes Applied:**

1. **Group Resolution Bug** (Fixed)
   - **Problem**: `play.hosts` contains group names ("all", "kafka_broker") not host objects
   - **Symptom**: `inventory.get_host("all")` returned `None`
   - **Fix**: Use `inventory.get_hosts(pattern=play.hosts)` to resolve groups to hosts

2. **Inventory Path Bug** (Fixed)
   - **Problem**: `inventory` can be a tuple, causing "expected str instance, tuple found"
   - **Fix**: Convert with `str(inventory[0])` when it's a list/tuple

3. **Variable Access Bug** (Fixed)
   - **Problem**: Couldn't read inventory variables in Ansible 2.16+
   - **Fix**: Access via `variable_manager.get_vars(play=play, host=host_obj)`

**Configuration:**

```ini
# ansible.cfg (required)
[defaults]
callbacks_enabled = support_bundle_on_failure
callback_plugins = ./callback_plugins

# playbooks/ansible.cfg (required)
[defaults]
callbacks_enabled = support_bundle_on_failure
callback_plugins = ../callback_plugins
```

```yaml
# roles/variables/defaults/main.yml
support_bundle_auto_collect_on_failure: false  # Default: disabled

# inventory or group_vars (to enable)
support_bundle_auto_collect_on_failure: true
```

---

### **What SHOULD Be Implemented** (per One-Pager V1) - FUTURE

**Trigger 1: Automatic on ANY Playbook Failure** ✅ **DONE** (via callback plugin)
```yaml
# In playbooks/all.yml or confluent.platform.yml
- name: Deploy Confluent Platform
  hosts: all
  tasks:
    - name: Run main deployment
      block:
        - import_playbook: confluent.platform.yml
      rescue:
        - name: Collect support bundle on failure
          import_playbook: support_bundle.yml
          when: auto_collect_support_bundle_on_failure | default(false)
        
        - name: Re-raise original error
          fail:
            msg: |
              Deployment failed. Support bundle collected at:
              {{ hostvars['localhost']['bundle_path'] }}.tar.gz
```

**Trigger 2: Health Check Failures**
```yaml
# In roles/kafka_broker/tasks/health_check.yml
- name: Run health checks
  block:
    - name: Check broker is healthy
      # ... health check tasks ...
  rescue:
    - name: Collect support bundle for debugging
      include_tasks: ../../common/tasks/collect_support_bundle.yml
      vars:
        # component-specific vars
    
    - fail:
        msg: "Health check failed. Bundle at {{ host_bundle_dir }}"
```

**Trigger 3: Molecule Test Failures** (pytest hook)
```python
# molecule/conftest.py
import subprocess
import pytest

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    
    if rep.when == "call" and rep.failed:
        # Extract scenario name from item
        scenario = item.funcargs.get('scenario_name', 'unknown')
        
        # Run support bundle collection
        subprocess.run([
            'ansible-playbook',
            '-i', '.molecule/ansible_inventory',
            'playbooks/support_bundle.yml',
            '-e', f'support_bundle_cluster_name=molecule_{scenario}'
        ])
```

### **Configuration Variables**

All variables are defined in `roles/variables/defaults/main.yml`:

```yaml
# Output and naming
support_bundle_output_path: "{{ playbook_dir }}"  # Local directory for final bundle .tar.gz
support_bundle_cluster_name: cp_cluster            # Cluster name in bundle filename
support_bundle_base_path: /tmp                     # Remote temp directory for diagnostics temp files

# Collection control
support_bundle_sanitize_configs: true              # Redact passwords/secrets from configs (enabled by default)
support_bundle_skip_configs: false                 # Skip all config file collection
support_bundle_journalctl_lines: 1000              # Number of journalctl lines to collect per service

# Auto-trigger
support_bundle_auto_collect_on_failure: false      # Auto-trigger on playbook failure via callback plugin

# Ansible logs (NEW in 2026-04-15)
support_bundle_ansible_log_path: ""                # Path to Ansible playbook execution log to include in bundle
                                                   # Example: -e "support_bundle_ansible_log_path=/path/to/ansible.log"
```

**Usage Examples:**

```bash
# With Ansible log file
ansible-playbook support_bundle.yml -e "support_bundle_ansible_log_path=ansible_run.log"

# Disable sanitization (for internal debugging)
ansible-playbook support_bundle.yml -e "support_bundle_sanitize_configs=false"

# Custom output location
ansible-playbook support_bundle.yml -e "support_bundle_output_path=/var/bundles"
```

---

## 3. Error Handling (Mid-Collection Failures)

### **Design Philosophy**: "Collect as much as possible, never fail"

**Every single collection task uses**: `ignore_errors: true`

### **Failure Scenarios & Behavior**

**Scenario 1: Config file doesn't exist**
```yaml
- name: Fetch main config file
  fetch:
    src: "{{ config_file }}"
    dest: "{{ host_bundle_dir }}/configs/"
  ignore_errors: true  # ← Continues even if file missing
  when: not support_bundle_skip_configs
```
**Result**: Missing file, but collection continues. Other configs still fetched.

**Scenario 2: Permission denied reading log files**
```yaml
- name: Find log files
  find:
    paths: "{{ log_dir }}"
  become: true
  register: log_files_found
  ignore_errors: true  # ← Continues even if permission denied

- name: Fetch log files
  fetch:
    src: "{{ item.path }}"
  become: true
  loop: "{{ log_files_found.files }}"
  ignore_errors: true  # ← Each file fetch can fail independently
  when: log_files_found.matched > 0
```
**Result**: Partial log collection. Some logs fetched, permission-denied ones skipped.

**Scenario 3: System command fails (e.g., lsof not installed)**
```yaml
- name: Collect open files for service
  shell: |
    pgrep -f {{ service_name }} | xargs -r lsof -p > /tmp/open_files_{{ inventory_hostname }}.txt 2>/dev/null || echo "lsof not available or no process found" > /tmp/open_files_{{ inventory_hostname }}.txt
  ignore_errors: true  # ← Continues even if lsof missing
```
**Result**: Creates file with "lsof not available" message instead of actual data.

**Scenario 4: Sanitization fails (sed syntax error)**
```yaml
- name: Sanitize .properties files
  shell: |
    sed -i '' -E 's/(.*password.*=).*/\1 ***REDACTED***/gi' {{ item.path }}
  loop: "{{ properties_files.files }}"
  ignore_errors: true  # ← Continues even if sed fails
  delegate_to: localhost
```
**Result**: Unsanitized file remains. SANITIZATION_REPORT.txt still generated.

**Scenario 5: Entire host unreachable**
```yaml
# In playbooks/support_bundle.yml
- name: Kafka Broker Support Bundle
  hosts: kafka_broker
  gather_facts: true  # ← May fail if host unreachable
  tasks:
    - include_role:
        name: common
        tasks_from: collect_support_bundle.yml
```
**Result**: 
- If gather_facts fails: No collection for that host
- Other hosts in same group: Continue normally
- Other component groups: Unaffected
- Bundle still created with partial data

### **Partial Bundle Handling**

**Bundle Manifest Reflects Partial State**:
```yaml
# bundle_path/host_manifest.yml (per host)
collection_scope:
  configs_collected: true/false  # Based on support_bundle_skip_configs
  configs_sanitized: true/false  # Based on support_bundle_sanitize_configs
  logs_collected: true           # Always true (attempt made)
  system_info_collected: true    # Always true (attempt made)
  diagnostics_collected: true    # Always true (attempt made)
```

**What's NOT captured**:
- No detailed error log of what failed
- No per-file success/failure tracking
- No count of "attempted vs successful" file fetches
- Sanitization report shows counts but not which specific files failed

### **Gap: No Failure Indicators**

**Missing**: Per-task success tracking
```yaml
# SHOULD EXIST but doesn't:
- name: Track collection results
  set_fact:
    collection_results:
      configs: "{{ config_fetch_results }}"
      logs: "{{ log_fetch_results }}"
      system: "{{ system_info_results }}"
      diagnostics: "{{ diagnostics_results }}"

- name: Generate collection report
  template:
    src: collection_report.yml.j2
    dest: "{{ host_bundle_dir }}/COLLECTION_REPORT.yml"
  vars:
    # Shows which tasks succeeded/failed
```

**Recommendation**: Add `COLLECTION_REPORT.yml` to each host directory showing:
- Which files were successfully fetched
- Which files failed (with error messages)
- Which commands failed (lsof, sysctl, etc.)
- Overall collection health: "COMPLETE", "PARTIAL", "FAILED"

---

## 4. Sanitization Design (The Missing Detail)

### **Current Implementation**

**File**: `roles/common/tasks/sanitize_config_files_local.yml`

**Approach**: Regex-based sed replacement on LOCALHOST after fetch

**When it runs**: 
- After config files fetched to controller
- Before logs/system/diagnostics collection
- Only if `support_bundle_sanitize_configs: true`

### **Sanitization Flow**

```
Remote Host                 Controller                      Output
-----------                 ----------                      ------
server.properties    →   fetch to bundle/configs/      →   [original]
                          ↓
                        sanitize_config_files_local.yml
                          ├─ find *.properties
                          ├─ sed -i (11 patterns)
                          ├─ find *jaas.conf
                          ├─ sed -i (3 patterns)
                          ├─ find override.conf
                          └─ sed -i (6 patterns)
                          ↓
                        [sanitized files in place]    →   ssl.keystore.password= ***REDACTED***
```

### **Sanitization Patterns**

**Category 1: .properties files** (11 patterns)
```bash
# Pattern: .*password.*= → .*password.*= ***REDACTED***
sed -i '' -E 's/(.*password.*=).*/\1 ***REDACTED***/gi' file.properties
# Matches:
#   ssl.keystore.password=secret123 → ssl.keystore.password= ***REDACTED***
#   ldap.bind.password=admin → ldap.bind.password= ***REDACTED***
#   confluent.metrics.reporter.sasl.password=foo → .password= ***REDACTED***

# Pattern: .*secret.*=
sed -i '' -E 's/(.*secret.*=).*/\1 ***REDACTED***/gi'
# Matches:
#   confluent.security.master.key=abc123 → .master.key= ***REDACTED***
#   api.secret=xyz → api.secret= ***REDACTED***

# Pattern: .*\.key=
sed -i '' -E 's/(.*\.key=).*/\1 ***REDACTED***/gi'
# Matches:
#   ssl.key.password=foo → ssl.key.password= ***REDACTED***
#   encryption.key=bar → encryption.key= ***REDACTED***

# Pattern: .*credential.*=
sed -i '' -E 's/(.*credential.*=).*/\1 ***REDACTED***/gi'

# Pattern: .*token.*=
sed -i '' -E 's/(.*token.*=).*/\1 ***REDACTED***/gi'

# Specific patterns:
sed -i '' -E 's/(.*truststore\.password.*=).*/\1 ***REDACTED***/gi'
sed -i '' -E 's/(.*keystore\.password.*=).*/\1 ***REDACTED***/gi'
sed -i '' -E 's/(.*ssl\.key\.password.*=).*/\1 ***REDACTED***/gi'

# THE PROBLEM PATTERN (Comment #19):
sed -i '' -E 's/(.*sasl\.jaas\.config.*=).*/\1 ***REDACTED***/gi'
# Redacts ENTIRE JAAS config line including login module!
# Before: sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required username="admin" password="secret";
# After:  sasl.jaas.config= ***REDACTED***
# SHOULD: sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required username="***" password="***";

sed -i '' -E 's/(.*basic\.auth\.credentials\.source.*=).*/\1 ***REDACTED***/gi'
sed -i '' -E 's/(.*ldap\..*password.*=).*/\1 ***REDACTED***/gi'
```

**Category 2: JAAS files** (3 patterns)
```bash
# Pattern: password="..."
sed -i '' -E 's/(password=")[^"]*"/\1***REDACTED***"/gi' jaas.conf
# Before: password="secret123"
# After:  password="***REDACTED***"

# Pattern: password='...'
sed -i '' -E "s/(password=')[^']*'/\1***REDACTED***'/gi" jaas.conf
# Before: password='secret123'
# After:  password='***REDACTED***'

# Pattern: password=value (no quotes)
sed -i '' -E 's/(password=)[^; \t]*/\1***REDACTED***/gi' jaas.conf
# Before: password=secret123;
# After:  password=***REDACTED***;
```

**Category 3: Systemd override files** (6 patterns)
```bash
# Pattern: Environment=.*PASSWORD.*=
sed -i '' -E 's/(Environment=.*PASSWORD.*=).*/\1***REDACTED***/gi' override.conf
# Before: Environment="KAFKA_OPTS=-Dpassword=secret"
# After:  Environment="KAFKA_OPTS=-Dpassword=***REDACTED***"

sed -i '' -E 's/(Environment=.*SECRET.*=).*/\1***REDACTED***/gi'
sed -i '' -E 's/(Environment=.*KEY.*=).*/\1***REDACTED***/gi'
sed -i '' -E 's/(Environment=.*TOKEN.*=).*/\1***REDACTED***/gi'
sed -i '' -E 's/(Environment=.*CREDENTIAL.*=).*/\1***REDACTED***/gi'

# Specific pattern:
sed -i '' -E 's/(Environment=CONFLUENT_SECURITY_MASTER_KEY=).*/\1***REDACTED***/gi'
```

### **Special Handling**

**Password files removal**:
```bash
# Never collect password.properties files
find {{ host_bundle_dir }}/configs -name "*password.properties" -type f -exec rm -f {} \;
echo "File removed: {}" > {{ host_bundle_dir }}/configs/removed_password_files.txt
```

### **Sanitization Report**

**Generated**: `host_bundle_dir/configs/SANITIZATION_REPORT.txt`
```
=== Configuration File Sanitization Report ===
Timestamp: 2026-04-15T17:20:04Z

Sanitized .properties files: 3
Sanitized JAAS files: 1
Sanitized override files: 1

Sensitive patterns redacted:
  - password, secret, key, token, credential
  - keystore.password, truststore.password
  - sasl.jaas.config, ldap passwords
  - CONFLUENT_SECURITY_MASTER_KEY

WARNING: While sanitization has been performed, please review
         files before sharing to ensure no sensitive data remains.
```

### **CRITICAL DESIGN FLAW** (Comment #19)

**Problem**: `sasl.jaas.config` redaction is too aggressive

**Current behavior**:
```properties
# BEFORE sanitization
sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required username="admin" password="admin-secret";

# AFTER sanitization
sasl.jaas.config= ***REDACTED***
```

**Expected behavior** (per Mansi's comment #19):
```properties
# SHOULD BE
sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required username="***REDACTED***" password="***REDACTED***";
```

**Why it matters**: Login module configuration is critical diagnostic info (PLAIN vs SCRAM vs GSSAPI). Redacting entire line loses context.

### **Missing: Component-Specific Sanitization** (Comment #11.1)

**Current**: Same patterns for all components

**Needed**: Per-component pattern lists
```yaml
# roles/kafka_broker/vars/support_bundle.yml
kafka_broker_sensitive_patterns:
  - "ssl.keystore.password"
  - "ssl.key.password"
  - "ssl.truststore.password"
  - "sasl.jaas.config"  # Special handling needed
  - "listener.name.*.sasl.jaas.config"

# roles/schema_registry/vars/support_bundle.yml
schema_registry_sensitive_patterns:
  - "kafkastore.ssl.keystore.password"
  - "schema.registry.ssl.keystore.password"
  - "authentication.roles.admin"  # May contain sensitive role configs

# roles/control_center/vars/support_bundle.yml
control_center_sensitive_patterns:
  - "confluent.controlcenter.rest.authentication.password"
  - "confluent.metrics.topic.replication"  # Not sensitive, don't redact!
```

### **Recommended Sanitization Refactor**

**New approach**: Component-aware, structure-preserving
```yaml
# New file: roles/common/tasks/sanitize_config_smart.yml
- name: Load component-specific sanitization rules
  include_vars:
    file: "{{ role_path }}/../{{ component_name }}/vars/sanitization_rules.yml"
  ignore_errors: true  # Falls back to generic rules

- name: Sanitize with structure preservation
  script: sanitize_smart.py
  args:
    config_dir: "{{ host_bundle_dir }}/configs"
    rules: "{{ sanitization_rules }}"
    preserve_structure: true  # Keep JAAS login modules intact
```

**Python script** (sanitize_smart.py):
```python
def sanitize_jaas_config(value):
    """Preserve login module, redact only credentials"""
    # Before: org...PlainLoginModule required username="admin" password="secret";
    value = re.sub(r'username="[^"]*"', 'username="***"', value)
    value = re.sub(r'password="[^"]*"', 'password="***"', value)
    # After: org...PlainLoginModule required username="***" password="***";
    return value

def sanitize_properties_file(file_path, rules):
    for line in file:
        key, value = line.split('=', 1)
        if key in rules['special_handling']:
            # Custom sanitization (e.g., JAAS config)
            sanitized = rules['special_handling'][key](value)
        elif any(pattern in key for pattern in rules['redact_patterns']):
            # Full redaction
            sanitized = "***REDACTED***"
        # ...
```

---

## 5. Per-Component File List (What Gets Collected)

### **Generic Collection** (ALL components)

**From `roles/common/tasks/collect_support_bundle.yml:27-92`**:

Every component collects:
1. Main config file (`config_file` variable)
2. JAAS config (`component.jaas_file` if defined)
3. Log4j config (`component.log4j_file` if defined)
4. Systemd service file (`component.systemd_file` if defined)
5. Systemd override (`component.systemd_override` if defined)
6. Client config (`component.client_config_file` if defined)
7. All files in `log_dir`
8. System info (OS, Java, memory, disk, network, etc.)
9. Diagnostics (service status, journalctl, processes, ports, ulimits, sysctl)

### **Zookeeper** (`playbooks/support_bundle.yml:65-81`)

```yaml
Variables passed:
  service_name: "{{ zookeeper_service_name }}"  # e.g., "confluent-zookeeper"
  component_name: "zookeeper"
  component: "{{ zookeeper }}"
  config_file: "{{ zookeeper.config_file }}"  # e.g., /etc/kafka/zookeeper.properties
  log_dir: "{{ zookeeper_log_dir }}"  # e.g., /var/log/kafka
  user: "{{ zookeeper_user }}"  # e.g., cp-kafka
  group: "{{ zookeeper_group }}"  # e.g., confluent

Files collected:
  configs/
    ├─ zookeeper.properties
    ├─ zookeeper_jaas.conf (if SASL enabled)
    ├─ log4j.properties
    ├─ confluent-zookeeper.service
    └─ override.conf (if exists)
  logs/
    ├─ zookeeper.out
    ├─ log-cleaner.log (if exists)
    └─ server.log (if exists)
  system/ (standard)
  diagnostics/ (standard)
```

### **Kafka Broker** (`playbooks/support_bundle.yml:99-114`)

```yaml
Variables:
  service_name: "{{ kafka_broker_service_name }}"  # confluent-kafka
  component_name: "kafka_broker"
  component: "{{ kafka_broker }}"
  config_file: "{{ kafka_broker.config_file }}"  # /etc/kafka/server.properties
  log_dir: "{{ kafka_broker_log_dir }}"  # /var/log/kafka
  user: "{{ kafka_broker_user }}"
  group: "{{ kafka_broker_group }}"

Files collected:
  configs/
    ├─ server.properties
    ├─ kafka_server_jaas.conf (if SASL)
    ├─ kafka_client_jaas.conf (if client auth)
    ├─ log4j.properties
    ├─ confluent-kafka.service
    ├─ override.conf
    └─ producer.properties / consumer.properties (if client_config_file set)
  logs/
    ├─ server.log
    ├─ state-change.log
    ├─ kafka-request.log
    ├─ log-cleaner.log
    ├─ controller.log
    ├─ kafka-authorizer.log (if ACLs enabled)
    └─ *.log (all others in log_dir)
```

### **Schema Registry** (`playbooks/support_bundle.yml:116-131`)

```yaml
Files collected:
  configs/
    ├─ schema-registry.properties
    ├─ schema-registry_jaas.conf
    ├─ log4j.properties
    ├─ confluent-schema-registry.service
    └─ override.conf
  logs/
    ├─ schema-registry.log
    ├─ schema-registry-gc.log (if GC logging enabled)
    └─ *.log
```

### **Kafka Connect** (`playbooks/support_bundle.yml:133-148`)

```yaml
Files collected:
  configs/
    ├─ connect-distributed.properties
    ├─ connect-log4j.properties
    ├─ kafka_connect_jaas.conf
    ├─ confluent-kafka-connect.service
    └─ override.conf
  logs/
    ├─ connect.log
    ├─ connect-gc.log
    └─ *.log
```

### **KSQL** (`playbooks/support_bundle.yml:167-182`)

```yaml
Files collected:
  configs/
    ├─ ksql-server.properties
    ├─ log4j.properties
    ├─ ksql_jaas.conf
    ├─ confluent-ksqldb.service
    └─ override.conf
  logs/
    ├─ ksql.log
    ├─ ksql-queries.log (if query logging enabled)
    └─ *.log
```

### **Control Center** (`playbooks/support_bundle.yml:201-216`)

```yaml
Files collected:
  configs/
    ├─ control-center.properties
    ├─ control-center-production.properties (if exists)
    ├─ log4j.properties
    ├─ control_center_jaas.conf
    ├─ confluent-control-center.service
    └─ override.conf
  logs/
    ├─ control-center.log
    ├─ control-center-gc.log
    └─ *.log
```

### **USM Agent** (`playbooks/support_bundle.yml:235-252`) ✅ **ADDED 2026-04-15**

```yaml
Variables:
  service_name: "{{ usm_agent_service_name }}"  # usm-agent
  component_name: "usm_agent"
  component: "{{ usm_agent }}"
  config_file: "{{ usm_agent.config_file }}"  # /etc/confluent/usm-agent/usm-agent.properties
  log_dir: "{{ usm_agent.log_dir }}"  # /var/log/confluent/usm-agent
  user: "{{ usm_agent_default_user }}"  # cp-usm-agent
  group: "{{ usm_agent_default_group }}"  # confluent

Files collected:
  configs/
    ├─ usm-agent.properties
    ├─ usm-agent.service
    └─ override.conf
  logs/
    ├─ *.log (all log files in /var/log/confluent/usm-agent)
  diagnostics/ (standard)

Note: USM Agent does NOT have JAAS or Log4j configs (not a Java service)
Note: Credential files (ccloud_credential.yaml, cp_credential.yaml) NOT collected by default
```

### **GAPS: Component-Specific Files Not Collected** (Comment #9.1, #13)

**Missing files per component**:

**Zookeeper**:
- ❌ `myid` file (data dir)
- ❌ `snapshot.*` / `log.*` (transaction logs - too large, but metadata useful)
- ❌ `/etc/kafka/zookeeper-env.sh` (environment overrides)

**Kafka Broker**:
- ❌ `meta.properties` (broker metadata)
- ❌ `recovery-point-offset-checkpoint`
- ❌ `replication-offset-checkpoint`
- ❌ `/var/lib/kafka/` structure (disk layout, partition assignments)
- ❌ Connector configs (if embedded mode)

**Schema Registry**:
- ❌ Schema cache files (if exists)
- ❌ Metrics reporter config (if separate file)

**Kafka Connect**:
- ❌ Connector configs from `/etc/kafka-connect/` (individual connector properties)
- ❌ Plugin installation paths
- ❌ Transform configs

**Control Center**:
- ❌ Data directory structure (`/var/lib/confluent-control-center/`)
- ❌ RocksDB stats (if accessible)

**USM Agent**:
- ❌ Credential files (`ccloud_credential.yaml`, `cp_credential.yaml`) not collected
- ❌ Additional log files beyond main log directory

### **Recommended: Per-Component File Lists**

```yaml
# roles/zookeeper/vars/support_bundle_files.yml
additional_config_files:
  - "{{ zookeeper_data_dir }}/myid"
  - "/etc/kafka/zookeeper-env.sh"

additional_data_files:
  - path: "{{ zookeeper_data_dir }}"
    include: "version-2/snapshot.* metadata"  # Metadata only, not full snapshots
    max_files: 3  # Latest 3 snapshots

# roles/kafka_broker/vars/support_bundle_files.yml
additional_config_files:
  - "{{ kafka_broker_data_dirs[0] }}/meta.properties"
  - "/etc/kafka/kafka-env.sh"

additional_data_files:
  - "{{ kafka_broker_data_dirs[0] }}/recovery-point-offset-checkpoint"
  - "{{ kafka_broker_data_dirs[0] }}/replication-offset-checkpoint"

# Usage in collect_support_bundle.yml:
- name: Include component-specific file list
  include_vars:
    file: "{{ role_path }}/../{{ component_name }}/vars/support_bundle_files.yml"
  ignore_errors: true  # Not all components have custom lists

- name: Collect additional config files
  fetch:
    src: "{{ item }}"
    dest: "{{ host_bundle_dir }}/configs/"
  loop: "{{ additional_config_files | default([]) }}"
```

---

## 6. Relationship to fetch_logs.yml (Replace, Extend, or Coexist?)

### **Current Reality**: Coexist (Unintentionally)

```
fetch_logs.yml                    support_bundle.yml
--------------                    ------------------
✅ Auto-triggered                 ❌ Manual only
   (health check failures)
                                  
Collects:                         Collects:
  - Logs from log_dir               - Logs from log_dir
  - Main config file                - ALL config files
  ❌ No sanitization                ✅ Sanitization optional
  ❌ No system info                 ✅ System info
  ❌ No diagnostics                 ✅ Diagnostics
                                  
Output:                           Output:
  troubleshooting/                  playbooks/support_bundle_*.tar.gz
    hostname.tar.gz                   ├─ ansible/
                                      ├─ hostname1/
Used by:                              │   ├─ configs/
  10+ health_check.yml files          │   ├─ logs/
                                      │   ├─ system/
Still in use: YES                     └─ manifest.yml
                                  
                                  Used by:
                                    Nobody (manual only)
```

### **Problem**: Redundancy and Confusion

**Scenario 1: Health check fails**
- ✅ `fetch_logs` runs automatically
- ✅ Creates `troubleshooting/hostname.tar.gz`
- ❌ Limited data (logs + 1 config)
- ❌ No sanitization

**Scenario 2: Deployment fails before health check**
- ❌ No automatic collection
- User must manually run `support_bundle.yml`

**Scenario 3: User wants comprehensive bundle**
- Must manually run `support_bundle.yml`
- Might not know it exists (documentation gap)

### **One-Pager Expectation** (Comments #5, #14)

**Comment #5 (Raahil)**:
> "is support bundle going to replace it or it will have to seperately be used?"

**Comment #5.1 (Raahil)**:
> "can we tie them somehow?"

**Comment #14 (Rohan)**:
> "we need to build this in a way that if playbook fails, then support bundle is automatically generated"

**Answer**: Support bundle SHOULD **replace** fetch_logs, not coexist.

### **Recommended Transition Plan**

**Phase 1: Make support_bundle auto-triggerable** (immediate)
```yaml
# Add to roles/common/tasks/collect_support_bundle.yml
# Make it usable from health checks with same interface as fetch_logs

# Usage in health checks becomes:
- include_tasks: ../../common/tasks/collect_support_bundle.yml
  vars:
    # Same variables as before
    service_name: "{{ kafka_broker_service_name }}"
    config_file: "{{ kafka_broker.config_file }}"
    # ... etc
```

**Phase 2: Add lightweight mode** (optional performance optimization)
```yaml
# roles/variables/defaults/main.yml
support_bundle_lightweight_mode: false

# When true:
# - Skip system info collection
# - Skip diagnostics collection
# - Collect only: configs + logs
# - Equivalent to old fetch_logs behavior
```

**Phase 3: Migrate health checks** (bulk update)
```bash
# Update all 10 health_check.yml files:
find roles/*/tasks/health_check.yml -exec sed -i \
  's/fetch_logs\.yml/collect_support_bundle.yml/g' {} \;

# Add component_name and component variables to each
```

**Phase 4: Add global error handler** (auto-trigger on ANY failure)
```yaml
# In playbooks/all.yml
- name: Run Confluent Platform Deployment
  block:
    - import_playbook: confluent.platform.yml
  rescue:
    - name: Auto-collect support bundle on failure
      import_playbook: support_bundle.yml
      when: auto_collect_support_bundle_on_failure | default(false)
    
    - fail:
        msg: "Deployment failed. Bundle: {{ hostvars['localhost']['bundle_path'] }}.tar.gz"
```

**Phase 5: Deprecate fetch_logs** (after 1-2 releases)
```yaml
# Add deprecation warning to fetch_logs.yml
- name: Deprecation Warning
  debug:
    msg: |
      WARNING: fetch_logs.yml is deprecated and will be removed in CP-Ansible 8.0.
      Please use support_bundle.yml instead.
      See: https://docs.confluent.io/ansible/support-bundle.html
```

### **Migration Comparison**

| Aspect | fetch_logs (old) | support_bundle (new) | Migration Effort |
|--------|------------------|----------------------|------------------|
| **Trigger** | Auto (health checks) | Auto (health checks) | Update 10 files |
| **Interface** | `service_name, config_file, log_dir, user, group` | Same + `component_name, component` | Add 2 vars per call |
| **Output** | `troubleshooting/hostname.tar.gz` | `bundle_path/hostname/` | Update paths in error messages |
| **Performance** | ~30 seconds | ~2 minutes (full) | Add lightweight mode |
| **Data collected** | Minimal | Comprehensive | Feature improvement |

### **Answer**: **REPLACE** (Recommended)

**Rationale**:
1. ✅ Aligns with one-pager expectations (Comments #5, #14)
2. ✅ Single tool reduces confusion
3. ✅ More diagnostic data for troubleshooting
4. ✅ Sanitization built-in (can share externally)
5. ✅ Consistent collection across manual + auto-trigger
6. ⚠️ Slightly slower (mitigated by lightweight mode)
7. ⚠️ Migration effort (10 files, straightforward)

---

## 7. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SUPPORT BUNDLE COLLECTION ARCHITECTURE                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│  TRIGGER POINTS  │
└──────────────────┘
         │
         ├─── Manual: ansible-playbook support_bundle.yml
         ├─── Auto (playbook failure): callback plugin → subprocess.run
         │       └─── callback_plugins/support_bundle_on_failure.py
         │           • Monitors all.yml execution via v2_playbook_on_play_start
         │           • Reads inventory variable: support_bundle_auto_collect_on_failure
         │           • Triggers on failure via v2_playbook_on_stats
         │           • Executes: ansible-playbook support_bundle.yml
         │
         └─── Auto (health check): include_tasks collect_support_bundle.yml [FUTURE]

         ↓

┌─────────────────────────────────────────────────────────────────────────────┐
│  PLAYBOOK ENTRY: playbooks/support_bundle.yml                               │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ├─── Play 1: Setup (localhost)
         │       └─── Create bundle_path/ansible/
         │
         ├─── Play 2-11: Per-component collection (parallel)
         │       │
         │       └─── For each component host:
         │               │
         │               ├─── include_role: common/collect_support_bundle.yml
         │               │       │
         │               │       └─── [See detailed flow below]
         │               │
         │               └─── Creates: bundle_path/{{ component_name }}/{{ inventory_hostname }}/
         │
         └─── Play 12: Finalization (localhost)
                 ├─── Generate manifest
                 ├─── Archive to .tar.gz
                 └─── Clean up uncompressed dir

         ↓

┌─────────────────────────────────────────────────────────────────────────────┐
│  ROLE TASK: roles/common/tasks/collect_support_bundle.yml                   │
│  (Runs on: component host, creates: localhost dirs)                         │
└─────────────────────────────────────────────────────────────────────────────┘

   Step 1: Create host dirs on LOCALHOST (delegated)
      │
      └─── file: state=directory
              path: bundle_path/hostname/{configs,logs,system,diagnostics}
              delegate_to: localhost

   Step 2: COLLECT CONFIGS (direct fetch pattern)
      │
      ┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
      │  Remote Host    │         │  Ansible Module  │         │  Localhost      │
      └─────────────────┘         └──────────────────┘         └─────────────────┘
            │                             │                             │
            │  1. Read file               │                             │
            │ <────────────────────────── │ fetch:                      │
            │                             │   src=/etc/kafka/server.properties
            │                             │   dest=bundle/.../configs/  │
            │  2. Return content          │                             │
            │ ─────────────────────────> │                             │
            │                             │  3. Write to localhost      │
            │                             │ ──────────────────────────> │
            │                             │                             │
            │  4. Repeat for JAAS, Log4j, systemd files...              │
            │                                                            │

   Step 3: SANITIZE (on localhost)
      │
      └─── include_tasks: sanitize_config_files_local.yml
              │
              ├─── find: *.properties
              ├─── shell: sed -i (11 patterns) [delegated]
              ├─── find: *jaas.conf
              ├─── shell: sed -i (3 patterns) [delegated]
              ├─── find: override.conf
              └─── shell: sed -i (6 patterns) [delegated]

   Step 4: COLLECT LOGS (direct fetch)
      │
      └─── find: paths=log_dir → register: log_files_found
           │
           └─── loop: fetch each log file
                   │
                ┌──┴────────────────────────────────────────────────┐
                │  Remote: /var/log/kafka/server.log                │
                │         ↓ fetch (become: true)                    │
                │  Localhost: bundle/.../logs/server.log            │
                └───────────────────────────────────────────────────┘

   Step 5: COLLECT DIAGNOSTICS (shell + fetch pattern) - STREAMLINED
      │
      └─── include_tasks: collect_diagnostics.yml
              │
              ├─── systemctl status → /tmp/service_status_host.txt → fetch [ESSENTIAL]
              ├─── journalctl -u svc -n 1000 → /tmp/journalctl_host.log → fetch [ESSENTIAL]
              └─── ps aux | grep → /tmp/processes_host.txt → fetch [ESSENTIAL]
              
              [REMOVED: ports, open_files, ulimit, sysctl - not essential]
              [REMOVED: system info collection - focus on app diagnostics]

   Step 6: GENERATE HOST MANIFEST
      │
      └─── template: host_manifest.yml.j2
              dest: bundle/.../host_manifest.yml
              delegate_to: localhost

   [All tasks use: ignore_errors: true]

         ↓

┌─────────────────────────────────────────────────────────────────────────────┐
│  FINALIZATION (localhost)                                                    │
└─────────────────────────────────────────────────────────────────────────────┘

   Bundle Directory Structure (before archive):
      │
      bundle_path/  (e.g., support_bundle_20260415_172004_cp_cluster/)
      ├─── ansible/
      │      ├─── ansible_version.txt
      │      ├─── execution_context.yml
      │      └─── inventory_sanitized.yml
      ├─── kafka_broker/                    ← Component-first grouping
      │      ├─── kafka-broker-1/
      │      │      ├─── configs/
      │      │      │      ├─── server.properties [SANITIZED]
      │      │      │      ├─── kafka_server_jaas.conf [SANITIZED]
      │      │      │      ├─── log4j.properties
      │      │      │      ├─── confluent-kafka.service
      │      │      │      ├─── override.conf [SANITIZED]
      │      │      │      └─── SANITIZATION_REPORT.txt
      │      │      ├─── logs/
      │      │      │      ├─── server.log
      │      │      │      ├─── state-change.log
      │      │      │      └─── ...
      │      │      ├─── diagnostics/              ← STREAMLINED (3 files only)
      │      │      │      ├─── service_status.txt  [ESSENTIAL - systemd status]
      │      │      │      ├─── journalctl.log      [ESSENTIAL - last 1000 lines]
      │      │      │      └─── processes.txt       [ESSENTIAL - ps aux output]
      │      │      └─── host_manifest.yml
      │      │      
      │      │      [REMOVED: system/ directory - not essential for app debugging]
      │      │      [REMOVED: ports.txt, open_files.txt, ulimit.txt, sysctl.txt]
      │      ├─── kafka-broker-2/
      │      │      └─── [same structure]
      │      └─── kafka-broker-3/
      │             └─── [same structure]
      ├─── zookeeper/                       ← Component-first grouping
      │      ├─── zk-1/
      │      │      └─── [same structure]
      │      ├─── zk-2/
      │      │      └─── [same structure]
      │      └─── zk-3/
      │             └─── [same structure]
      ├─── schema_registry/                 ← Component-first grouping
      │      └─── schema-registry-1/
      │             └─── [same structure]
      └─── bundle_manifest.yml

         ↓

   archive: path=bundle_path/ → bundle_name.tar.gz (gzip)
   file: rm -rf bundle_path/
   stat: get archive size
   debug: "Bundle created: X.XX MB"

         ↓

┌─────────────────────────────────────────────────────────────────────────────┐
│  OUTPUT                                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

   Location: {{ support_bundle_output_path }}/support_bundle_*.tar.gz
   Default: {{ playbook_dir }}/support_bundle_20260415_172004_cp_cluster.tar.gz

   Size: Typical 10-50 MB (depends on log size)
   
   Ready for:
      - Manual analysis
      - Upload to GTS ticket
      - Claude skill debugging (future)
      - S3 upload from CI (future)

┌─────────────────────────────────────────────────────────────────────────────┐
│  ERROR HANDLING                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

   Every collection task: ignore_errors: true
      │
      ├─── Config file missing → Skip, continue with other configs
      ├─── Permission denied → Skip that file, continue
      ├─── Command not found (lsof) → Write "not available" message
      ├─── Host unreachable → Skip that host, continue with others
      └─── Sanitization fails → Unsanitized file remains (warning in report)

   Result: Partial bundle always created (unless total playbook failure)
   
   Gap: No detailed collection success/failure report per host
```

---

## Summary

This document provides the detailed technical implementation of the support bundle collection mechanism, covering:

1. **Collection Flow**: Task-by-task execution from playbook entry to final archive
2. **Trigger Mechanisms**: Current manual-only + recommended auto-trigger implementations
3. **Error Handling**: Resilience design with `ignore_errors` everywhere
4. **Sanitization**: Regex patterns, limitations, and recommended improvements
5. **Per-Component Files**: What gets collected from each component type
6. **fetch_logs Relationship**: Recommendation to replace rather than coexist
7. **Architecture Diagram**: Visual flow from trigger to output

**Key Findings**:
- ✅ Core collection mechanism is solid and follows direct-fetch pattern
- ❌ Missing auto-trigger functionality (V1 requirement)
- ❌ JAAS sanitization too aggressive (loses login module info)
- ❌ No component-specific file collection
- ❌ No detailed collection success/failure tracking

**Critical Gaps**: Auto-trigger, Ansible playbook logs, pytest hooks
