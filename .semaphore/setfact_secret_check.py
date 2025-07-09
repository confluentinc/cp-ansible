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


def get_changed_files_and_content():
    """Get files changed in the current PR and their actual changed content."""
    try:
        # Get the base branch from galaxy.yml or environment
        base_branch = os.environ.get('BASE_BRANCH') or get_base_branch_from_galaxy()
        current_branch = os.environ.get('SEMAPHORE_GIT_PR_BRANCH', 'HEAD')
        collection_root = os.environ.get('PATH_TO_CPA', os.getcwd())

        print(f"Comparing {current_branch} against base branch: {base_branch}")
        print(f"Working directory: {collection_root}")

        # First, fetch all remote branches with their history
        print("Fetching remote branches...")
        fetch_result = subprocess.run(
            ['git', 'fetch', 'origin', '+refs/heads/*:refs/remotes/origin/*'],
            capture_output=True, text=True, cwd=collection_root, check=False
        )

        if fetch_result.returncode != 0:
            print(f"Warning: Could not fetch branches: {fetch_result.stderr}")
            subprocess.run(
                ['git', 'fetch', 'origin'],
                capture_output=True, text=True, cwd=collection_root, check=False
            )

        # Check if base branch exists
        branch_check = subprocess.run(
            ['git', 'rev-parse', f'origin/{base_branch}'],
            capture_output=True, text=True, cwd=collection_root, check=False
        )

        if branch_check.returncode != 0:
            print(f"Base branch origin/{base_branch} not found, trying alternatives...")
            for alt_branch in ['main', 'master', 'develop']:
                alt_check = subprocess.run(
                    ['git', 'rev-parse', f'origin/{alt_branch}'],
                    capture_output=True, text=True, cwd=collection_root, check=False
                )
                if alt_check.returncode == 0:
                    base_branch = alt_branch
                    print(f"Using alternative base branch: {base_branch}")
                    break
            else:
                print("No valid base branch found, using HEAD~1 as fallback")
                base_branch = None

        # Get the diff content directly
        if base_branch:
            git_commands = [
                ['git', 'diff', f'origin/{base_branch}...HEAD'],
                ['git', 'diff', f'origin/{base_branch}', 'HEAD'],
                ['git', 'diff', f'origin/{base_branch}..HEAD']
            ]
        else:
            git_commands = [
                ['git', 'diff', 'HEAD~1...HEAD'],
                ['git', 'diff', 'HEAD~5...HEAD']
            ]

        diff_content = None
        for cmd in git_commands:
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=collection_root, check=False
            )
            if result.returncode == 0:
                print(f"Successfully got diff using: {' '.join(cmd)}")
                diff_content = result.stdout
                break
            else:
                print(f"Failed command: {' '.join(cmd)}")

        if not diff_content:
            print("Error: Could not get diff content")
            return {}

        return parse_diff_for_setfact(diff_content)

    except Exception as e:
        print(f"Error: Could not get git diff: {e}")
        return {}


def parse_diff_for_setfact(diff_content):
    """Parse git diff output to find set_fact usage in changed lines."""
    issues = []
    current_file = None
    line_number = 0
    
    for line in diff_content.split('\n'):
        # Track which file we're looking at
        if line.startswith('diff --git'):
            # Extract filename from "diff --git a/path/file.yml b/path/file.yml"
            parts = line.split()
            if len(parts) >= 4:
                current_file = parts[3][2:]  # Remove "b/" prefix
        
        elif line.startswith('@@'):
            # Parse hunk header to get line number: @@ -old_start,old_count +new_start,new_count @@
            match = re.search(r'@@\s*-\d+(?:,\d+)?\s*\+(\d+)(?:,(\d+))?\s*@@', line)
            if match:
                line_number = int(match.group(1)) - 1  # -1 because we'll increment before checking
        
        elif line.startswith('+') and not line.startswith('+++'):
            # This is an added line
            line_number += 1
            line_content = line[1:]  # Remove the '+' prefix
            
            # Check if this line contains set_fact
            if current_file and current_file.endswith(('.yml', '.yaml')):
                if 'set_fact:' in line_content or 'ansible.builtin.set_fact:' in line_content:
                    issues.append({
                        'file': current_file,
                        'line': line_number,
                        'content': line_content.strip(),
                        'message': 'set_fact task found in changed lines - please verify no sensitive data is exposed'
                    })
        
        elif not line.startswith('-'):
            # Context line or other line that affects line numbering
            if line_number > 0:  # Only increment if we're tracking line numbers
                line_number += 1

    return issues


def main():
    """Main function to run the set_fact sanity check."""
    collection_root = os.environ.get('PATH_TO_CPA', os.getcwd())

    # Get changed content from git diff
    issues = get_changed_files_and_content()

    if not issues:
        print("No set_fact tasks found in changed lines.")
        return 0

    print(f"Found {len(issues)} set_fact tasks in changed lines:")
    print("=" * 60)
    
    for issue in issues:
        print(f"File: {issue['file']}")
        print(f"Line: ~{issue['line']}")
        print(f"Content: {issue['content']}")
        print(f"Issue: {issue['message']}")
        print("-" * 60)

    print("⚠️  IMPORTANT: Please manually verify these set_fact tasks do not leak sensitive information!")
    print("   Consider adding 'no_log: true' if they handle secrets.")
    print("   These are warnings and will not fail the build.")
    return 0  # Don't fail the build, just warn


if __name__ == '__main__':
    sys.exit(main())
