"""
URI Authorization Sanity Check
Scans YAML files for URI tasks with authorization that lack proper no_log protection.
"""

import os
import sys
import glob
import yaml


def get_all_yaml_files(collection_root):
    """Get all YAML files in relevant directories (roles, playbooks)."""
    patterns = [
        os.path.join(collection_root, 'roles', '*', 'tasks', '*.yml'),
        os.path.join(collection_root, 'roles', '*', 'handlers', '*.yml'),
        os.path.join(collection_root, 'playbooks', '*.yml'),
    ]

    all_files = []
    for pattern in patterns:
        all_files.extend(glob.glob(pattern))

    return all_files


def is_uri_task_with_auth(task):
    """
    Check if a task is a URI request with authorization parameters.

    Returns True if the task uses URI module with any authentication method.
    """
    if not isinstance(task, dict) or 'uri' not in task:
        return False

    uri_params = task['uri']
    if not isinstance(uri_params, dict):
        return False

    # Check for direct authentication parameters
    auth_params = ['url_username', 'url_password', 'force_basic_auth']
    if any(param in uri_params for param in auth_params):
        return True

    # Check headers for authorization
    headers = uri_params.get('headers', {})
    if isinstance(headers, dict):
        for header_name in headers:
            if 'authorization' in header_name.lower() or 'auth' in header_name.lower():
                return True

    # Check for credentials in request body
    body = uri_params.get('body', '')
    if isinstance(body, str):
        body_lower = body.lower()
        if 'password' in body_lower or 'token' in body_lower:
            return True

    return False


def has_no_log_protection(task):
    """
    Check if a task has proper no_log protection.

    Accepts both 'no_log: true' and string patterns containing 'mask_secrets'.
    """
    no_log = task.get('no_log', False)

    # Check for mask_secrets pattern
    if isinstance(no_log, str) and 'mask_secrets' in no_log:
        return True

    # Check for boolean true (case-insensitive string handling)
    if no_log is True:
        return True

    if isinstance(no_log, str) and no_log.lower() == 'true':
        return True

    return False


def get_task_line_number(content, task_name, task_index):
    """Get approximate line number for a task in the file content."""
    if not task_name:
        return task_index + 1

    lines = content.split('\n')
    for i, line in enumerate(lines):
        if task_name in line and 'name:' in line:
            return i + 1

    return task_index + 1


def check_file_for_auth_issues(file_path):
    """
    Check a single YAML file for URI tasks with authorization issues.

    Returns list of issues in the format:
    [{'file': str, 'task': str, 'line': int, 'message': str}, ...]
    """
    issues = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse YAML content
        try:
            parsed_content = yaml.safe_load(content)
        except yaml.YAMLError:
            return issues  # Skip files with YAML errors

        if not parsed_content:
            return issues

        # Ensure we have a list of tasks
        tasks = parsed_content if isinstance(parsed_content, list) else [parsed_content]

        for i, task in enumerate(tasks):
            if not isinstance(task, dict):
                continue

            # Check for URI task with auth but no logging protection
            if is_uri_task_with_auth(task) and not has_no_log_protection(task):
                task_name = task.get('name', f'Task {i + 1}')
                line_number = get_task_line_number(content, task_name, i)

                issues.append({
                    'file': file_path,
                    'task': task_name,
                    'line': line_number,
                    'message': 'URI task with authorization should have no_log: true to prevent credential exposure'
                })

    except Exception as e:
        print(f"Warning: Could not parse {file_path}: {e}")

    return issues


def main():
    """Main function to run the URI authorization sanity check."""
    collection_root = os.environ.get('PATH_TO_CPA', os.getcwd())

    try:
        # Get all YAML files to check
        all_files = get_all_yaml_files(collection_root)

        if not all_files:
            print("No YAML files found to check.")
            return 0

        print(f"Checking {len(all_files)} YAML files for URI authorization issues...")

        # Check each file for issues
        all_issues = []
        for file_path in all_files:
            issues = check_file_for_auth_issues(file_path)
            all_issues.extend(issues)

        # Report results
        if all_issues:
            print("❌ URI Authorization Sanity Check FAILED:")
            print("=" * 60)

            for issue in all_issues:
                rel_path = os.path.relpath(issue['file'], collection_root)
                print(f"File: {rel_path}")
                print(f"Task: {issue['task']}")
                print(f"Line: ~{issue['line']}")
                print(f"Issue: {issue['message']}")
                print("-" * 40)

            print(f"\n❌ Found {len(all_issues)} authorization issues that must be fixed.")
            print("   Add 'no_log: true' to prevent credential exposure in logs.")

            return 1  # Fail the build
        else:
            print("✅ No URI authorization issues found!")
            return 0

    except Exception as e:
        print(f"Error during URI authorization check: {e}")
        return 1  # Fail on script errors for security checks


if __name__ == '__main__':
    sys.exit(main())
