#!/usr/bin/env python3
"""Classify a KAG change into the smallest authoritative validation lane."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Sequence

try:
    from scripts.repo_local.kag_impact import classify_impact
except ImportError:  # pragma: no cover - direct script execution
    from repo_local.kag_impact import classify_impact  # type: ignore


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--owner", required=True)
    parser.add_argument("--base-ref")
    parser.add_argument("--head-ref", default="HEAD")
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--related-owner", action="append", default=[])
    return parser.parse_args(argv)


def _git_paths(root: Path, base_ref: str, head_ref: str) -> list[str]:
    result = subprocess.run(
        (
            "git",
            "diff",
            "--name-only",
            "--diff-filter=ACDMRTUXB",
            base_ref,
            head_ref,
            "--",
        ),
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.repo_root).resolve()
    paths = list(args.path)
    if args.base_ref:
        paths.extend(_git_paths(root, args.base_ref, args.head_ref))
    if not paths:
        raise SystemExit("provide --path or --base-ref")
    classification = classify_impact(
        paths,
        owner=args.owner,
        related_owners=args.related_owner,
    )
    print(
        json.dumps(
            classification.as_dict(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
