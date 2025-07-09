# Runs sanity and galaxy-importer checks on collection to ensure all the checks are met

set -ex

echo "Sanity + Galaxy-Importer Test Block"
echo "----------------"
echo "Python $PYTHON_VERSION"
echo "Ansible $ANSIBLE_VERSION"


cd $PATH_TO_CPA

version_gte() {
    # returns 0 if first arg version is greater than equal to second arg else returns 1

    local actual_ansi_version="$1"
    local min_allowed_ansi_version="$2"

    # Sort the versions in ascending order
    sorted_versions=$(printf "%s\n%s" "$actual_ansi_version" "$min_allowed_ansi_version" | sort -V)

    versions=($sorted_versions)
    # Split the sorted versions into an array

    if [[ "${versions[0]}" = "$min_allowed_ansi_version" ]]; then
        echo 0
        # actual ansible core version >= min allowed
    else
        echo 1
        # min core version allowed > actual ansible version
    fi
}

# This is very bad practice of grepping from yml files. Whenever someone will change the yml file significantly then this might break
MIN_ALLOWED_CORE_VERSION_LINE=$(cat meta/runtime.yml | grep 'requires_ansible:')
MIN_ALLOWED_CORE_VERSION=${MIN_ALLOWED_CORE_VERSION_LINE:21:4}
ANSI_CORE_VERSION_OKAY=$(version_gte $ANSIBLE_CORE_VERSION $MIN_ALLOWED_CORE_VERSION)
if [[ $ANSI_CORE_VERSION_OKAY -eq 1 ]]; then
    echo "Skipping this block as meta/runtime.yml specified minimum version is newer than this" >> $LOG_FILE
    exit
fi

sudo apt install -y shellcheck

pyenv install 3.8
pyenv local $PYTHON_VERSION 3.9 3.8 3.9 3.10 3.11 3.12 # This creates .python-version file which lists all these versions.
# 1st version in list will be the one coming from $PYTHON_VERSION and also become the default version of python
pip install wheel
pip install pylint
pip install "ansible==$ANSIBLE_VERSION"
pip install yamllint
pip install galaxy-importer
pip install setuptools

python --version
ansible --version

export PYTHON_INTERPRETER=$(which python)
echo $PYTHON_INTERPRETER

# Test1
export GALAXY_IMPORTER_CONFIG="$PATH_TO_CPA/galaxy-importer/galaxy-importer.cfg"
python -m galaxy_importer.main $ARTEFACT

# Test2
ansible-test sanity

# Test3 - Custom URI Authorization Check
echo "Running custom URI authorization sanity check..."
python3 << 'EOF'
import os
import sys
import glob
import yaml
import re

def get_all_yaml_files():
    """Get all YAML files in relevant directories."""
    collection_root = os.getcwd()

    # Find all YAML files in tasks and handlers directories
    patterns = [
        os.path.join(collection_root, 'roles', '*', 'tasks', '*.yml'),
        os.path.join(collection_root, 'roles', '*', 'handlers', '*.yml'),
        os.path.join(collection_root, 'playbooks', '*.yml'),
    ]

    all_files = []
    for pattern in patterns:
        all_files.extend(glob.glob(pattern))

    return all_files

def check_file_for_auth_issues(file_path):
    """Check a single YAML file for URI tasks with authorization issues."""
    issues = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse YAML content
        try:
            parsed_content = yaml.safe_load(content)
        except yaml.YAMLError as e:
            return issues

        if not parsed_content:
            return issues

        # Handle both single task and list of tasks
        tasks = parsed_content if isinstance(parsed_content, list) else [parsed_content]

        for i, task in enumerate(tasks):
            if not isinstance(task, dict):
                continue

            # Check if this is a URI task with authorization
            if is_uri_task_with_auth(task):
                if not has_no_log_protection(task):
                    task_name = task.get('name', f'Task {i+1}')
                    # Get line number from original content
                    line_number = get_task_line_number(content, task_name, i)

                    issues.append({
                        'file': file_path,
                        'task': task_name,
                        'line': line_number,
                        'message': 'URI task with authorization should have no_log: "{{mask_secrets|bool}}" to prevent credential exposure'
                    })

    except Exception as e:
        print(f"Warning: Could not parse {file_path}: {e}")

    return issues

def get_task_line_number(content, task_name, task_index):
    """Get approximate line number for a task."""
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if task_name and task_name in line and 'name:' in line:
            return i + 1
    return task_index + 1

def is_uri_task_with_auth(task):
    """Check if task is a URI request with authorization."""
    if 'uri' not in task:
        return False

    uri_params = task['uri']
    if not isinstance(uri_params, dict):
        return False

    # Check for various authorization parameters
    auth_indicators = [
        'url_username', 'url_password', 'force_basic_auth'
    ]

    for param in auth_indicators:
        if param in uri_params:
            return True

    # Check headers for authorization
    headers = uri_params.get('headers', {})
    if isinstance(headers, dict):
        for header_name in headers:
            if 'authorization' in header_name.lower() or 'auth' in header_name.lower():
                return True

    # Check for body containing credentials
    body = uri_params.get('body', '')
    if isinstance(body, str) and ('password' in body.lower() or 'token' in body.lower()):
        return True

    return False

def has_no_log_protection(task):
    """Check if task has no_log protection."""
    no_log = task.get('no_log', False)

    # Check for the recommended pattern
    if isinstance(no_log, str) and 'mask_secrets' in no_log:
        return True

    # Check for simple boolean true
    if no_log is True:
        return True

    return False

def main():
    """Main function to run the sanity check."""
    collection_root = os.getcwd()

    # Get all YAML files
    all_files = get_all_yaml_files()

    if not all_files:
        print("No YAML files found to check.")
        return 0

    all_issues = []

    for file_path in all_files:
        issues = check_file_for_auth_issues(file_path)
        all_issues.extend(issues)

    # Report results
    if all_issues:
        print("⚠️  URI Authorization Sanity Check Warnings:")
        print("=" * 60)
        for issue in all_issues:
            rel_path = os.path.relpath(issue['file'], collection_root)
            print(f"File: {rel_path}")
            print(f"Task: {issue['task']}")
            print(f"Line: ~{issue['line']}")
            print(f"Issue: {issue['message']}")
            print("-" * 60)

        print(f"\nTotal authorization issues found: {len(all_issues)}")
        print("These are warnings and will not fail the build.")
        return 0  # Don't fail the build, just warn
    else:
        print("✅ No URI authorization issues found!")
        return 0

if __name__ == '__main__':
    sys.exit(main())
EOF

echo "URI authorization sanity check completed."

# Test4 - Custom set_fact Secret Leak Check
echo "Running custom set_fact secret leak sanity check..."
python3 << 'EOF'
import os
import sys
import glob
import yaml
import re
import subprocess

def get_base_branch_from_galaxy():
    """Get base branch from galaxy.yml version information."""
    try:
        with open('galaxy.yml', 'r') as f:
            galaxy_content = yaml.safe_load(f)

        version = galaxy_content.get('version')

        # Extract major.minor version and replace patch with 'x'
        version_parts = version.split('.')
        if len(version_parts) >= 2:
            major_minor = f"{version_parts[0]}.{version_parts[1]}.x"
            return major_minor

        return version  # fallback to full version

    except Exception as e:
        print(f"Error: Could not read galaxy.yml: {e}")
        raise

def get_changed_files_and_lines():
    """Get files changed in the current PR and their changed line ranges."""
    try:
        # Get the base branch from galaxy.yml or environment
        base_branch = os.environ.get('BASE_BRANCH') or get_base_branch_from_galaxy()
        current_branch = os.environ.get('SEMAPHORE_GIT_PR_BRANCH', 'HEAD')

        print(f"Comparing {current_branch} against base branch: {base_branch}")

        # Get changed files
        result = subprocess.run(
            ['git', 'diff', '--name-only', f'origin/{base_branch}...{current_branch}'],
            capture_output=True, text=True, cwd=os.getcwd()
        )

        if result.returncode != 0:
            print("Warning: Could not get changed files")
            return {}

        changed_files = result.stdout.strip().split('\n')
        changed_files = [f for f in changed_files if f.endswith('.yml') or f.endswith('.yaml')]

        file_changes = {}
        for file_path in changed_files:
            if os.path.exists(file_path):
                # Get changed line numbers for this file
                diff_result = subprocess.run(
                    ['git', 'diff', '-U0', f'origin/{base_branch}...{current_branch}', file_path],
                    capture_output=True, text=True, cwd=os.getcwd()
                )

                if diff_result.returncode == 0:
                    changed_lines = parse_diff_lines(diff_result.stdout)
                    file_changes[file_path] = changed_lines

        return file_changes

    except Exception as e:
        print(f"Error: Could not get git diff: {e}")
        return {}

def parse_diff_lines(diff_output):
    """Parse git diff output to extract changed line numbers."""
    changed_lines = set()

    for line in diff_output.split('\n'):
        if line.startswith('@@'):
            # Parse hunk header: @@ -old_start,old_count +new_start,new_count @@
            match = re.search(r'@@\s*-\d+(?:,\d+)?\s*\+(\d+)(?:,(\d+))?\s*@@', line)
            if match:
                start = int(match.group(1))
                count = int(match.group(2)) if match.group(2) else 1
                changed_lines.update(range(start, start + count))

    return changed_lines

def check_file_for_setfact_issues(file_path, changed_lines=None):
    """Check a single YAML file for set_fact tasks that might leak secrets."""
    issues = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse YAML content
        try:
            parsed_content = yaml.safe_load(content)
        except yaml.YAMLError as e:
            return issues

        if not parsed_content:
            return issues

        # Handle both single task and list of tasks
        tasks = parsed_content if isinstance(parsed_content, list) else [parsed_content]

        for i, task in enumerate(tasks):
            if not isinstance(task, dict):
                continue

            # Check if this is a set_fact task
            if is_setfact_task(task):
                potential_secrets = check_for_potential_secrets(task)
                if potential_secrets:
                    task_name = task.get('name', f'Task {i+1}')
                    # Get line number from original content
                    line_number = get_task_line_number(content, task_name, i)

                    # If we have changed lines info, only report if this task is in changed lines
                    if changed_lines is None or any(abs(line_number - changed_line) <= 5 for changed_line in changed_lines):
                        issues.append({
                            'file': file_path,
                            'task': task_name,
                            'line': line_number,
                            'potential_secrets': potential_secrets,
                            'has_no_log': has_no_log_protection(task),
                            'message': 'set_fact task may contain secrets - please verify no sensitive data is exposed'
                        })

    except Exception as e:
        print(f"Warning: Could not parse {file_path}: {e}")

    return issues

def is_setfact_task(task):
    """Check if task is a set_fact task."""
    return 'set_fact' in task or 'ansible.builtin.set_fact' in task

def check_for_potential_secrets(task):
    """Check if set_fact task contains potential secrets."""
    potential_secrets = []

    # Get the set_fact content
    set_fact_content = task.get('set_fact', task.get('ansible.builtin.set_fact', {}))

    if not isinstance(set_fact_content, dict):
        return potential_secrets

    # Secret indicators to look for
    secret_indicators = [
        'password', 'passwd', 'pass', 'secret', 'key', 'token', 'auth',
        'credential', 'private', 'cert', 'keystore', 'truststore',
        'oauth', 'sasl', 'ldap', 'kerberos', 'ssl', 'tls'
    ]

    # Check variable names and values
    for var_name, var_value in set_fact_content.items():
        # Check variable name for secret indicators
        var_name_lower = var_name.lower()
        for indicator in secret_indicators:
            if indicator in var_name_lower:
                potential_secrets.append(f"Variable name '{var_name}' contains '{indicator}'")
                break

        # Check variable value for secret patterns (if it's a string)
        if isinstance(var_value, str):
            var_value_lower = var_value.lower()
            for indicator in secret_indicators:
                if indicator in var_value_lower:
                    potential_secrets.append(f"Variable '{var_name}' value contains '{indicator}'")
                    break

            # Check for common secret patterns
            if re.search(r'[A-Za-z0-9+/]{20,}={0,2}', var_value):  # Base64-like patterns
                potential_secrets.append(f"Variable '{var_name}' contains base64-like pattern")

            if re.search(r'[a-fA-F0-9]{32,}', var_value):  # Hex patterns (32+ chars)
                potential_secrets.append(f"Variable '{var_name}' contains hex pattern")

    return potential_secrets

def get_task_line_number(content, task_name, task_index):
    """Get approximate line number for a task."""
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if task_name and task_name in line and 'name:' in line:
            return i + 1
    return task_index + 1

def has_no_log_protection(task):
    """Check if task has no_log protection."""
    no_log = task.get('no_log', False)

    # Check for the recommended pattern
    if isinstance(no_log, str) and 'mask_secrets' in no_log:
        return True

    # Check for simple boolean true
    if no_log is True:
        return True

    return False

def main():
    """Main function to run the set_fact sanity check."""
    collection_root = os.getcwd()

    # Get changed files and lines from git diff
    changed_files = get_changed_files_and_lines()

    if not changed_files:
        print("No YAML files changed in this PR or could not determine changes.")
        return 0

    all_issues = []

    for file_path, changed_lines in changed_files.items():
        if os.path.exists(file_path):
            issues = check_file_for_setfact_issues(file_path, changed_lines)
            all_issues.extend(issues)

    # Report results
    if all_issues:
        print("⚠️  set_fact Secret Leak Sanity Check Warnings (Changed Files Only):")
        print("=" * 60)
        for issue in all_issues:
            rel_path = os.path.relpath(issue['file'], collection_root)
            print(f"File: {rel_path}")
            print(f"Task: {issue['task']}")
            print(f"Line: ~{issue['line']}")
            print(f"Issue: {issue['message']}")
            print(f"No Log Protection: {'✅ Yes' if issue['has_no_log'] else '❌ No'}")
            print("Potential Secret Indicators:")
            for secret in issue['potential_secrets']:
                print(f"  - {secret}")
            print("-" * 60)

        print(f"\nTotal set_fact issues found in changed files: {len(all_issues)}")
        print("⚠️  IMPORTANT: Please manually verify these set_fact tasks do not leak sensitive information!")
        print("   Consider adding 'no_log: \"{{mask_secrets|bool}}\"' if they handle secrets.")
        print("   These are warnings and will not fail the build.")
        return 0  # Don't fail the build, just warn
    else:
        print("✅ No set_fact secret leak issues found in changed files!")
        return 0

if __name__ == '__main__':
    sys.exit(main())
EOF

echo "set_fact secret leak sanity check completed."