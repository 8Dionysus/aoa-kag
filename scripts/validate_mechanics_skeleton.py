#!/usr/bin/env python3
"""Validate the aoa-kag mechanics root skeleton."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
MECHANICS_ROOT = REPO_ROOT / "mechanics"
TOPOLOGY_PATH = MECHANICS_ROOT / "topology.json"

REQUIRED_ROOT_FILES = ("AGENTS.md", "README.md", "topology.json")
FORBIDDEN_ROOT_ENTRIES = ("_meta", "backlog", "legacy", "notes", "scratch", "templates")
CANONICAL_AGENT_HEADINGS = (
    "## Applies to",
    "## Role",
    "## Read before editing",
    "## Boundaries",
    "## Validation",
    "## Closeout",
)
README_SNIPPETS = (
    "`mechanics/` is the dispatcher for repeatable KAG operation pressure.",
    "No KAG mechanic package is active yet.",
    "Create a package only when",
    "python scripts/validate_mechanics_skeleton.py",
)


def _load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, f"{_display(path)}: file is missing"
    except json.JSONDecodeError as exc:
        return None, f"{_display(path)}: invalid JSON: {exc}"
    if not isinstance(payload, dict):
        return None, f"{_display(path)}: must be a JSON object"
    return payload, None


def _display(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def validate(repo_root: Path = REPO_ROOT) -> list[str]:
    mechanics_root = repo_root / "mechanics"
    issues: list[str] = []

    if not mechanics_root.is_dir():
        return ["mechanics/: directory is missing"]

    for name in FORBIDDEN_ROOT_ENTRIES:
        if (mechanics_root / name).exists():
            issues.append(f"mechanics/{name}: forbidden root mechanics entry")

    topology, topology_error = _load_json(mechanics_root / "topology.json")
    if topology_error:
        issues.append(topology_error)
        topology = None

    if topology is not None:
        if topology.get("version") != 1:
            issues.append("mechanics/topology.json: version must be 1")
        if topology.get("layer") != "aoa-kag":
            issues.append("mechanics/topology.json: layer must be aoa-kag")

        active_package_names: list[str] = []
        active_packages = topology.get("active_packages")
        if isinstance(active_packages, list):
            for package in active_packages:
                if isinstance(package, dict) and isinstance(package.get("path"), str):
                    package_path = package["path"]
                    if "/" in package_path or package_path in REQUIRED_ROOT_FILES:
                        issues.append(
                            "mechanics/topology.json: active package paths must be "
                            f"single directory names: {package_path!r}"
                        )
                    else:
                        active_package_names.append(package_path)

        actual_root_entries = sorted(path.name for path in mechanics_root.iterdir())
        allowed_root_entries = sorted((*REQUIRED_ROOT_FILES, *active_package_names))
        if actual_root_entries != allowed_root_entries:
            issues.append(
                "mechanics/: root entries must match required root files plus "
                f"topology active packages {allowed_root_entries!r}; found {actual_root_entries!r}"
            )

        root_contract = topology.get("root_contract")
        if not isinstance(root_contract, dict):
            issues.append("mechanics/topology.json: root_contract must be an object")
        else:
            if sorted(root_contract.get("allowed_root_files", [])) != sorted(REQUIRED_ROOT_FILES):
                issues.append(
                    "mechanics/topology.json: root_contract.allowed_root_files "
                    f"must be {sorted(REQUIRED_ROOT_FILES)!r}"
                )
            if sorted(root_contract.get("forbidden_root_entries", [])) != sorted(FORBIDDEN_ROOT_ENTRIES):
                issues.append(
                    "mechanics/topology.json: root_contract.forbidden_root_entries "
                    f"must be {sorted(FORBIDDEN_ROOT_ENTRIES)!r}"
                )

        if not isinstance(active_packages, list):
            issues.append("mechanics/topology.json: active_packages must be a list")
        else:
            for package in active_packages:
                if not isinstance(package, dict) or not isinstance(package.get("path"), str):
                    issues.append("mechanics/topology.json: active_packages entries must name a path")
                    continue
                package_root = mechanics_root / package["path"]
                if not package_root.is_dir():
                    issues.append(f"mechanics/topology.json: package path is missing: {package['path']}")
                    continue
                for filename in topology.get("package_contract", {}).get("required_files", []):
                    if not (package_root / filename).exists():
                        issues.append(f"{_display(package_root / filename)}: required package file is missing")

    agents_path = mechanics_root / "AGENTS.md"
    if agents_path.is_file():
        agents_text = agents_path.read_text(encoding="utf-8")
        for heading in CANONICAL_AGENT_HEADINGS:
            if heading not in agents_text:
                issues.append(f"mechanics/AGENTS.md: missing heading {heading!r}")
    else:
        issues.append("mechanics/AGENTS.md: file is missing")

    readme_path = mechanics_root / "README.md"
    if readme_path.is_file():
        readme_text = readme_path.read_text(encoding="utf-8")
        for snippet in README_SNIPPETS:
            if snippet not in readme_text:
                issues.append(f"mechanics/README.md: missing snippet {snippet!r}")
    else:
        issues.append("mechanics/README.md: file is missing")

    return issues


def main() -> int:
    issues = validate(REPO_ROOT)
    if issues:
        print("Mechanics skeleton validation failed.", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1
    print("[ok] mechanics skeleton is present and bounded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
