"""
set_fact Secret Leak Sanity Check
Checks for set_fact tasks that might leak secrets in changed files.
"""

import os
import sys
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
        collection_root = os.environ.get('PATH_TO_CPA', os.getcwd())

        print(f"Comparing {current_branch} against base branch: {base_branch}")
        print(f"Working directory: {collection_root}")

        # Check if we're in a shallow clone and unshallow if needed
        shallow_check = subprocess.run(
            ['git', 'rev-parse', '--is-shallow-repository'],
            capture_output=True, text=True, cwd=collection_root, check=False
        )

        if shallow_check.returncode == 0 and shallow_check.stdout.strip() == 'true':
            print("Repository is shallow, attempting to unshallow...")
            subprocess.run(
                ['git', 'fetch', '--unshallow'],
                capture_output=True, text=True, cwd=collection_root, check=False
            )

        # Try to fetch all branches to get the base branch
        fetch_all_result = subprocess.run(
            ['git', 'fetch', 'origin'],
            capture_output=True, text=True, cwd=collection_root, check=False
        )

        if fetch_all_result.returncode == 0:
            print("Successfully fetched all branches")

        # Get changed files - try multiple approaches with better fallbacks
        git_commands = [
            ['git', 'diff', '--name-only', f'origin/{base_branch}...HEAD'],
            ['git', 'diff', '--name-only', f'origin/{base_branch}..HEAD'],
            ['git', 'diff', '--name-only', 'origin/main...HEAD'],
            ['git', 'diff', '--name-only', 'origin/master...HEAD'],
            ['git', 'diff', '--name-only', 'HEAD~1...HEAD'],
            ['git', 'diff', '--name-only', 'HEAD~5...HEAD'],
            ['git', 'diff', '--name-only', 'HEAD~10...HEAD'],
            ['git', 'diff', '--name-only', '--diff-filter=AM', 'HEAD~1...HEAD'],  # Added/Modified files only
            ['git', 'show', '--name-only', '--pretty=format:', 'HEAD'],  # Files in current commit
            ['git', 'ls-files', '*.yml', '*.yaml']  # Final fallback - all YAML files
        ]

        result = None
        for cmd in git_commands:
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=collection_root, check=False
            )
            if result.returncode == 0 and result.stdout.strip():
                print(f"Successfully got files using: {' '.join(cmd)}")
                break
            else:
                print(f"Failed command: {' '.join(cmd)}")
                if result.stderr:
                    print(f"Error: {result.stderr.strip()}")

        if not result or result.returncode != 0:
            print("Warning: Could not get changed files with any method")
            return {}

        changed_files = result.stdout.strip().split('\n')
        changed_files = [f.strip() for f in changed_files if f.strip() and f.strip().endswith(('.yml', '.yaml'))]

        if not changed_files:
            print("No YAML files found in changes, falling back to check roles directory")
            # Final fallback: check for YAML files in roles directory
            roles_result = subprocess.run(
                ['find', 'roles', '-name', '*.yml', '-o', '-name', '*.yaml'],
                capture_output=True, text=True, cwd=collection_root, check=False
            )
            if roles_result.returncode == 0:
                changed_files = [f.strip() for f in roles_result.stdout.strip().split('\n') if f.strip()]
                if changed_files:
                    print(f"Found {len(changed_files)} YAML files in roles directory")

        if not changed_files:
            print("No YAML files found")
            return {}

        print(f"Found {len(changed_files)} YAML files to check")

        file_changes = {}
        for file_path in changed_files:
            full_path = os.path.join(collection_root, file_path) if not os.path.isabs(file_path) else file_path
            if os.path.exists(full_path):
                # For line-level changes, just assume whole file if we can't get diff
                file_changes[full_path] = set()

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
                task_name = task.get('name', f'Task {i + 1}')
                # Get line number from original content
                line_number = get_task_line_number(content, task_name, i)

                # If we have changed lines info, only report if this task is in changed lines
                if changed_lines is None or any(abs(line_number - changed_line) <= 5 for changed_line in changed_lines):
                    issues.append({
                        'file': file_path,
                        'task': task_name,
                        'line': line_number,
                        'has_no_log': has_no_log_protection(task),
                        'message': 'set_fact task found - please verify no sensitive data is exposed and consider adding no_log if needed'
                    })

    except Exception as e:
        print(f"Warning: Could not parse {file_path}: {e}")

    return issues


def is_setfact_task(task):
    """Check if task is a set_fact task."""
    return 'set_fact' in task or 'ansible.builtin.set_fact' in task


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
    collection_root = os.environ.get('PATH_TO_CPA', os.getcwd())

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
        print("⚠️  set_fact Usage Warnings (Changed Files Only):")
        print("=" * 60)
        for issue in all_issues:
            rel_path = os.path.relpath(issue['file'], collection_root)
            print(f"File: {rel_path}")
            print(f"Task: {issue['task']}")
            print(f"Line: ~{issue['line']}")
            print(f"Issue: {issue['message']}")
            print(f"No Log Protection: {'✅ Yes' if issue['has_no_log'] else '❌ No'}")
            print("-" * 60)

        print(f"\nTotal set_fact tasks found in changed files: {len(all_issues)}")
        print("⚠️  IMPORTANT: Please manually verify these set_fact tasks do not leak sensitive information!")
        print("   Consider adding 'no_log: true' if they handle secrets.")
        print("   These are warnings and will not fail the build.")
        return 0  # Don't fail the build, just warn
    else:
        print("✅ No set_fact tasks found in changed files!")
        return 0


if __name__ == '__main__':
    sys.exit(main())
