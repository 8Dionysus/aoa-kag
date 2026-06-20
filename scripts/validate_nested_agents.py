#!/usr/bin/env python3
"""Validate required nested AGENTS.md documents for aoa-kag."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class AgentsDocSpec:
    path: Path
    required_snippets: tuple[str, ...]


REQUIRED_DOCS: tuple[AgentsDocSpec, ...] = (
    AgentsDocSpec(
        Path("docs") / "decisions" / "AGENTS.md",
        (
            "# AGENTS.md",
            "durable decision-rationale lane",
            "AOA-KAG-D-####",
            "KAG surfaces",
            "Source lanes",
            "Source repositories own authored meaning",
            "python scripts/generate_decision_indexes.py --check",
            "python scripts/validate_decision_records.py",
        ),
    ),
    AgentsDocSpec(
        Path("docs") / "validation" / "AGENTS.md",
        (
            "# AGENTS.md",
            "validation lanes",
            "command authority",
            "script inventory",
            "config/validation_lanes.json",
            "python -m unittest tests.test_validation_command_authority tests.test_script_topology",
        ),
    ),
    AgentsDocSpec(
        Path("docs") / "testing" / "AGENTS.md",
        (
            "# AGENTS.md",
            "test-home topology",
            "test_inventory.json",
            "scripts/run_tests.py",
            "config/validation_lanes.json",
        ),
    ),
    AgentsDocSpec(
        Path("manifests") / "AGENTS.md",
        (
            "# AGENTS.md Guidance for `manifests/`",
            "source-authored control surfaces",
            "generated/",
            "python scripts/generate_kag.py",
            "python scripts/validate_kag.py",
        ),
    ),
    AgentsDocSpec(
        Path("generated") / "AGENTS.md",
        (
            "# AGENTS.md Guidance for `generated/`",
            "Do not hand-edit files in `generated/`",
            ".min.json",
            "python scripts/generate_kag.py",
            "python scripts/validate_kag.py",
        ),
    ),
    AgentsDocSpec(
        Path("kag") / "AGENTS.md",
        (
            "# AGENTS.md",
            "source-home preflight",
            "local-subtree protocol",
            "live graph stores",
            "source_home.manifest.json",
            "Do not create `nodes/`, `edges/`, `indexes/`, `projections/`, `receipts/`",
            "sibling `/kag` rollout readiness",
        ),
    ),
    AgentsDocSpec(
        Path("schemas") / "AGENTS.md",
        (
            "# AGENTS.md Guidance for `schemas/`",
            "contract surfaces",
            "$schema",
            "$id",
            "paired example",
        ),
    ),
    AgentsDocSpec(
        Path("examples") / "AGENTS.md",
        (
            "# AGENTS.md Guidance for `examples/`",
            "public-safe",
            "illustrative",
            "schemas/",
            "No secrets",
        ),
    ),
)


def validate(repo_root: Path) -> list[str]:
    issues: list[str] = []
    for spec in REQUIRED_DOCS:
        path = repo_root / spec.path
        if not path.is_file():
            issues.append(f"{spec.path.as_posix()}: file is missing")
            continue

        text = path.read_text(encoding="utf-8")
        for snippet in spec.required_snippets:
            if snippet not in text:
                issues.append(f"{spec.path.as_posix()}: missing snippet {snippet!r}")

    return issues


def main() -> int:
    issues = validate(REPO_ROOT)
    if issues:
        print("Nested AGENTS validation failed.", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1

    print("[ok] nested AGENTS docs are present and shaped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
