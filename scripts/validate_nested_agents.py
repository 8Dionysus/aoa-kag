#!/usr/bin/env python3
"""Validate required nested AGENTS.md documents for aoa-kag."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class AgentsDocSpec:
    path: Path
    required_snippets: tuple[str, ...]


REQUIRED_DOCS: tuple[AgentsDocSpec, ...] = (
    AgentsDocSpec(
        Path(".agents") / "AGENTS.md",
        (
            "# AGENTS.md",
            "agent-facing companion lanes",
            "Codex Spark guidance",
            "Do not restore root `Spark/` as an active lane",
            "on-demand route",
            "VALIDATION.md",
        ),
    ),
    AgentsDocSpec(
        Path(".agents") / "spark" / "AGENTS.md",
        (
            "# AGENTS.md",
            "real-time, interruptible Codex Spark lane",
            "GPT-5.3-Codex-Spark",
            "done-or-handoff",
            "one KAG seam",
            "on-demand route",
            "VALIDATION.md",
        ),
    ),
    AgentsDocSpec(
        Path("quests") / "AGENTS.md",
        (
            "# AGENTS.md",
            "source quest record district",
            "quests/<lane>/<state>/<quest-file>",
            "Do not keep active source records as root `quests/AOA-KAG-Q-*.yaml` aliases",
            "on-demand route",
        ),
    ),
    AgentsDocSpec(
        Path("quests") / "kag" / "AGENTS.md",
        (
            "# AGENTS.md",
            "AOA-KAG-Q-*.yaml",
            "state directory must match",
            "validation route",
        ),
    ),
    AgentsDocSpec(
        Path("docs") / "decisions" / "AGENTS.md",
        (
            "# AGENTS.md",
            "durable decision-rationale lane",
            "AOA-KAG-D-####",
            "KAG surfaces",
            "Source lanes",
            "Source repositories own authored meaning",
            "on-demand route",
            "VALIDATION.md",
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
            "on-demand route",
        ),
    ),
    AgentsDocSpec(
        Path("docs") / "testing" / "AGENTS.md",
        (
            "# AGENTS.md",
            "test-home topology",
            "test_inventory.json",
            "test runner",
            "config/validation_lanes.json",
        ),
    ),
    AgentsDocSpec(
        Path("manifests") / "AGENTS.md",
        (
            "# AGENTS.md Guidance for `manifests/`",
            "source-authored control surfaces",
            "generated/",
            "KAG generation builder",
            "KAG validator",
        ),
    ),
    AgentsDocSpec(
        Path("generated") / "AGENTS.md",
        (
            "# AGENTS.md Guidance for `generated/`",
            "Do not hand-edit files in `generated/`",
            ".min.json",
            "KAG generation builder",
            "KAG validator",
        ),
    ),
    AgentsDocSpec(
        Path("kag") / "AGENTS.md",
        (
            "# AGENTS.md",
            "KAG source home",
            "local provider home",
            "Provider Records",
            "source_home.manifest.json",
            "manifest.json",
            "aoa-kag-mcp",
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

    # D-0049 keeps inherited cards prompt-light. Guard syntax only: semantic
    # owner/source coverage remains in the required snippets and local owners.
    command_line = re.compile(
        r"(?im)^\s*(?:[-*]\s*)?(?:python(?:\s+-m)?\s+|pytest\b|git\s+(?:status|diff|show|log|check)\b|gh\s+|uv\s+|bash\s+|jq\s+)"
    )
    inline_command = re.compile(
        r"`(?:python(?:\s+-m)?\s+|pytest\b|git\s+(?:status|diff|show|log|check)\b|gh\s+|uv\s+|bash\s+|jq\s+)[^`]+`"
    )
    for path in sorted(repo_root.rglob("AGENTS.md")):
        relative = path.relative_to(repo_root).as_posix()
        text = path.read_text(encoding="utf-8")
        if "```" in text:
            issues.append(f"{relative}: fenced procedure is not allowed in an active AGENTS card")
        if command_line.search(text):
            issues.append(f"{relative}: runnable command line is not allowed in an active AGENTS card")
        if inline_command.search(text):
            issues.append(f"{relative}: inline runnable command is not allowed in an active AGENTS card")
        for section in re.findall(
            r"(?ims)^##+\s+(?:Start here|required reading order)\s*$.*?(?=^##+\s+|\Z)",
            text,
        ):
            if "README.md" in section:
                issues.append(f"{relative}: unconditional README inventory is not allowed")

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
