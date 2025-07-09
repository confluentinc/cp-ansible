"""
set_fact Secret Leak Sanity Check
Scans git diff for set_fact tasks in changed lines to prevent potential secret leakage.
"""

import os
import sys
import re
import subprocess
import yaml


def get_base_branch():
    """Determine the base branch for comparison."""
    # Priority: Environment variable > galaxy.yml version > fallback
    base_branch = os.environ.get('BASE_BRANCH')
    if base_branch:
        return base_branch
    
    try:
        with open('galaxy.yml', 'r') as f:
            galaxy_content = yaml.safe_load(f)
        
        version = galaxy_content.get('version', '')
        version_parts = version.split('.')
        
        if len(version_parts) >= 2:
            return f"{version_parts[0]}.{version_parts[1]}.x"
        
        return version
    except Exception as e:
        print(f"Warning: Could not read galaxy.yml: {e}")
        return None


def fetch_remote_branches(collection_root):
    """Fetch remote branches to ensure we have the latest refs."""
    print("Fetching remote branches...")
    
    # Try comprehensive fetch first, then basic fetch as fallback
    fetch_commands = [
        ['git', 'fetch', 'origin', '+refs/heads/*:refs/remotes/origin/*'],
        ['git', 'fetch', 'origin']
    ]
    
    for cmd in fetch_commands:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=collection_root, check=False)
        if result.returncode == 0:
            return True
    
    print("Warning: Could not fetch remote branches")
    return False


def find_valid_base_branch(base_branch, collection_root):
    """Find a valid base branch that exists in the repository."""
    # First try the suggested base branch
    if base_branch:
        result = subprocess.run(
            ['git', 'rev-parse', f'origin/{base_branch}'],
            capture_output=True, text=True, cwd=collection_root, check=False
        )
        if result.returncode == 0:
            print(f"Using base branch: {base_branch}")
            return base_branch
    
    # Try common fallback branches
    fallback_branches = ['main', 'master', 'develop']
    for branch in fallback_branches:
        result = subprocess.run(
            ['git', 'rev-parse', f'origin/{branch}'],
            capture_output=True, text=True, cwd=collection_root, check=False
        )
        if result.returncode == 0:
            print(f"Using fallback base branch: {branch}")
            return branch
    
    print("No valid base branch found")
    return None


def get_git_diff(base_branch, collection_root):
    """Get the git diff content for analysis."""
    current_branch = os.environ.get('SEMAPHORE_GIT_PR_BRANCH', 'HEAD')
    print(f"Comparing {current_branch} against base branch: {base_branch}")
    
    # Build command list based on available base branch
    if base_branch:
        commands = [
            ['git', 'diff', f'origin/{base_branch}...HEAD'],
            ['git', 'diff', f'origin/{base_branch}', 'HEAD'],
            ['git', 'diff', f'origin/{base_branch}..HEAD']
        ]
    else:
        commands = [
            ['git', 'diff', 'HEAD~1...HEAD'],
            ['git', 'diff', 'HEAD~5...HEAD']
        ]
    
    # Try each command until one succeeds
    for cmd in commands:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=collection_root, check=False)
        if result.returncode == 0:
            print(f"Successfully got diff using: {' '.join(cmd)}")
            return result.stdout
        print(f"Failed command: {' '.join(cmd)}")
    
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
            
            if (current_file and 
                current_file.endswith(('.yml', '.yaml')) and
                ('set_fact:' in line_content or 'ansible.builtin.set_fact:' in line_content)):
                
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
        # Get base branch and fetch remote refs
        base_branch = get_base_branch()
        fetch_remote_branches(collection_root)
        valid_base_branch = find_valid_base_branch(base_branch, collection_root)
        
        # Get and parse git diff
        diff_content = get_git_diff(valid_base_branch, collection_root)
        if not diff_content:
            print("Error: Could not retrieve git diff")
            return 0
        
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
        print("   Consider adding 'no_log: true' if they handle secrets.")
        print("   These are warnings and will not fail the build.")
        
        return 0  # Don't fail the build, just warn
    
    except Exception as e:
        print(f"Error during set_fact check: {e}")
        return 0  # Don't fail on script errors


if __name__ == '__main__':
    sys.exit(main())
