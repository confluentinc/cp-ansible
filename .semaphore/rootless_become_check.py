"""
Rootless unguarded-become sanity check.

A rootless deploy user (rootless_enabled: true) has no privilege escalation path at
all - a task with a literal `become: true` that isn't skipped under rootless fails
loudly with a sudo error, which is fine. The real risk is the opposite: a task that
*should* be skipped under rootless but has no guard referencing rootless_enabled at
all, so it silently attempts to escalate (and either fails confusingly deep in the
run, or - on a host where the connecting user happens to have passwordless sudo -
succeeds without anyone noticing rootless was never actually rootless).

Scans roles/*/tasks/*.yml for a task with a literal `become: true`/`become: yes`
(not a templated expression, which is already conditional by definition) whose
own + inherited `when:` conditions never mention rootless_enabled. Block-level
`when:` and `become` are inherited by children, same as Ansible itself.
"""

import glob
import os
import sys

import yaml

ROOTLESS_VAR = "rootless_enabled"


def normalize_when(when):
    """Return a task's `when:` value as a list of condition strings."""
    if when is None:
        return []
    if isinstance(when, str):
        return [when]
    if isinstance(when, (list, tuple)):
        return [str(w) for w in when]
    return [str(when)]


def is_literal_become_true(become):
    """True only for an actual boolean True (become: true/yes) - not a template string."""
    return become is True


def _walk(tasks, inherited_when, inherited_become, filepath, violations):
    """Recursively walk a task list, propagating block when/become to children."""
    if not isinstance(tasks, list):
        return
    for task in tasks:
        if not isinstance(task, dict):
            continue
        effective_when = inherited_when + normalize_when(task.get("when"))
        # A block's own `become` applies to children that don't set their own.
        own_become = task.get("become", inherited_become)
        is_block = any(k in task for k in ("block", "rescue", "always"))
        if is_block:
            for key in ("block", "rescue", "always"):
                if key in task:
                    _walk(task[key], effective_when, own_become, filepath, violations)
            continue
        name = task.get("name", "<unnamed>")
        if is_literal_become_true(own_become):
            guarded = any(ROOTLESS_VAR in w for w in effective_when)
            if not guarded:
                violations.append({"file": filepath, "task": name})


def find_violations_in_docs(docs, filepath):
    """Find violations in a list of parsed YAML documents from one file."""
    violations = []
    for doc in docs:
        _walk(doc, [], None, filepath, violations)
    return violations


def scan_tree(collection_root):
    """Scan every roles/*/tasks/*.yml file under collection_root."""
    violations = []
    pattern = os.path.join(collection_root, "roles", "*", "tasks", "*.yml")
    for filepath in sorted(glob.glob(pattern)):
        try:
            with open(filepath, "r", encoding="utf-8") as handle:
                docs = list(yaml.safe_load_all(handle))
        except (yaml.YAMLError, OSError) as exc:
            print(f"Warning: could not parse {filepath}: {exc}")
            continue
        rel = os.path.relpath(filepath, collection_root)
        violations.extend(find_violations_in_docs(docs, rel))
    return violations


def main():
    collection_root = os.environ.get("PATH_TO_CPA") or os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
    print("Running rootless unguarded-become sanity check...")
    print(f"Scanning roles under: {collection_root}")

    violations = scan_tree(collection_root)

    if not violations:
        print(f"✅ No literal 'become: true' found without a {ROOTLESS_VAR} guard.")
        return 0

    print(f"❌ Found {len(violations)} unguarded become violation(s):")
    print("=" * 60)
    for v in violations:
        print(f"File: {v['file']}")
        print(f"Task: {v['task']!r}")
        print("-" * 40)
    print(
        "\nA task with a literal 'become: true' must have 'rootless_enabled' in its "
        "own or an enclosing block's `when:` (e.g. "
        f"`when: not ({ROOTLESS_VAR} | bool)`), or use a templated `become:` expression "
        "instead - otherwise it silently attempts privilege escalation under a rootless "
        "deploy instead of failing loudly or being skipped."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
