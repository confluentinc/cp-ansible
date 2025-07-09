#!/usr/bin/python
"""
URI Authorization Sanity Check
Checks for URI tasks with authorization that lack no_log protection.
"""

import os
import sys
import glob
import yaml
import re


def get_all_yaml_files(collection_root):
    """Get all YAML files in relevant directories."""
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
        'Authorization'
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

    # Check for simple boolean true (case-insensitive)
    if no_log is True:
        return True

    # Check for string representations of true (case-insensitive)
    if isinstance(no_log, str) and no_log.lower() == 'true':
        return True

    return False


def main():
    """Main function to run the sanity check."""
    collection_root = os.environ.get('PATH_TO_CPA', os.getcwd())

    # Get all YAML files
    all_files = get_all_yaml_files(collection_root)

    if not all_files:
        print("No YAML files found to check.")
        return 0

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
            print("-" * 60)

        print(f"\nTotal authorization issues found: {len(all_issues)}")
        print("❌ These issues must be fixed before the build can pass.")
        return 1  # Fail the build
    else:
        print("✅ No URI authorization issues found!")
        return 0


if __name__ == '__main__':
    sys.exit(main())
