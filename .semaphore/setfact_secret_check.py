"""
set_fact Secret Leak Sanity Check
Scans git diff for set_fact tasks in changed lines to prevent potential secret leakage.
"""

import os
import sys
import re
import subprocess


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
    # Constants
    SET_FACT_PATTERN = r'\bset_fact\s*:'
    YAML_EXTENSIONS = ('.yml', '.yaml')
    WARNING_MESSAGE = 'set_fact task found in changed lines - please verify no sensitive data is exposed'

    # Regex patterns
    HUNK_HEADER_PATTERN = re.compile(r'@@\s*-\d+(?:,\d+)?\s*\+(\d+)(?:,(\d+))?\s*@@')
    SET_FACT_REGEX = re.compile(SET_FACT_PATTERN)

    issues = []
    current_file = None
    new_file_line_number = 0

    for line in diff_content.split('\n'):
        # Detect new file in diff
        if line.startswith('diff --git'):
            current_file = _extract_filename_from_diff_header(line)
            new_file_line_number = 0
            continue

        # Parse hunk header to get starting line number in new file
        if line.startswith('@@'):
            new_file_line_number = _parse_hunk_header(line, HUNK_HEADER_PATTERN)
            continue

        # Process added lines
        if line.startswith('+') and not line.startswith('+++'):
            new_file_line_number += 1
            line_content = line[1:]  # Remove '+' prefix

            if _is_set_fact_in_yaml(current_file, line_content, YAML_EXTENSIONS, SET_FACT_REGEX):
                issues.append({
                    'file': current_file,
                    'line': new_file_line_number,
                    'content': line_content.strip(),
                    'message': WARNING_MESSAGE
                })
            continue

        # Handle context lines and empty lines (increment line counter for new file)
        if _is_context_line(line, new_file_line_number):
            new_file_line_number += 1
        # Removed lines (starting with '-') are ignored - they don't exist in new file

    return issues


def _extract_filename_from_diff_header(diff_line):
    """Extract filename from 'diff --git a/file.yml b/file.yml' format."""
    parts = diff_line.split()
    if len(parts) >= 4:
        return parts[3][2:]  # Remove "b/" prefix
    return None


def _parse_hunk_header(hunk_line, pattern):
    """
    Parse hunk header to get starting line number in new file.

    Example: '@@ -1,6 +1,10 @@' returns 0 (will be incremented to 1 before use)
    """
    match = pattern.search(hunk_line)
    if match:
        return int(match.group(1)) - 1  # Set to one less, will increment before processing
    return 0


def _is_set_fact_in_yaml(file_path, line_content, yaml_extensions, set_fact_pattern):
    """Check if line contains set_fact and file is a YAML file."""
    if not file_path:
        return False
    if not file_path.endswith(yaml_extensions):
        return False
    return set_fact_pattern.search(line_content) is not None


def _is_context_line(line, line_number):
    """Check if line is a context line (unchanged) or empty line within a hunk."""
    return line.startswith(' ') or (line == '' and line_number > 0)


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
