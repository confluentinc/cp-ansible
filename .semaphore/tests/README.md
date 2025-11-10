# Tests for Semaphore CI Sanity Check Scripts

This directory contains unit tests for the sanity check scripts used in SemaphoreCI.

## Setup

Install test dependencies:

```bash
pip install -r requirements.txt
```

## Running Tests

Run all tests:

```bash
pytest
```

Run tests for a specific script:

```bash
pytest test_setfact_secret_check.py
pytest test_uri_auth_check.py
```

Run with verbose output:

```bash
pytest -v
```

## Test Coverage

### test_setfact_secret_check.py

Tests cover:
- Finding `set_fact` in git diff output
- Ignoring `set_fact` in non-YAML files
- Ignoring removed lines
- Multiple `set_fact` instances
- Git diff success/failure scenarios
- Main function exit codes (0 for warnings, 1 for failures)
- Exception handling

### test_uri_auth_check.py

Tests cover:
- Detecting URI tasks with authorization (headers, body, etc.)
- Detecting `no_log` protection (boolean, string, mask_secrets pattern)
- Finding issues in YAML files
- Multiple issues in single file
- Invalid YAML handling
- Main function exit codes (0 for success, 1 for failures)
- Exception handling

## Exit Code Expectations

- **setfact_secret_check.py**: Returns 0 (warnings only, doesn't fail build)
- **uri_auth_check.py**: Returns 1 when issues found (fails build), 0 when no issues
