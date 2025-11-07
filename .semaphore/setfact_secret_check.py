"""
set_fact Secret Leak Sanity Check
Scans git diff for set_fact tasks in changed lines to prevent potential secret leakage.
"""

import os
import sys
import re
import subprocess
import yaml


def get_git_diff(base_branch, feature_branch, collection_root):
    """Get the git diff content for analysis."""
    print(f"Comparing {feature_branch} against base branch: {base_branch}")

    # Fetch the base branch since SemaphoreCI uses --single-branch clone
    print(f"Fetching base branch {base_branch}...")
    fetch_result = subprocess.run(
        ['git', 'fetch', 'origin', f'{base_branch}:refs/remotes/origin/{base_branch}'],
        capture_output=True, text=True, cwd=collection_root, check=False
    )
    if fetch_result.returncode != 0:
        print(f"Warning: Failed to fetch base branch: {fetch_result.stderr}")

    # Now try the diff command
    cmd = ['git', 'diff', f'origin/{base_branch}...origin/{feature_branch}']
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=collection_root, check=False)

    if result.returncode == 0 and result.stdout.strip():
        print(f"Successfully got diff using: {' '.join(cmd)}")
        return result.stdout

    print(f"Failed to get diff: {' '.join(cmd)}")
    if result.stderr:
        print(f"Error: {result.stderr}")
    return None


def parse_diff_for_setfact(diff_content):
    """
    Parse git diff to find set_fact usage in added/modified lines.

    Returns list of issues found in the format:
    [{'file': str, 'line': int, 'content': str, 'message': str}, ...]
    """
    issues = []
    current_file = None
    line_number = 0

    for line in diff_content.split('\n'):
        if line.startswith('diff --git'):
            # Extract target filename: "diff --git a/file.yml b/file.yml"
            parts = line.split()
            if len(parts) >= 4:
                current_file = parts[3][2:]  # Remove "b/" prefix
                line_number = 0

        elif line.startswith('@@'):
            # Parse hunk header: @@ -old_start,old_count +new_start,new_count @@
            match = re.search(r'@@\s*-\d+(?:,\d+)?\s*\+(\d+)(?:,(\d+))?\s*@@', line)
            if match:
                line_number = int(match.group(1)) - 1  # Will increment before checking

        elif line.startswith('+') and not line.startswith('+++'):
            # Added line - check for set_fact usage
            line_number += 1
            line_content = line[1:]  # Remove '+' prefix

            set_fact_pattern = r'\bset_fact\s*:'
            if (current_file and current_file.endswith(('.yml', '.yaml')) and re.search(set_fact_pattern, line_content)):

                issues.append({
                    'file': current_file,
                    'line': line_number,
                    'content': line_content.strip(),
                    'message': 'set_fact task found in changed lines - please verify no sensitive data is exposed'
                })

        elif not line.startswith('-') and line_number > 0:
            # Context line - increment line counter
            line_number += 1

    return issues


def main():
    """Main function to run the set_fact sanity check."""
    collection_root = os.environ.get('PATH_TO_CPA', os.getcwd())

    try:
        # Get branches from SemaphoreCI environment variables
        feature_branch = os.environ.get('SEMAPHORE_GIT_PR_BRANCH', 'HEAD')
        base_branch = os.environ.get('SEMAPHORE_GIT_PR_BASE_BRANCH') or os.environ.get('SEMAPHORE_GIT_BRANCH', 'main')

        # Get and parse git diff
        diff_content = get_git_diff(base_branch, feature_branch, collection_root)

        if not diff_content:
            print("Error: Could not retrieve git diff")
            return 1  # Fail if we can't get the diff - the check didn't run

        issues = parse_diff_for_setfact(diff_content)

        # Report results
        if not issues:
            print("✅ No set_fact tasks found in changed lines.")
            return 0

        print(f"⚠️  Found {len(issues)} set_fact tasks in changed lines:")
        print("=" * 60)

        for issue in issues:
            print(f"File: {issue['file']}")
            print(f"Line: ~{issue['line']}")
            print(f"Content: {issue['content']}")
            print(f"Issue: {issue['message']}")
            print("-" * 40)

        print("\n⚠️  IMPORTANT: Please manually verify these set_fact tasks do not leak sensitive information!")
        print("   Consider adding 'no_log: true' if not already added and if they handle secrets.")
        print("   These are warnings and will not fail the build.")

        return 0  # Don't fail the build, just warn

    except Exception as e:
        print(f"Error during set_fact check: {e}")
        import traceback
        traceback.print_exc()
        return 1  # Fail the build


if __name__ == '__main__':
    sys.exit(main())
