"""
Rootless privileged-tag sanity check.

Rootless installs (rootless_enabled: true) skip tasks tagged privileged/package/
systemd/sysctl. A `configuration`-tagged task must never also carry one of those
tags, or config generation silently drops in a non-root run (the ANSIENG-5897
regression).

Scans roles/*/tasks/*.yml for that conflict. Block-level tags are inherited by
their children.
"""

import glob
import os
import sys

import yaml

# Tags that, combined with `configuration`, would drop config in a non-root run.
ROOTLESS_SKIP_TAGS = {"privileged", "package", "systemd", "sysctl"}
CONFIG_TAG = "configuration"


def normalize_tags(tags):
    """Return a task's `tags` value as a list, tolerating str / list / None."""
    if tags is None:
        return []
    if isinstance(tags, str):
        return [tags]
    if isinstance(tags, (list, tuple)):
        return [t for t in tags if isinstance(t, str)]
    return []


def _walk(tasks, inherited, filepath, violations):
    """Recursively walk a task list, propagating block tags to children."""
    if not isinstance(tasks, list):
        return
    for task in tasks:
        if not isinstance(task, dict):
            continue
        effective = set(inherited) | set(normalize_tags(task.get("tags")))
        is_block = any(k in task for k in ("block", "rescue", "always"))
        if is_block:
            for key in ("block", "rescue", "always"):
                if key in task:
                    _walk(task[key], effective, filepath, violations)
            continue
        name = task.get("name", "<unnamed>")
        # Must run rootless if it's config-generating or itself rootless-purpose (by name).
        must_run_rootless = CONFIG_TAG in effective or "rootless" in str(name).lower()
        if must_run_rootless:
            conflicting = effective & ROOTLESS_SKIP_TAGS
            if conflicting:
                violations.append(
                    {
                        "file": filepath,
                        "task": name,
                        "conflicting_tags": sorted(conflicting),
                    }
                )


def find_violations_in_docs(docs, filepath):
    """Find violations in a list of parsed YAML documents from one file."""
    violations = []
    for doc in docs:
        _walk(doc, [], filepath, violations)
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
    print("Running rootless privileged-tag sanity check...")
    print(f"Scanning roles under: {collection_root}")

    violations = scan_tree(collection_root)

    if not violations:
        print(
            "✅ No 'configuration' task also carries a rootless-skipped tag "
            f"({', '.join(sorted(ROOTLESS_SKIP_TAGS))})."
        )
        return 0

    print(f"❌ Found {len(violations)} rootless tag violation(s):")
    print("=" * 60)
    for v in violations:
        print(f"File: {v['file']}")
        print(f"Task: {v['task']!r}")
        print(f"Conflicting tags: {v['conflicting_tags']}")
        print("-" * 40)
    print(
        "\nA task tagged 'configuration' must not also be tagged with any of "
        f"{sorted(ROOTLESS_SKIP_TAGS)}, or `--skip-tags privileged` (used by "
        "non-root installs) will drop config generation. Move the privileged "
        "action into a separate task."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
