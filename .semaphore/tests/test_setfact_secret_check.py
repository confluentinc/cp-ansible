"""
Tests for setfact_secret_check.py
"""

import os
import sys
from unittest.mock import patch, MagicMock

# Add parent directory to path to import the script
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from setfact_secret_check import (
    parse_diff_for_setfact,
    get_git_diff,
    main
)


class TestParseDiffForSetfact:
    """Tests for parse_diff_for_setfact function"""

    def test_finds_set_fact_in_yaml_file(self):
        """Test that set_fact in YAML files is detected"""
        diff_content = """diff --git a/roles/test/tasks/main.yml b/roles/test/tasks/main.yml
index 1234567..abcdefg 100644
--- a/roles/test/tasks/main.yml
+++ b/roles/test/tasks/main.yml
@@ -10,6 +10,7 @@
   debug:
     msg: "test"
+  - set_fact:
+      secret: "password123"
   - name: Another task
     debug:
       msg: "done"
"""
        issues = parse_diff_for_setfact(diff_content)
        assert len(issues) == 1
        assert issues[0]['file'] == 'roles/test/tasks/main.yml'
        assert 'set_fact' in issues[0]['content']
        assert issues[0]['line'] > 0

    def test_finds_multiple_set_fact_instances(self):
        """Test that multiple set_fact instances are detected"""
        diff_content = """diff --git a/playbooks/test.yml b/playbooks/test.yml
index 1234567..abcdefg 100644
--- a/playbooks/test.yml
+++ b/playbooks/test.yml
@@ -1,3 +1,6 @@
+  - set_fact:
+      var1: "value1"
   - name: Task
     debug:
       msg: "test"
+  - set_fact:
+      var2: "value2"
"""
        issues = parse_diff_for_setfact(diff_content)
        assert len(issues) == 2

    def test_ignores_set_fact_in_non_yaml_files(self):
        """Test that set_fact in non-YAML files is ignored"""
        diff_content = """diff --git a/scripts/test.sh b/scripts/test.sh
index 1234567..abcdefg 100644
--- a/scripts/test.sh
+++ b/scripts/test.sh
@@ -1,2 +1,3 @@
 #!/bin/bash
+set_fact="something"
 echo "test"
"""
        issues = parse_diff_for_setfact(diff_content)
        assert len(issues) == 0

    def test_ignores_removed_lines(self):
        """Test that removed lines (starting with -) are ignored"""
        diff_content = """diff --git a/roles/test/tasks/main.yml b/roles/test/tasks/main.yml
index 1234567..abcdefg 100644
--- a/roles/test/tasks/main.yml
+++ b/roles/test/tasks/main.yml
@@ -10,6 +10,5 @@
-  - set_fact:
-    secret: "old"
   - name: Task
     debug:
       msg: "test"
"""
        issues = parse_diff_for_setfact(diff_content)
        assert len(issues) == 0

    def test_no_set_fact_found(self):
        """Test that diff without set_fact returns empty list"""
        diff_content = """diff --git a/roles/test/tasks/main.yml b/roles/test/tasks/main.yml
index 1234567..abcdefg 100644
--- a/roles/test/tasks/main.yml
+++ b/roles/test/tasks/main.yml
@@ -10,6 +10,7 @@
   - name: Task
     debug:
       msg: "test"
+      new_line: "added"
"""
        issues = parse_diff_for_setfact(diff_content)
        assert len(issues) == 0

    def test_set_fact_with_variations(self):
        """Test that set_fact with spacing variations is detected"""
        diff_content = """diff --git a/roles/test/tasks/main.yml b/roles/test/tasks/main.yml
index 1234567..abcdefg 100644
--- a/roles/test/tasks/main.yml
+++ b/roles/test/tasks/main.yml
@@ -10,6 +10,7 @@
+  - set_fact :
+      var: "value"
"""
        issues = parse_diff_for_setfact(diff_content)
        assert len(issues) == 1


class TestGetGitDiff:
    """Tests for get_git_diff function"""

    @patch('subprocess.run')
    def test_successful_git_diff(self, mock_subprocess):
        """Test successful git diff retrieval"""
        # Mock successful fetch
        mock_fetch = MagicMock()
        mock_fetch.returncode = 0

        # Mock successful diff
        mock_diff = MagicMock()
        mock_diff.returncode = 0
        mock_diff.stdout = "diff --git a/file.yml b/file.yml\n+  - set_fact:\n"

        mock_subprocess.side_effect = [mock_fetch, mock_diff]

        result = get_git_diff('main', 'feature', '/tmp/test')
        assert result is not None
        assert 'set_fact' in result
        assert mock_subprocess.call_count == 2

    @patch('subprocess.run')
    def test_failed_git_diff(self, mock_subprocess):
        """Test failed git diff returns None"""
        # Mock successful fetch
        mock_fetch = MagicMock()
        mock_fetch.returncode = 0

        # Mock failed diff
        mock_diff = MagicMock()
        mock_diff.returncode = 1
        mock_diff.stdout = ""
        mock_diff.stderr = "fatal: bad revision"

        mock_subprocess.side_effect = [mock_fetch, mock_diff]

        result = get_git_diff('main', 'feature', '/tmp/test')
        assert result is None

    @patch('subprocess.run')
    def test_empty_git_diff(self, mock_subprocess):
        """Test that empty diff returns None"""
        # Mock successful fetch
        mock_fetch = MagicMock()
        mock_fetch.returncode = 0

        # Mock empty diff (exit 0 but no content)
        mock_diff = MagicMock()
        mock_diff.returncode = 0
        mock_diff.stdout = ""

        mock_subprocess.side_effect = [mock_fetch, mock_diff]

        result = get_git_diff('main', 'feature', '/tmp/test')
        assert result is None


class TestMain:
    """Tests for main function"""

    @patch.dict(os.environ, {
        'PATH_TO_CPA': '/tmp/test',
        'SEMAPHORE_GIT_PR_BRANCH': 'feature-branch',
        'SEMAPHORE_GIT_PR_BASE_BRANCH': 'main'
    })
    @patch('subprocess.run')
    def test_main_no_issues_found(self, mock_subprocess):
        """Test main returns 0 when no set_fact issues found"""
        # Mock successful fetch and diff
        mock_fetch = MagicMock()
        mock_fetch.returncode = 0

        mock_diff = MagicMock()
        mock_diff.returncode = 0
        mock_diff.stdout = "diff --git a/file.yml b/file.yml\n+  - name: task\n"

        mock_subprocess.side_effect = [mock_fetch, mock_diff]

        exit_code = main()
        assert exit_code == 0

    @patch.dict(os.environ, {
        'PATH_TO_CPA': '/tmp/test',
        'SEMAPHORE_GIT_PR_BRANCH': 'feature-branch',
        'SEMAPHORE_GIT_PR_BASE_BRANCH': 'main'
    })
    @patch('subprocess.run')
    def test_main_issues_found_but_warns_only(self, mock_subprocess):
        """Test main returns 0 when issues found (warning only, doesn't fail)"""
        # Mock successful fetch and diff with set_fact
        mock_fetch = MagicMock()
        mock_fetch.returncode = 0

        mock_diff = MagicMock()
        mock_diff.returncode = 0
        mock_diff.stdout = """diff --git a/roles/test/tasks/main.yml b/roles/test/tasks/main.yml
index 1234567..abcdefg 100644
--- a/roles/test/tasks/main.yml
+++ b/roles/test/tasks/main.yml
@@ -10,6 +10,7 @@
+  - set_fact:
+      secret: "password"
"""

        mock_subprocess.side_effect = [mock_fetch, mock_diff]

        exit_code = main()
        # Should return 0 (warning only, doesn't fail build)
        assert exit_code == 0

    @patch.dict(os.environ, {
        'PATH_TO_CPA': '/tmp/test',
        'SEMAPHORE_GIT_PR_BRANCH': 'feature-branch',
        'SEMAPHORE_GIT_PR_BASE_BRANCH': 'main'
    })
    @patch('subprocess.run')
    def test_main_git_diff_fails_returns_1(self, mock_subprocess):
        """Test main returns 1 when git diff fails"""
        # Mock successful fetch
        mock_fetch = MagicMock()
        mock_fetch.returncode = 0

        # Mock failed diff
        mock_diff = MagicMock()
        mock_diff.returncode = 1
        mock_diff.stdout = ""
        mock_diff.stderr = "fatal: bad revision"

        mock_subprocess.side_effect = [mock_fetch, mock_diff]

        exit_code = main()
        # Should return 1 (fail if check didn't run)
        assert exit_code == 1

    @patch.dict(os.environ, {
        'PATH_TO_CPA': '/tmp/test',
        'SEMAPHORE_GIT_PR_BRANCH': 'feature-branch',
        'SEMAPHORE_GIT_PR_BASE_BRANCH': 'main'
    })
    @patch('subprocess.run')
    def test_main_exception_returns_1(self, mock_subprocess):
        """Test main returns 1 when exception occurs"""
        # Mock subprocess to raise exception
        mock_subprocess.side_effect = Exception("Unexpected error")

        exit_code = main()
        # Should return 1 (fail on exception)
        assert exit_code == 1

    @patch.dict(os.environ, {
        'PATH_TO_CPA': '/tmp/test',
        'SEMAPHORE_GIT_PR_BRANCH': 'feature-branch'
        # No SEMAPHORE_GIT_PR_BASE_BRANCH, should fallback to SEMAPHORE_GIT_BRANCH or 'main'
    })
    @patch('subprocess.run')
    def test_main_uses_fallback_base_branch(self, mock_subprocess):
        """Test main uses fallback when SEMAPHORE_GIT_PR_BASE_BRANCH not set"""
        mock_fetch = MagicMock()
        mock_fetch.returncode = 0

        mock_diff = MagicMock()
        mock_diff.returncode = 0
        mock_diff.stdout = "diff --git a/file.yml b/file.yml\n"

        mock_subprocess.side_effect = [mock_fetch, mock_diff]

        exit_code = main()
        assert exit_code == 0
        # Verify it tried to use fallback (main)
        assert any('main' in str(call) for call in mock_subprocess.call_args_list)
