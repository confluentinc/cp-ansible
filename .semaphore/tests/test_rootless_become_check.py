"""
Tests for rootless_become_check.py
"""

import os
import sys

# Add parent directory to path to import the script
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rootless_become_check import (  # noqa: E402
    normalize_when,
    find_violations_in_docs,
    scan_tree,
)


class TestNormalizeWhen:
    def test_none(self):
        assert normalize_when(None) == []

    def test_string(self):
        assert normalize_when("rootless_enabled | bool") == ["rootless_enabled | bool"]

    def test_list(self):
        assert normalize_when(["a", "b"]) == ["a", "b"]


class TestFindViolations:
    def test_unguarded_become_flagged(self):
        docs = [[{"name": "Install package", "yum": {}, "become": True}]]
        violations = find_violations_in_docs(docs, "roles/x/tasks/main.yml")
        assert len(violations) == 1
        assert violations[0]["task"] == "Install package"

    def test_unrelated_when_still_flagged(self):
        # A when: exists, but it never mentions rootless_enabled - still a gap.
        docs = [
            [
                {
                    "name": "Install package",
                    "yum": {},
                    "become": True,
                    "when": "ansible_os_family == 'RedHat'",
                }
            ]
        ]
        violations = find_violations_in_docs(docs, "roles/x/tasks/main.yml")
        assert len(violations) == 1

    def test_guarded_task_level_ok(self):
        docs = [
            [
                {
                    "name": "Install package",
                    "yum": {},
                    "become": True,
                    "when": "not (rootless_enabled | bool)",
                }
            ]
        ]
        assert find_violations_in_docs(docs, "roles/x/tasks/main.yml") == []

    def test_guarded_via_when_list_ok(self):
        docs = [
            [
                {
                    "name": "Install package",
                    "yum": {},
                    "become": True,
                    "when": ["some_other_cond", "not (rootless_enabled | bool)"],
                }
            ]
        ]
        assert find_violations_in_docs(docs, "roles/x/tasks/main.yml") == []

    def test_guarded_via_inherited_block_when_ok(self):
        docs = [
            [
                {
                    "name": "blk",
                    "when": "not (rootless_enabled | bool)",
                    "block": [{"name": "Install package", "yum": {}, "become": True}],
                }
            ]
        ]
        assert find_violations_in_docs(docs, "roles/x/tasks/main.yml") == []

    def test_inherited_block_become_flagged(self):
        # become set at block level, inherited by a child with no rootless guard.
        docs = [
            [
                {
                    "name": "blk",
                    "become": True,
                    "block": [{"name": "Install package", "yum": {}}],
                }
            ]
        ]
        violations = find_violations_in_docs(docs, "roles/x/tasks/main.yml")
        assert len(violations) == 1

    def test_templated_become_not_flagged(self):
        # A templated become: is already conditional by definition.
        docs = [
            [
                {
                    "name": "Install package",
                    "yum": {},
                    "become": "{{ not (rootless_enabled | bool) }}",
                }
            ]
        ]
        assert find_violations_in_docs(docs, "roles/x/tasks/main.yml") == []

    def test_become_false_not_flagged(self):
        docs = [[{"name": "no-op", "debug": {}, "become": False}]]
        assert find_violations_in_docs(docs, "roles/x/tasks/main.yml") == []

    def test_no_become_not_flagged(self):
        docs = [[{"name": "no-op", "debug": {}}]]
        assert find_violations_in_docs(docs, "roles/x/tasks/main.yml") == []


class TestScanTreeAgainstRepo:
    def test_repo_tree_is_clean(self):
        """The actual collection tree must satisfy the invariant."""
        collection_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        violations = scan_tree(collection_root)
        assert violations == [], f"Unexpected unguarded become violations: {violations}"
