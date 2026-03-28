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
