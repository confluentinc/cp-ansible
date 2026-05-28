# -*- coding: utf-8 -*-
"""Pytest hook to auto-collect a support bundle on molecule test failure.

When a pytest-molecule test fails, this hook runs cp-ansible's
``playbooks/support_bundle.yml`` against molecule's ephemeral inventory.
The resulting ``.tar.gz`` lands in ``~/confluent-platform-support-bundles/``
on the EC2 host, which the CI fetch play in cp-ansible-tools ships to
Semaphore as a job artifact.

Requires ``MOLECULE_DESTROY=never`` so containers are still up when the
hook fires (already set in the on-demand all.yml).
"""
import os
import subprocess

import pytest

_COLLECTION_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BUNDLE_PLAYBOOK = os.path.join(_COLLECTION_ROOT, "playbooks", "support_bundle.yml")


def _find_molecule_inventory(scenario):
    cache_root = os.path.expanduser("~/.cache/molecule")
    if not os.path.isdir(cache_root):
        return None
    for project in os.listdir(cache_root):
        candidate = os.path.join(
            cache_root, project, scenario, "inventory", "ansible_inventory.yml"
        )
        if os.path.exists(candidate):
            return candidate
    return None


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return
    if not os.path.exists(_BUNDLE_PLAYBOOK):
        return

    scenario = os.path.basename(os.path.dirname(str(item.fspath)))
    inventory = _find_molecule_inventory(scenario)
    if not inventory:
        return

    subprocess.run(
        ["ansible-playbook", "-i", inventory, _BUNDLE_PLAYBOOK],
        cwd=_COLLECTION_ROOT,
        check=False,
    )
