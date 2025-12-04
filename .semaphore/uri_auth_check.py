"""
URI Authorization Sanity Check
Scans YAML files for URI tasks with authorization that lack proper no_log protection.
"""

import os
import sys
import glob
import yaml


# Constants
YAML_FILE_PATTERNS = [
    ('roles', '*', 'tasks', '*.yml'),
    ('roles', '*', 'handlers', '*.yml'),
    ('playbooks', '*.yml'),
]
AUTH_HEADER_KEYWORDS = ['authorization']
CREDENTIAL_KEYWORDS = ['password', 'token']
TASK_MODULE_INDICATORS = ['name', 'debug', 'set_fact', 'include_role', 'import_role']
WARNING_MESSAGE = 'URI task with authorization should have no_log: true to prevent credential exposure'


def get_all_yaml_files(collection_root):
    """Get all YAML files in relevant directories (roles, playbooks)."""
    all_files = []
    for pattern_parts in YAML_FILE_PATTERNS:
        pattern = os.path.join(collection_root, *pattern_parts)
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

    # Check headers dict for authorization
    # Note: Authorization must be in headers dict, not a direct parameter
    if _has_auth_in_headers(uri_params.get('headers', {})):
        return True

    # Check request body for credentials
    if _has_credentials_in_body(uri_params.get('body', '')):
        return True

    return False


def _has_auth_in_headers(headers):
    """Check if headers dict contains authorization-related headers."""
    if not isinstance(headers, dict):
        return False
    for header_name in headers:
        header_lower = header_name.lower()
        if any(keyword in header_lower for keyword in AUTH_HEADER_KEYWORDS):
            return True
    return False


def _has_credentials_in_body(body):
    """Check if request body contains credential-related keywords."""
    if not isinstance(body, str):
        return False
    body_lower = body.lower()
    return any(keyword in body_lower for keyword in CREDENTIAL_KEYWORDS)


def has_no_log_protection(task):
    """
    Check if a task has proper no_log protection.

    Accepts both 'no_log: true' and string patterns containing 'mask_secrets'.
    """
    no_log = task.get('no_log', False)

    # Boolean true
    if no_log is True:
        return True

    # String 'true' (case-insensitive)
    if isinstance(no_log, str):
        if no_log.lower() == 'true':
            return True
        # Check for mask_secrets pattern
        if 'mask_secrets' in no_log:
            return True

    return False


def get_task_line_number(content, task_name, task_index, occurrence=1):
    """
    Get approximate line number for a task in the file content.

    Args:
        content: File content as string
        task_name: Name of the task
        task_index: Index of task in the tasks list (fallback)
        occurrence: Which occurrence of this task name to find (1-based)

    Returns:
        Line number (1-based) where the task is found
    """
    if not task_name:
        return task_index + 1

    lines = content.split('\n')
    found_count = 0

    for i, line in enumerate(lines):
        if task_name in line and 'name:' in line:
            found_count += 1
            if found_count == occurrence:
                return i + 1

    # Fallback: if we couldn't find the Nth occurrence, return index-based estimate
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

        # Extract tasks from parsed content
        # Handle both playbooks (list of plays with 'tasks' key) and role task files (list of tasks)
        all_tasks = _extract_tasks_from_yaml(parsed_content)

        # Check each task for URI authorization issues
        # First pass: count all tasks with each name to determine occurrence numbers
        task_name_to_indices = {}
        for i, task in enumerate(all_tasks):
            if isinstance(task, dict):
                task_name = task.get('name', '')
                if task_name:
                    if task_name not in task_name_to_indices:
                        task_name_to_indices[task_name] = []
                    task_name_to_indices[task_name].append(i)

        # Track which occurrence we're processing for tasks with authorization issues
        task_name_processed_counts = {}

        for i, task in enumerate(all_tasks):
            if not isinstance(task, dict):
                continue

            # Check for URI task with auth but no logging protection
            if is_uri_task_with_auth(task) and not has_no_log_protection(task):
                task_name = task.get('name', f'Task {i + 1}')
                # Find which occurrence this is among all tasks with this name
                if task_name in task_name_to_indices:
                    # Find the position of current index in the list of all indices for this name
                    occurrence = task_name_to_indices[task_name].index(i) + 1
                else:
                    occurrence = 1
                line_number = get_task_line_number(content, task_name, i, occurrence)

                issues.append({
                    'file': file_path,
                    'task': task_name,
                    'line': line_number,
                    'message': WARNING_MESSAGE
                })

    except Exception as e:
        print(f"Warning: Could not parse {file_path}: {e}")

    return issues


def _extract_tasks_from_yaml(parsed_content):
    """
    Extract tasks from YAML content.

    Handles multiple formats:
    - Playbooks: list of plays, each with a 'tasks' key
    - Role task files: list of tasks directly
    - Single play or single task
    - Nested tasks in blocks (block, rescue, always)
    """
    all_tasks = []

    if isinstance(parsed_content, list):
        for item in parsed_content:
            if isinstance(item, dict):
                if _is_play(item):
                    # Extract tasks from play
                    tasks = item.get('tasks', [])
                    if isinstance(tasks, list):
                        all_tasks.extend(_extract_tasks_from_list(tasks))
                elif _is_task(item):
                    # Direct task (role task file format)
                    all_tasks.extend(_extract_tasks_from_task(item))
    elif isinstance(parsed_content, dict):
        if _is_play(parsed_content):
            # Single play
            tasks = parsed_content.get('tasks', [])
            if isinstance(tasks, list):
                all_tasks.extend(_extract_tasks_from_list(tasks))
        else:
            # Single task
            all_tasks.extend(_extract_tasks_from_task(parsed_content))

    return all_tasks


def _extract_tasks_from_list(tasks):
    """Extract all tasks from a list, handling nested blocks."""
    all_tasks = []
    for task in tasks:
        if isinstance(task, dict):
            all_tasks.extend(_extract_tasks_from_task(task))
    return all_tasks


def _extract_tasks_from_task(task):
    """
    Extract tasks from a single task item.

    Handles nested structures at any depth:
    - block: list of tasks (supports arbitrary nesting)
    - rescue: list of tasks (supports arbitrary nesting)
    - always: list of tasks (supports arbitrary nesting)
    - Direct task (no nesting)

    This function recursively processes nested blocks, so it handles
    blocks within blocks at any level of nesting.
    """
    tasks = []

    # Check for nested block structures
    for block_key in ['block', 'rescue', 'always']:
        if block_key in task:
            block_tasks = task[block_key]
            if isinstance(block_tasks, list):
                # Recursively extract tasks from nested blocks (handles any depth)
                for nested_task in block_tasks:
                    if isinstance(nested_task, dict):
                        tasks.extend(_extract_tasks_from_task(nested_task))

    # If this is a direct task (not just a block wrapper), add it
    # Check if it has task-like properties and isn't just a block wrapper
    has_block_structure = 'block' in task or 'rescue' in task or 'always' in task

    if _is_task(task) and not has_block_structure:
        # It's a direct task without block structure
        tasks.append(task)
    # If it has block/rescue/always, we've already extracted nested tasks above
    # Don't add the wrapper itself as a task

    return tasks


def _is_play(item):
    """Check if a dict represents an Ansible play (has 'tasks' key)."""
    return isinstance(item, dict) and 'tasks' in item


def _is_task(item):
    """Check if a dict represents an Ansible task (has module indicators)."""
    if not isinstance(item, dict):
        return False
    # Check for URI module or common task indicators
    return 'uri' in item or any(key in item for key in TASK_MODULE_INDICATORS)


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
