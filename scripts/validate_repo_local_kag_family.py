#!/usr/bin/env python3
"""Validate a repository-owned KAG index family."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

try:
    from scripts.validators.common import ValidationError
    from scripts.validators.repo_local_kag_index import (
        load_repo_local_kag_repository_index_family,
    )
except ImportError:  # pragma: no cover - direct script execution
    from validators.common import ValidationError  # type: ignore
    from validators.repo_local_kag_index import (  # type: ignore
        load_repo_local_kag_repository_index_family,
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--source-index",
        default="kag/indexes/source_surface_index.json",
        help="Source index path, relative to the repository root.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    try:
        source, family = load_repo_local_kag_repository_index_family(
            repo_root,
            source_index=Path(args.source_index),
        )
    except ValidationError as exc:
        print(f"[repo-local-kag-family] {exc}", file=sys.stderr)
        return 1

    repo = source.get("repo")
    owner = repo.get("name", repo_root.name) if isinstance(repo, dict) else repo_root.name
    counts = ", ".join(
        f"{kind}={len(payload['entries'])}" for kind, payload in family.items()
    )
    print(f"[repo-local-kag-family] valid owner={owner} {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
