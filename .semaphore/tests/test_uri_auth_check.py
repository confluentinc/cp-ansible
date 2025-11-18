"""
Tests for uri_auth_check.py
"""

import os
import sys
import tempfile
from unittest.mock import patch

# Add parent directory to path to import the script
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from uri_auth_check import (
    is_uri_task_with_auth,
    has_no_log_protection,
    check_file_for_auth_issues,
    get_all_yaml_files,
    main
)


class TestIsUriTaskWithAuth:
    """Tests for is_uri_task_with_auth function"""

    def test_uri_with_authorization_header(self):
        """Test URI task with Authorization header in headers dict is detected"""
        task = {
            'name': 'Test task',
            'uri': {
                'url': 'https://api.example.com',
                'headers': {
                    'Authorization': 'Bearer token123'
                }
            }
        }
        assert is_uri_task_with_auth(task) is True

    def test_uri_with_auth_in_headers(self):
        """Test URI task with auth in headers dict is detected"""
        task = {
            'name': 'Test task',
            'uri': {
                'url': 'https://api.example.com',
                'headers': {
                    'Authorization': 'Bearer token123'
                }
            }
        }
        assert is_uri_task_with_auth(task) is True

    def test_uri_with_auth_lowercase_header(self):
        """Test URI task with lowercase auth header is detected"""
        task = {
            'name': 'Test task',
            'uri': {
                'url': 'https://api.example.com',
                'headers': {
                    'authorization': 'Bearer token123'
                }
            }
        }
        assert is_uri_task_with_auth(task) is True

    def test_uri_with_password_in_body(self):
        """Test URI task with password in body is detected"""
        task = {
            'name': 'Test task',
            'uri': {
                'url': 'https://api.example.com',
                'body': '{"username": "user", "password": "secret"}'
            }
        }
        assert is_uri_task_with_auth(task) is True

    def test_uri_with_token_in_body(self):
        """Test URI task with token in body is detected"""
        task = {
            'name': 'Test task',
            'uri': {
                'url': 'https://api.example.com',
                'body': '{"token": "abc123"}'
            }
        }
        assert is_uri_task_with_auth(task) is True

    def test_uri_without_auth(self):
        """Test URI task without auth is not detected"""
        task = {
            'name': 'Test task',
            'uri': {
                'url': 'https://api.example.com',
                'method': 'GET'
            }
        }
        assert is_uri_task_with_auth(task) is False

    def test_non_uri_task(self):
        """Test non-URI task is not detected"""
        task = {
            'name': 'Test task',
            'debug': {
                'msg': 'Hello'
            }
        }
        assert is_uri_task_with_auth(task) is False

    def test_invalid_task_structure(self):
        """Test invalid task structure returns False"""
        assert is_uri_task_with_auth({}) is False
        assert is_uri_task_with_auth(None) is False
        assert is_uri_task_with_auth("not a dict") is False


class TestHasNoLogProtection:
    """Tests for has_no_log_protection function"""

    def test_no_log_true(self):
        """Test no_log: true is detected"""
        task = {
            'name': 'Test task',
            'no_log': True
        }
        assert has_no_log_protection(task) is True

    def test_no_log_string_true(self):
        """Test no_log: 'true' (string) is detected"""
        task = {
            'name': 'Test task',
            'no_log': 'true'
        }
        assert has_no_log_protection(task) is True

    def test_no_log_uppercase_string_true(self):
        """Test no_log: 'TRUE' (uppercase string) is detected"""
        task = {
            'name': 'Test task',
            'no_log': 'TRUE'
        }
        assert has_no_log_protection(task) is True

    def test_no_log_with_mask_secrets(self):
        """Test no_log with mask_secrets pattern is detected"""
        task = {
            'name': 'Test task',
            'no_log': '{{ mask_secrets | default(true) }}'
        }
        assert has_no_log_protection(task) is True

    def test_no_log_false(self):
        """Test no_log: false is not detected"""
        task = {
            'name': 'Test task',
            'no_log': False
        }
        assert has_no_log_protection(task) is False

    def test_no_no_log(self):
        """Test task without no_log is not detected"""
        task = {
            'name': 'Test task'
        }
        assert has_no_log_protection(task) is False

    def test_no_log_empty_string(self):
        """Test no_log: '' (empty string) is not detected"""
        task = {
            'name': 'Test task',
            'no_log': ''
        }
        assert has_no_log_protection(task) is False


class TestCheckFileForAuthIssues:
    """Tests for check_file_for_auth_issues function"""

    def test_uri_with_auth_no_no_log_finds_issue(self):
        """Test URI task with auth but no no_log finds issue"""
        yaml_content = """
- name: API call
  uri:
    url: https://api.example.com
    headers:
      Authorization: Bearer token123
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            issues = check_file_for_auth_issues(temp_path)
            assert len(issues) == 1
            assert 'Authorization' in issues[0]['message'] or 'authorization' in issues[0]['message'].lower()
        finally:
            os.unlink(temp_path)

    def test_uri_with_auth_and_no_log_no_issue(self):
        """Test URI task with auth and no_log finds no issue"""
        yaml_content = """
- name: API call
  uri:
    url: https://api.example.com
    Authorization: Bearer token123
  no_log: true
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            issues = check_file_for_auth_issues(temp_path)
            assert len(issues) == 0
        finally:
            os.unlink(temp_path)

    def test_uri_without_auth_no_issue(self):
        """Test URI task without auth finds no issue"""
        yaml_content = """
- name: API call
  uri:
    url: https://api.example.com
    method: GET
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            issues = check_file_for_auth_issues(temp_path)
            assert len(issues) == 0
        finally:
            os.unlink(temp_path)

    def test_multiple_issues_in_file(self):
        """Test multiple issues in one file are all found"""
        yaml_content = """
- name: API call 1
  uri:
    url: https://api.example.com
    headers:
      Authorization: Bearer token1

- name: API call 2
  uri:
    url: https://api2.example.com
    headers:
      Authorization: Bearer token2
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            issues = check_file_for_auth_issues(temp_path)
            assert len(issues) == 2
        finally:
            os.unlink(temp_path)

    def test_invalid_yaml_returns_empty(self):
        """Test invalid YAML returns empty issues list"""
        yaml_content = """
- name: Task
  invalid: [unclosed
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            issues = check_file_for_auth_issues(temp_path)
            assert len(issues) == 0
        finally:
            os.unlink(temp_path)

    def test_empty_file_returns_empty(self):
        """Test empty file returns empty issues list"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            temp_path = f.name

        try:
            issues = check_file_for_auth_issues(temp_path)
            assert len(issues) == 0
        finally:
            os.unlink(temp_path)

    def test_playbook_format_with_nested_tasks(self):
        """Test that playbook format with nested tasks is handled correctly"""
        yaml_content = """
- name: Test Play
  hosts: all
  tasks:
    - name: API call without no_log
      uri:
        url: https://api.example.com
        headers:
          Authorization: Bearer token123

    - name: Another task
      debug:
        msg: "test"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            issues = check_file_for_auth_issues(temp_path)
            assert len(issues) == 1
            assert 'Authorization' in issues[0]['message'] or 'authorization' in issues[0]['message'].lower()
        finally:
            os.unlink(temp_path)

    def test_playbook_format_with_multiple_plays(self):
        """Test that playbook with multiple plays extracts tasks from all plays"""
        yaml_content = """
- name: First Play
  hosts: group1
  tasks:
    - name: API call 1
      uri:
        url: https://api1.example.com
        headers:
          Authorization: Bearer token1

- name: Second Play
  hosts: group2
  tasks:
    - name: API call 2
      block:
        - name: nested block
          block:
            - name: test nested block 2
              block:
                - name: API call 2
                  uri:
                    url: https://api2.example.com
                    headers:
                      Authorization: Bearer token2
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            issues = check_file_for_auth_issues(temp_path)
            assert len(issues) == 2
        finally:
            os.unlink(temp_path)


class TestGetAllYamlFiles:
    """Tests for get_all_yaml_files function"""

    def test_finds_yaml_files_in_expected_directories(self):
        """Test that YAML files are found in expected directories"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create directory structure
            os.makedirs(os.path.join(tmpdir, 'roles', 'test', 'tasks'), exist_ok=True)
            os.makedirs(os.path.join(tmpdir, 'roles', 'test', 'handlers'), exist_ok=True)
            os.makedirs(os.path.join(tmpdir, 'playbooks'), exist_ok=True)

            # Create test files
            with open(os.path.join(tmpdir, 'roles', 'test', 'tasks', 'main.yml'), 'w') as f:
                f.write('- name: test')
            with open(os.path.join(tmpdir, 'roles', 'test', 'handlers', 'main.yml'), 'w') as f:
                f.write('- name: handler')
            with open(os.path.join(tmpdir, 'playbooks', 'test.yml'), 'w') as f:
                f.write('- name: playbook')

            files = get_all_yaml_files(tmpdir)
            assert len(files) == 3
            assert any('roles/test/tasks/main.yml' in f for f in files)
            assert any('roles/test/handlers/main.yml' in f for f in files)
            assert any('playbooks/test.yml' in f for f in files)


class TestMain:
    """Tests for main function"""

    @patch.dict(os.environ, {'PATH_TO_CPA': '/tmp/test'})
    @patch('uri_auth_check.get_all_yaml_files')
    def test_main_no_issues_returns_0(self, mock_get_files):
        """Test main returns 0 when no issues found"""
        mock_get_files.return_value = []

        exit_code = main()
        assert exit_code == 0

    @patch.dict(os.environ, {'PATH_TO_CPA': '/tmp/test'})
    @patch('uri_auth_check.get_all_yaml_files')
    def test_main_issues_found_returns_1(self, mock_get_files):
        """Test main returns 1 when issues found"""
        # Create a temporary file with an issue
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("""
- name: API call
  uri:
    url: https://api.example.com
    headers:
      Authorization: Bearer token123
""")
            temp_path = f.name

        try:
            mock_get_files.return_value = [temp_path]

            exit_code = main()
            assert exit_code == 1
        finally:
            os.unlink(temp_path)

    @patch.dict(os.environ, {'PATH_TO_CPA': '/tmp/test'})
    @patch('uri_auth_check.get_all_yaml_files')
    def test_main_no_yaml_files_returns_0(self, mock_get_files):
        """Test main returns 0 when no YAML files found"""
        mock_get_files.return_value = []

        exit_code = main()
        assert exit_code == 0

    @patch.dict(os.environ, {'PATH_TO_CPA': '/tmp/test'})
    @patch('uri_auth_check.get_all_yaml_files')
    def test_main_exception_returns_1(self, mock_get_files):
        """Test main returns 1 when exception occurs"""
        mock_get_files.side_effect = Exception("Unexpected error")

        exit_code = main()
        assert exit_code == 1

    @patch.dict(os.environ, {'PATH_TO_CPA': '/tmp/test'})
    @patch('uri_auth_check.get_all_yaml_files')
    def test_main_multiple_files_with_issues(self, mock_get_files):
        """Test main finds issues across multiple files"""
        # Create temporary files with issues
        temp_files = []
        try:
            for i in range(2):
                f = tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False)
                f.write(f"""
- name: API call {i}
  uri:
    url: https://api{i}.example.com
    headers:
      Authorization: Bearer token{i}
""")
                f.close()
                temp_files.append(f.name)

            mock_get_files.return_value = temp_files

            exit_code = main()
            assert exit_code == 1
        finally:
            for f in temp_files:
                os.unlink(f)
