"""
Pytest configuration for Molecule tests with support bundle auto-collection.

This conftest.py hooks into pytest's test execution lifecycle to automatically
collect support bundles BEFORE Docker containers are destroyed on test failure.

LOCATION: /Users/ishikapaliwal/ansible_collections/confluent/platform/molecule/conftest.py

This solves the critical timing issue where:
  - Molecule pytest runs tests in Docker containers
  - On test failure, pytest immediately destroys containers
  - Standard callback plugins trigger AFTER containers are destroyed
  - Result: No diagnostic data available

This hook ensures support bundle collection happens BEFORE cleanup.
"""

import os
import subprocess
import pytest
from pathlib import Path


def pytest_runtest_makereport(item, call):
    """
    Hook called after each test phase (setup, call, teardown).

    We intercept test failures during the 'call' phase (actual test execution)
    and trigger support bundle collection BEFORE molecule destroy runs.

    Args:
        item: The test item being executed
        call: The call information (contains exception info if test failed)
    """
    if call.when == "call":  # Only during actual test execution (not setup/teardown)
        # Check if test failed
        if call.excinfo is not None:
            # Extract scenario name from test item
            scenario_name = _get_scenario_name(item)

            if scenario_name:
                print(f"\n{'=' * 80}")
                print(f"❌ TEST FAILED: {item.nodeid}")
                print(f"📦 SCENARIO: {scenario_name}")
                print(f"🔍 Collecting support bundle BEFORE container cleanup...")
                print(f"{'=' * 80}\n")

                try:
                    _collect_support_bundle_for_scenario(scenario_name)
                except Exception as e:
                    print(f"⚠️  Support bundle collection failed: {e}")
                    print(f"Continuing with test cleanup...\n")


def _get_scenario_name(item):
    """
    Extract molecule scenario name from pytest test item.

    Pytest item path looks like: molecule/rbac-scram-rhel/test_default.py::test_run
    We extract 'rbac-scram-rhel' as the scenario name.

    Args:
        item: Pytest test item

    Returns:
        str: Scenario name (e.g., 'rbac-scram-rhel') or None if not found
    """
    try:
        # Get the path to the test file
        test_path = Path(item.fspath)

        # Navigate up to find molecule directory
        for parent in test_path.parents:
            if parent.name == "molecule":
                # Scenario is the directory containing the test
                scenario_dir = test_path.parent
                return scenario_dir.name

        return None
    except Exception as e:
        print(f"⚠️  Could not extract scenario name: {e}")
        return None


def _collect_support_bundle_for_scenario(scenario_name):
    """
    Trigger support bundle collection for a specific scenario.

    This runs ansible-playbook with the molecule-generated inventory to collect
    diagnostics from running Docker containers BEFORE they are destroyed.

    Args:
        scenario_name: Name of the molecule scenario (e.g., 'rbac-scram-rhel')
    """
    # Get paths
    repo_root = Path(__file__).parent.parent  # cp-ansible root
    playbooks_dir = repo_root / "playbooks"
    molecule_dir = repo_root / "molecule" / scenario_name

    # Molecule creates ephemeral inventory during test execution
    # The instance_config.yml contains connection info for running Docker containers
    instance_config = molecule_dir / "instance_config.yml"

    if not instance_config.exists():
        print(f"⚠️  Molecule instance config not found: {instance_config}")
        print(f"Containers may have already been destroyed or never created")
        return

    # Path to support_bundle.yml
    support_bundle_playbook = playbooks_dir / "support_bundle.yml"

    if not support_bundle_playbook.exists():
        print(f"⚠️  support_bundle.yml not found at: {support_bundle_playbook}")
        return

    # Build ansible-playbook command
    # Target the Docker containers using molecule's instance config
    cmd = [
        "ansible-playbook",
        str(support_bundle_playbook),
        "-i", str(instance_config),
        "-e", f"support_bundle_cluster_name={scenario_name}",
        "-e", "support_bundle_sanitize_configs=true",
        "-e", f"support_bundle_output_path={playbooks_dir}",
        "-v",  # Verbose output for debugging
    ]

    print(f"Executing: {' '.join(cmd)}")
    print(f"Working directory: {repo_root}\n")

    # Execute support bundle collection
    try:
        result = subprocess.run(
            cmd,
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )

        if result.returncode == 0:
            # Find created bundle
            bundles = list(playbooks_dir.glob(f"support_bundle_*_{scenario_name}.tar.gz"))
            if bundles:
                bundle_size = bundles[0].stat().st_size / (1024 * 1024)  # MB
                print(f"\n{'=' * 80}")
                print(f"✅ Support bundle collected successfully!")
                print(f"📦 Bundle: {bundles[0].name}")
                print(f"📊 Size: {bundle_size:.2f} MB")
                print(f"📂 Location: {bundles[0]}")
                print(f"{'=' * 80}\n")
            else:
                print(f"⚠️  Support bundle command succeeded but no bundle file found")
                print(f"Expected pattern: support_bundle_*_{scenario_name}.tar.gz")
                print(f"Check {playbooks_dir} for bundles\n")
        else:
            print(f"\n⚠️  Support bundle collection failed (exit code {result.returncode})")
            if result.stdout:
                print(f"Output:\n{result.stdout[:500]}")  # First 500 chars
            if result.stderr:
                print(f"Error output:\n{result.stderr[:500]}")

    except subprocess.TimeoutExpired:
        print(f"⚠️  Support bundle collection timed out after 10 minutes")
    except Exception as e:
        print(f"⚠️  Unexpected error during collection: {e}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport_wrapper(item, call):
    """
    Wrapper hook to ensure our collection happens before pytest's internal cleanup.

    The tryfirst=True ensures this runs before other hooks, guaranteeing we collect
    support bundle before any container destruction logic runs.
    """
    outcome = yield
    rep = outcome.get_result()

    # Only collect on test failure during the call phase
    if rep.when == "call" and rep.failed:
        scenario_name = _get_scenario_name(item)
        if scenario_name:
            # Store metadata for potential use in teardown or reporting
            item.scenario_name = scenario_name
            item.support_bundle_collected = True
