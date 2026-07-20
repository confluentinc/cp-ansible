"""
Tests for rootless_privileged_tag_check.py
"""

import os
import sys

# Add parent directory to path to import the script
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rootless_privileged_tag_check import (  # noqa: E402
    normalize_tags,
    find_violations_in_docs,
    scan_tree,
)


class TestNormalizeTags:
    def test_none(self):
        assert normalize_tags(None) == []

    def test_string(self):
        assert normalize_tags("configuration") == ["configuration"]

    def test_list(self):
        assert normalize_tags(["configuration", "privileged"]) == [
            "configuration",
            "privileged",
        ]


class TestFindViolations:
    def test_clean_configuration_task(self):
        docs = [[{"name": "Write config", "template": {}, "tags": ["configuration"]}]]
        assert find_violations_in_docs(docs, "roles/x/tasks/main.yml") == []

    def test_configuration_plus_privileged_flagged(self):
        docs = [
            [{"name": "Write config", "template": {}, "tags": ["configuration", "privileged"]}]
        ]
        violations = find_violations_in_docs(docs, "roles/x/tasks/main.yml")
        assert len(violations) == 1
        assert violations[0]["task"] == "Write config"
        assert violations[0]["conflicting_tags"] == ["privileged"]

    def test_privileged_only_task_ignored(self):
        # A purely privileged task (e.g. user creation) is fine - not a config task.
        docs = [[{"name": "Create user", "user": {}, "tags": ["privileged"]}]]
        assert find_violations_in_docs(docs, "roles/x/tasks/main.yml") == []

    def test_configuration_plus_package_and_systemd(self):
        docs = [
            [
                {"name": "cfg1", "template": {}, "tags": ["configuration", "package"]},
                {"name": "cfg2", "template": {}, "tags": ["configuration", "systemd"]},
            ]
        ]
        violations = find_violations_in_docs(docs, "roles/x/tasks/main.yml")
        assert len(violations) == 2

    def test_block_tag_inheritance_flagged(self):
        # A configuration task nested inside a block tagged privileged must be caught.
        docs = [
            [
                {
                    "name": "priv block",
                    "tags": ["privileged"],
                    "block": [
                        {"name": "Write config", "template": {}, "tags": ["configuration"]}
                    ],
                }
            ]
        ]
        violations = find_violations_in_docs(docs, "roles/x/tasks/main.yml")
        assert len(violations) == 1
        assert violations[0]["conflicting_tags"] == ["privileged"]

    def test_string_tag_form(self):
        docs = [[{"name": "cfg", "template": {}, "tags": "configuration"}]]
        assert find_violations_in_docs(docs, "roles/x/tasks/main.yml") == []


class TestScanTreeAgainstRepo:
    def test_repo_tree_is_clean(self):
        """The actual collection tree must satisfy the invariant."""
        collection_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        violations = scan_tree(collection_root)
        assert violations == [], f"Unexpected rootless tag violations: {violations}"
