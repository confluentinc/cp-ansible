# Support Bundle Collection Playbook - Implementation Plan

## Context

CP-ansible is used by customers to deploy Confluent Platform via the `all.yml` playbook. When customers encounter issues, they need to provide comprehensive diagnostic information to support teams for troubleshooting. Currently, there's a basic `fetch_logs.yml` playbook that only collects component logs and main config files.

**Problem**: The existing log collection is insufficient for debugging customer issues. Support teams need:
- Complete configuration files (JAAS, Log4j, systemd overrides, not just main .properties)
- System information (OS, Java version, memory, disk, network)
- Runtime diagnostics (service status, journalctl logs, processes, ports)
- Ansible execution context (inventory, version, variables used)
- SSL certificate metadata (expiry dates, to catch cert issues)

**Solution**: Create a comprehensive support bundle collection playbook that gathers all diagnostic data needed to debug deployment and runtime issues, packaged in a timestamped archive with manifests.

**User Preferences**:
- Full comprehensive implementation (configs, logs, system info, diagnostics)
- Include SSL certificate metadata collection (expiry, subject, issuer)
- Configurable output path for the bundle
- Skip Kafka-specific diagnostics (topics/consumer groups) for initial version

---

## Implementation Overview

### Files to Create

1. **`playbooks/support_bundle.yml`** - Main playbook entry point
2. **`roles/common/tasks/collect_support_bundle.yml`** - Core collection orchestrator
3. **`roles/common/tasks/collect_system_info.yml`** - System information collection
4. **`roles/common/tasks/collect_diagnostics.yml`** - Runtime diagnostics collection
5. **`roles/common/tasks/collect_ssl_metadata.yml`** - SSL certificate metadata extraction
6. **`roles/common/templates/host_manifest.yml.j2`** - Per-host manifest template
7. **`roles/common/templates/bundle_manifest.yml.j2`** - Overall bundle manifest template

### Variables to Add

In `roles/variables/defaults/main.yml`:
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
```

---

## Archive Structure

```
support_bundle_<timestamp>_<cluster_name>/
├── ansible/
│   ├── inventory_sanitized.yml      # Inventory with passwords removed
│   ├── ansible_version.txt
│   └── execution_context.yml        # Groups, host counts, etc.
│
├── bundle_manifest.yml               # Overall bundle metadata
│
├── <hostname1>/
│   ├── configs/
│   │   ├── <component>.properties
│   │   ├── <component>_jaas.conf
│   │   ├── log4j.properties
│   │   ├── <service>.service
│   │   ├── override.conf
│   │   └── sensitive_files_metadata.txt  # Permissions, not content
│   ├── logs/                         # Component log files
│   ├── ssl/                          # SSL certificate metadata only
│   │   └── certificates_info.txt     # Expiry, subject, issuer
│   ├── system/
│   │   ├── os_info.txt
│   │   ├── java_version.txt
│   │   ├── memory.txt
│   │   ├── disk.txt
│   │   ├── network.txt
│   │   ├── hostname.txt
│   │   ├── environment.txt           # Sanitized env vars
│   │   └── ansible_facts.txt
│   ├── diagnostics/
│   │   ├── service_status.txt
│   │   ├── journalctl.log
│   │   ├── processes.txt
│   │   ├── ports.txt
│   │   ├── open_files.txt
│   │   ├── ulimit.txt
│   │   └── sysctl.txt
│   └── host_manifest.yml
│
└── <hostname2>/...
```

Final output: `support_bundle_<timestamp>_<cluster_name>.tar.gz`

---

## Implementation Steps

### Step 1: Create Main Playbook (`playbooks/support_bundle.yml`)

**Pattern**: Follow the same structure as `playbooks/fetch_logs.yml` (reference file)

```yaml
---
# Set up bundle structure on localhost
- name: Support Bundle Setup
  hosts: localhost
  connection: local
  gather_facts: true
  tasks:
    - name: Generate bundle timestamp
      set_fact:
        bundle_timestamp: "{{ ansible_date_time.date | regex_replace('-','') }}_{{ ansible_date_time.time | regex_replace(':','') }}"

    - name: Set bundle name
      set_fact:
        bundle_name: "support_bundle_{{ bundle_timestamp }}_{{ support_bundle_cluster_name }}"
        bundle_path: "{{ support_bundle_output_path }}/support_bundle_{{ bundle_timestamp }}_{{ support_bundle_cluster_name }}"

    - name: Create bundle directory structure
      file:
        path: "{{ bundle_path }}/ansible"
        state: directory
        mode: '0755'

    - name: Save Ansible version info
      copy:
        content: |
          Ansible Version: {{ ansible_version.full }}
          Python Version: {{ ansible_python.version.major }}.{{ ansible_python.version.minor }}.{{ ansible_python.version.micro }}
          Playbook: support_bundle.yml
          Timestamp: {{ ansible_date_time.iso8601 }}
        dest: "{{ bundle_path }}/ansible/ansible_version.txt"

    - name: Save execution context
      copy:
        content: "{{ {'timestamp': ansible_date_time.iso8601, 'groups': groups, 'ansible_version': ansible_version.full} | to_nice_yaml }}"
        dest: "{{ bundle_path }}/ansible/execution_context.yml"

    - name: Save sanitized inventory
      copy:
        content: "{{ hostvars | to_nice_json }}"
        dest: "{{ bundle_path }}/ansible/inventory_sanitized.yml"
      no_log: "{{ mask_sensitive_logs }}"

# Import variables
- name: Import all variables
  hosts: all
  tags: always
  tasks:
    - import_role:
        name: variables

# Component collection plays (same pattern as fetch_logs.yml)
- name: Zookeeper Support Bundle
  hosts: zookeeper
  gather_facts: true
  tags: zookeeper
  tasks:
    - include_role:
        name: common
        tasks_from: collect_support_bundle.yml
      vars:
        service_name: "{{ zookeeper_service_name }}"
        component_name: "zookeeper"
        component: "{{ zookeeper }}"
        config_file: "{{ zookeeper.config_file }}"
        log_dir: "{{ zookeeper_log_dir }}"
        user: "{{ zookeeper_user }}"
        group: "{{ zookeeper_group }}"

# Repeat for: kafka_controller, kafka_broker, schema_registry,
# kafka_connect, kafka_connect_replicator, ksql, kafka_rest,
# control_center, control_center_next_gen

# Finalize bundle
- name: Finalize Support Bundle
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Generate bundle manifest
      template:
        src: "{{ playbook_dir }}/../roles/common/templates/bundle_manifest.yml.j2"
        dest: "{{ hostvars['localhost']['bundle_path'] }}/bundle_manifest.yml"

    - name: Archive support bundle
      archive:
        path: "{{ hostvars['localhost']['bundle_path'] }}"
        dest: "{{ support_bundle_output_path }}/{{ hostvars['localhost']['bundle_name'] }}.tar.gz"
        format: gz

    - name: Display completion message
      debug:
        msg: |
          ========================================
          Support Bundle Created Successfully
          ========================================
          Location: {{ support_bundle_output_path }}/{{ hostvars['localhost']['bundle_name'] }}.tar.gz
          Size: {{ (lookup('file', support_bundle_output_path + '/' + hostvars['localhost']['bundle_name'] + '.tar.gz') | length / 1024 / 1024) | round(2) }} MB

          Please upload this file to your support ticket.
```

**Critical Reference**: `/Users/ishikapaliwal/ansible_collections/confluent/platform/playbooks/fetch_logs.yml` - Shows the exact pattern for iterating through components

### Step 2: Create Core Collection Task (`roles/common/tasks/collect_support_bundle.yml`)

**Pattern**: Extend the logic from `roles/common/tasks/fetch_logs.yml` (reference file)

```yaml
---
# Set up paths
- name: Set bundle facts
  set_fact:
    host_bundle_dir: "{{ hostvars['localhost']['bundle_path'] }}/{{ inventory_hostname }}"
    remote_temp_dir: "{{ support_bundle_base_path }}/support_bundle_{{ inventory_hostname }}"

- name: Create host bundle directories on localhost
  file:
    path: "{{ host_bundle_dir }}/{{ item }}"
    state: directory
    mode: '0755'
  delegate_to: localhost
  vars:
    ansible_connection: local
    ansible_become: "{{ ansible_become_localhost }}"
  loop:
    - configs
    - logs
    - ssl
    - system
    - diagnostics

- name: Remove old remote temporary directory
  file:
    path: "{{ remote_temp_dir }}"
    state: absent

- name: Create remote temporary directory
  file:
    path: "{{ remote_temp_dir }}/{{ item }}"
    state: directory
    mode: '0750'
    owner: "{{ user }}"
    group: "{{ group }}"
  loop:
    - configs
    - logs
    - ssl
    - system
    - diagnostics

# COLLECT CONFIGURATION FILES
- name: Copy main config file
  copy:
    src: "{{ config_file }}"
    dest: "{{ remote_temp_dir }}/configs/"
    remote_src: true
    mode: '0640'
  ignore_errors: true
  register: config_copy_result

- name: Copy JAAS config file
  copy:
    src: "{{ component.jaas_file }}"
    dest: "{{ remote_temp_dir }}/configs/"
    remote_src: true
    mode: '0640'
  ignore_errors: true
  when: component.jaas_file is defined

- name: Copy Log4j config file
  copy:
    src: "{{ component.log4j_file }}"
    dest: "{{ remote_temp_dir }}/configs/"
    remote_src: true
    mode: '0640'
  ignore_errors: true
  when: component.log4j_file is defined

- name: Copy systemd service file
  copy:
    src: "{{ component.systemd_file }}"
    dest: "{{ remote_temp_dir }}/configs/"
    remote_src: true
    mode: '0640'
  ignore_errors: true
  when: component.systemd_file is defined

- name: Copy systemd override file
  copy:
    src: "{{ component.systemd_override }}"
    dest: "{{ remote_temp_dir }}/configs/"
    remote_src: true
    mode: '0640'
  ignore_errors: true
  when: component.systemd_override is defined

- name: Collect client config file (if exists)
  copy:
    src: "{{ component.client_config_file }}"
    dest: "{{ remote_temp_dir }}/configs/"
    remote_src: true
    mode: '0640'
  ignore_errors: true
  when: component.client_config_file is defined

# COLLECT LOG FILES (reuse existing pattern from fetch_logs.yml)
- name: Find log files
  find:
    paths: "{{ log_dir }}"
    recurse: false
  register: log_files_found
  ignore_errors: true

- name: Copy log files to temporary directory
  copy:
    src: "{{ item.path }}"
    dest: "{{ remote_temp_dir }}/logs/"
    remote_src: true
    mode: '0640'
  loop: "{{ log_files_found.files }}"
  ignore_errors: true
  when: log_files_found.matched > 0

# COLLECT SSL CERTIFICATE METADATA
- name: Collect SSL metadata
  include_tasks: collect_ssl_metadata.yml
  when: ssl_enabled | default(false)

# COLLECT SYSTEM INFORMATION
- name: Collect system information
  include_tasks: collect_system_info.yml

# COLLECT RUNTIME DIAGNOSTICS
- name: Collect runtime diagnostics
  include_tasks: collect_diagnostics.yml

# GENERATE HOST MANIFEST
- name: Generate host manifest
  template:
    src: host_manifest.yml.j2
    dest: "{{ remote_temp_dir }}/host_manifest.yml"
  ignore_errors: true

# ARCHIVE AND FETCH
- name: Archive remote bundle
  archive:
    path: "{{ remote_temp_dir }}"
    dest: "{{ remote_temp_dir }}.tar.gz"
    format: gz
    remove: true
  ignore_errors: true

- name: Fetch bundle to localhost
  fetch:
    src: "{{ remote_temp_dir }}.tar.gz"
    dest: "{{ host_bundle_dir }}/"
    flat: true
  ignore_errors: true

- name: Extract bundle on localhost
  unarchive:
    src: "{{ host_bundle_dir }}/support_bundle_{{ inventory_hostname }}.tar.gz"
    dest: "{{ host_bundle_dir }}/"
  delegate_to: localhost
  vars:
    ansible_connection: local
  ignore_errors: true

- name: Remove archive from localhost (keep extracted files)
  file:
    path: "{{ host_bundle_dir }}/support_bundle_{{ inventory_hostname }}.tar.gz"
    state: absent
  delegate_to: localhost
  vars:
    ansible_connection: local

- name: Clean up remote temp files
  file:
    path: "{{ remote_temp_dir }}.tar.gz"
    state: absent
  ignore_errors: true
```

**Critical Reference**: `/Users/ishikapaliwal/ansible_collections/confluent/platform/roles/common/tasks/fetch_logs.yml` - Core collection pattern to follow

### Step 3: Create System Info Collection (`roles/common/tasks/collect_system_info.yml`)

```yaml
---
- name: Collect OS information
  shell: |
    echo "=== OS Information ===" > {{ remote_temp_dir }}/system/os_info.txt
    uname -a >> {{ remote_temp_dir }}/system/os_info.txt
    cat /etc/os-release >> {{ remote_temp_dir }}/system/os_info.txt 2>/dev/null || true
  args:
    executable: "{{ shell_executable }}"
  ignore_errors: true

- name: Collect Java version
  shell: |
    java -version 2>&1 > {{ remote_temp_dir }}/system/java_version.txt
    echo "---" >> {{ remote_temp_dir }}/system/java_version.txt
    echo "JAVA_HOME: $JAVA_HOME" >> {{ remote_temp_dir }}/system/java_version.txt
  args:
    executable: "{{ shell_executable }}"
  ignore_errors: true

- name: Collect memory information
  shell: |
    free -h > {{ remote_temp_dir }}/system/memory.txt 2>&1
    echo "---" >> {{ remote_temp_dir }}/system/memory.txt
    cat /proc/meminfo >> {{ remote_temp_dir }}/system/memory.txt 2>/dev/null || true
  args:
    executable: "{{ shell_executable }}"
  ignore_errors: true

- name: Collect disk information
  shell: |
    df -h > {{ remote_temp_dir }}/system/disk.txt 2>&1
    echo "---" >> {{ remote_temp_dir }}/system/disk.txt
    lsblk >> {{ remote_temp_dir }}/system/disk.txt 2>/dev/null || true
  args:
    executable: "{{ shell_executable }}"
  ignore_errors: true

- name: Collect network configuration
  shell: |
    ip addr > {{ remote_temp_dir }}/system/network.txt 2>/dev/null || ifconfig >> {{ remote_temp_dir }}/system/network.txt 2>&1
    echo "---" >> {{ remote_temp_dir }}/system/network.txt
    ip route >> {{ remote_temp_dir }}/system/network.txt 2>/dev/null || netstat -rn >> {{ remote_temp_dir }}/system/network.txt 2>&1
  args:
    executable: "{{ shell_executable }}"
  ignore_errors: true

- name: Collect hostname and DNS
  shell: |
    echo "Hostname: $(hostname)" > {{ remote_temp_dir }}/system/hostname.txt
    echo "FQDN: $(hostname -f 2>/dev/null || hostname)" >> {{ remote_temp_dir }}/system/hostname.txt
    echo "---" >> {{ remote_temp_dir }}/system/hostname.txt
    cat /etc/hosts >> {{ remote_temp_dir }}/system/hostname.txt 2>/dev/null || true
    echo "---" >> {{ remote_temp_dir }}/system/hostname.txt
    cat /etc/resolv.conf >> {{ remote_temp_dir }}/system/hostname.txt 2>/dev/null || true
  args:
    executable: "{{ shell_executable }}"
  ignore_errors: true

- name: Collect environment variables (sanitized)
  shell: |
    env | grep -E 'JAVA|KAFKA|CONFLUENT|PATH|USER|HOME' | grep -v -E 'PASSWORD|SECRET|KEY|TOKEN' > {{ remote_temp_dir }}/system/environment.txt 2>&1
  args:
    executable: "{{ shell_executable }}"
  ignore_errors: true

- name: Save Ansible facts
  copy:
    content: |
      Ansible Version: {{ ansible_version.full }}
      OS Family: {{ ansible_os_family }}
      Distribution: {{ ansible_distribution }} {{ ansible_distribution_version }}
      Kernel: {{ ansible_kernel }}
      Architecture: {{ ansible_architecture }}
      Memory (MB): {{ ansible_memtotal_mb }}
      Processor Count: {{ ansible_processor_count }}
      Processor Cores: {{ ansible_processor_cores }}
      Python Version: {{ ansible_python_version }}
    dest: "{{ remote_temp_dir }}/system/ansible_facts.txt"
  ignore_errors: true
```

### Step 4: Create Diagnostics Collection (`roles/common/tasks/collect_diagnostics.yml`)

```yaml
---
- name: Check service status
  shell: |
    systemctl status {{ service_name }} --no-pager -l > {{ remote_temp_dir }}/diagnostics/service_status.txt 2>&1 || true
  args:
    executable: "{{ shell_executable }}"
  ignore_errors: true

- name: Collect journalctl logs
  shell: |
    journalctl -u {{ service_name }} -n {{ support_bundle_journalctl_lines }} --no-pager > {{ remote_temp_dir }}/diagnostics/journalctl.log 2>&1 || true
  args:
    executable: "{{ shell_executable }}"
  ignore_errors: true

- name: Collect process information
  shell: |
    ps aux | grep -E '{{ service_name }}|java' | grep -v grep > {{ remote_temp_dir }}/diagnostics/processes.txt 2>&1
    echo "---" >> {{ remote_temp_dir }}/diagnostics/processes.txt
    pgrep -f {{ service_name }} | xargs -r ps -f -p >> {{ remote_temp_dir }}/diagnostics/processes.txt 2>/dev/null || true
  args:
    executable: "{{ shell_executable }}"
  ignore_errors: true

- name: Collect listening ports
  shell: |
    ss -tulpn > {{ remote_temp_dir }}/diagnostics/ports.txt 2>/dev/null || netstat -tulpn > {{ remote_temp_dir }}/diagnostics/ports.txt 2>&1 || true
  args:
    executable: "{{ shell_executable }}"
  ignore_errors: true

- name: Collect open files for service
  shell: |
    pgrep -f {{ service_name }} | xargs -r lsof -p > {{ remote_temp_dir }}/diagnostics/open_files.txt 2>/dev/null || echo "lsof not available or no process found" > {{ remote_temp_dir }}/diagnostics/open_files.txt
  args:
    executable: "{{ shell_executable }}"
  ignore_errors: true

- name: Collect ulimit settings
  shell: |
    echo "Current user limits:" > {{ remote_temp_dir }}/diagnostics/ulimit.txt
    ulimit -a >> {{ remote_temp_dir }}/diagnostics/ulimit.txt 2>&1
    echo "---" >> {{ remote_temp_dir }}/diagnostics/ulimit.txt
    echo "Service user limits:" >> {{ remote_temp_dir }}/diagnostics/ulimit.txt
    su - {{ user }} -s /bin/bash -c "ulimit -a" >> {{ remote_temp_dir }}/diagnostics/ulimit.txt 2>/dev/null || echo "Could not retrieve service user limits" >> {{ remote_temp_dir }}/diagnostics/ulimit.txt
  args:
    executable: "{{ shell_executable }}"
  ignore_errors: true

- name: Collect kernel parameters
  shell: |
    sysctl -a 2>/dev/null | grep -E 'vm\.|net\.|fs\.' > {{ remote_temp_dir }}/diagnostics/sysctl.txt || echo "Could not retrieve sysctl parameters" > {{ remote_temp_dir }}/diagnostics/sysctl.txt
  args:
    executable: "{{ shell_executable }}"
  ignore_errors: true
```

### Step 5: Create SSL Metadata Collection (`roles/common/tasks/collect_ssl_metadata.yml`)

```yaml
---
- name: Find keystore files
  find:
    paths: "{{ ssl_file_dir_final }}"
    patterns: "*.jks,*.p12,*.pfx,*.bcfks"
  register: keystore_files
  ignore_errors: true

- name: Extract certificate metadata from keystores
  shell: |
    echo "=== {{ item.path }} ===" >> {{ remote_temp_dir }}/ssl/certificates_info.txt
    echo "File: {{ item.path }}" >> {{ remote_temp_dir }}/ssl/certificates_info.txt
    echo "Size: {{ item.size }} bytes" >> {{ remote_temp_dir }}/ssl/certificates_info.txt
    echo "Modified: {{ item.mtime }}" >> {{ remote_temp_dir }}/ssl/certificates_info.txt
    echo "" >> {{ remote_temp_dir }}/ssl/certificates_info.txt
    keytool -list -v -keystore {{ item.path }} -storepass:file <(echo "{{ lookup('vars', component_name + '_keystore_storepass', default='changeit') }}") 2>/dev/null | grep -E 'Alias|Owner|Issuer|Valid from|Valid until|SHA256' >> {{ remote_temp_dir }}/ssl/certificates_info.txt 2>&1 || echo "Could not read keystore" >> {{ remote_temp_dir }}/ssl/certificates_info.txt
    echo "---" >> {{ remote_temp_dir }}/ssl/certificates_info.txt
    echo "" >> {{ remote_temp_dir }}/ssl/certificates_info.txt
  args:
    executable: "{{ shell_executable }}"
  loop: "{{ keystore_files.files }}"
  when: keystore_files.matched > 0
  ignore_errors: true
  no_log: "{{ mask_sensitive_logs }}"

- name: Find PEM certificate files
  find:
    paths: "{{ ssl_file_dir_final }}"
    patterns: "*.crt,*.pem,ca.crt"
  register: cert_files
  ignore_errors: true

- name: Extract certificate metadata from PEM files
  shell: |
    echo "=== {{ item.path }} ===" >> {{ remote_temp_dir }}/ssl/certificates_info.txt
    echo "File: {{ item.path }}" >> {{ remote_temp_dir }}/ssl/certificates_info.txt
    echo "" >> {{ remote_temp_dir }}/ssl/certificates_info.txt
    openssl x509 -in {{ item.path }} -noout -text 2>/dev/null | grep -E 'Subject:|Issuer:|Not Before|Not After|Public-Key' >> {{ remote_temp_dir }}/ssl/certificates_info.txt 2>&1 || echo "Could not read certificate" >> {{ remote_temp_dir }}/ssl/certificates_info.txt
    echo "---" >> {{ remote_temp_dir }}/ssl/certificates_info.txt
    echo "" >> {{ remote_temp_dir }}/ssl/certificates_info.txt
  args:
    executable: "{{ shell_executable }}"
  loop: "{{ cert_files.files }}"
  when: cert_files.matched > 0
  ignore_errors: true

- name: List SSL file permissions (metadata only, no content)
  shell: |
    ls -lh {{ ssl_file_dir_final }}/ > {{ remote_temp_dir }}/ssl/file_permissions.txt 2>&1 || echo "Could not list SSL directory" > {{ remote_temp_dir }}/ssl/file_permissions.txt
  args:
    executable: "{{ shell_executable }}"
  ignore_errors: true
```

### Step 6: Create Manifest Templates

**`roles/common/templates/host_manifest.yml.j2`**:
```yaml
collection_info:
  timestamp: {{ ansible_date_time.iso8601 }}
  hostname: {{ inventory_hostname }}
  component: {{ component_name }}
  service_name: {{ service_name }}

host_info:
  os_family: {{ ansible_os_family }}
  distribution: {{ ansible_distribution }} {{ ansible_distribution_version }}
  kernel: {{ ansible_kernel }}
  architecture: {{ ansible_architecture }}
  memory_mb: {{ ansible_memtotal_mb }}

ansible_info:
  ansible_version: {{ ansible_version.full }}
  python_version: {{ ansible_python_version }}

component_info:
  config_file: {{ config_file }}
  log_dir: {{ log_dir }}
  user: {{ user }}
  group: {{ group }}
  service_file: {{ component.systemd_file | default('N/A') }}

collection_scope:
  configs_collected: true
  logs_collected: true
  ssl_metadata_collected: {{ ssl_enabled | default(false) }}
  system_info_collected: true
  diagnostics_collected: true
```

**`roles/common/templates/bundle_manifest.yml.j2`**:
```yaml
support_bundle_info:
  bundle_name: {{ hostvars['localhost']['bundle_name'] }}
  timestamp: {{ hostvars['localhost']['bundle_timestamp'] }}
  cluster_name: {{ support_bundle_cluster_name }}
  output_path: {{ support_bundle_output_path }}

ansible_controller:
  ansible_version: {{ ansible_version.full }}
  python_version: {{ ansible_python.version.major }}.{{ ansible_python.version.minor }}

inventory_summary:
  total_hosts: {{ groups['all'] | length }}
  zookeeper_hosts: {{ groups['zookeeper'] | default([]) | length }}
  kafka_controller_hosts: {{ groups['kafka_controller'] | default([]) | length }}
  kafka_broker_hosts: {{ groups['kafka_broker'] | default([]) | length }}
  schema_registry_hosts: {{ groups['schema_registry'] | default([]) | length }}
  kafka_connect_hosts: {{ groups['kafka_connect'] | default([]) | length }}
  ksql_hosts: {{ groups['ksql'] | default([]) | length }}
  kafka_rest_hosts: {{ groups['kafka_rest'] | default([]) | length }}
  control_center_hosts: {{ groups['control_center'] | default([]) | length }}

collection_settings:
  journalctl_lines: {{ support_bundle_journalctl_lines }}
  base_path: {{ support_bundle_base_path }}
```

---

## Critical Files to Reference

1. **`/Users/ishikapaliwal/ansible_collections/confluent/platform/playbooks/fetch_logs.yml`** - Shows playbook structure and component iteration pattern

2. **`/Users/ishikapaliwal/ansible_collections/confluent/platform/roles/common/tasks/fetch_logs.yml`** - Core collection, archival, and fetch pattern

3. **`/Users/ishikapaliwal/ansible_collections/confluent/platform/roles/variables/vars/main.yml`** (lines 55-61, 131-138, 449-458) - Component dictionary structures with all file paths

4. **`/Users/ishikapaliwal/ansible_collections/confluent/platform/roles/variables/defaults/main.yml`** - Variable defaults and naming conventions

5. **`/Users/ishikapaliwal/ansible_collections/confluent/platform/playbooks/validate_hosts.yml`** - System information collection patterns

---

## Verification Steps

### After Implementation:

1. **Run on test cluster**:
   ```bash
   ansible-playbook -i inventory.yml playbooks/support_bundle.yml
   ```

2. **Verify bundle created**:
   ```bash
   ls -lh support_bundle_*.tar.gz
   ```

3. **Extract and inspect**:
   ```bash
   tar -tzf support_bundle_*.tar.gz | head -20
   tar -xzf support_bundle_*.tar.gz
   cd support_bundle_*/
   ```

4. **Check manifests**:
   ```bash
   cat bundle_manifest.yml
   cat <hostname>/host_manifest.yml
   ```

5. **Verify no sensitive data**:
   ```bash
   # Should return empty or only metadata files
   find . -name "*.jks" -o -name "*.p12" -o -name "*.key"
   grep -r "password=" . | grep -v metadata
   ```

6. **Check file structure**:
   ```bash
   tree -L 3 .
   ```

7. **Test on different deployments**:
   - Package installation
   - Archive installation
   - SSL enabled
   - RBAC enabled
   - ZooKeeper mode
   - KRaft mode

8. **Test tag filtering**:
   ```bash
   ansible-playbook -i inventory.yml playbooks/support_bundle.yml --tags zookeeper
   ansible-playbook -i inventory.yml playbooks/support_bundle.yml --tags kafka_broker
   ```

9. **Test with custom output path**:
   ```bash
   ansible-playbook -i inventory.yml playbooks/support_bundle.yml -e support_bundle_output_path=/tmp
   ```

10. **Verify error handling** (simulate failures):
    - Stop a service before collection
    - Remove read permissions on a config file
    - Verify partial bundle still created

---

## Usage Examples

```bash
# Full support bundle
ansible-playbook -i inventory.yml playbooks/support_bundle.yml

# Specific component only
ansible-playbook -i inventory.yml playbooks/support_bundle.yml --tags kafka_broker

# Custom cluster name and output path
ansible-playbook -i inventory.yml playbooks/support_bundle.yml \
  -e support_bundle_cluster_name=production_kafka \
  -e support_bundle_output_path=/var/support_bundles

# Collect more journalctl lines
ansible-playbook -i inventory.yml playbooks/support_bundle.yml \
  -e support_bundle_journalctl_lines=5000

# Multiple components
ansible-playbook -i inventory.yml playbooks/support_bundle.yml \
  --tags zookeeper,kafka_broker,schema_registry
```

---

## Security Considerations

**Never Collect**:
- Private keys (`*.key`, PEM private keys)
- Keystore/truststore files (`*.jks`, `*.p12`, `*.pfx`)
- Password file contents
- JAAS file contents (may contain plaintext passwords)
- Environment variables containing passwords/secrets

**Always Sanitize**:
- Inventory files (remove password variables)
- Environment variables (filter out SECRET, PASSWORD, KEY, TOKEN)
- Command output containing credentials

**Metadata Only**:
- SSL certificate expiry dates, subjects, issuers
- File permissions and ownership
- File existence and sizes

---

## Out of Scope (Future Enhancements)

- Kafka-specific diagnostics (topics, consumer groups) - user requested to skip for now
- Bundle analysis/summary tool
- Direct upload to support portal
- Incremental bundle collection
- Bundle comparison tool
