#!/usr/bin/env python3
"""Query a validated repo-local KAG index family."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

try:
    from scripts.generate_repo_local_kag_index import REPOSITORY_INDEX_FILENAMES
    from scripts.repo_local.query import RepoKagQuery
    from scripts.validators.repo_local_kag_index import (
        validate_repo_local_kag_repository_index_family,
    )
except ImportError:  # pragma: no cover - direct script execution
    from generate_repo_local_kag_index import REPOSITORY_INDEX_FILENAMES  # type: ignore
    from repo_local.query import RepoKagQuery  # type: ignore
    from validators.repo_local_kag_index import (  # type: ignore
        validate_repo_local_kag_repository_index_family,
    )


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def load_family(repo_root: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    index_root = repo_root / "kag" / "indexes"
    source_index = read_json(index_root / "source_surface_index.json")
    family = {
        index_kind: read_json(index_root / filename)
        for index_kind, filename in REPOSITORY_INDEX_FILENAMES.items()
    }
    validate_repo_local_kag_repository_index_family(
        family,
        source_payload=source_index,
        label=f"{repo_root.name} query family",
    )
    return source_index, family


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Query a repo-local KAG index family.")
    parser.add_argument("query", help="Exact or natural-language query text.")
    parser.add_argument("--repo-root", default=".", help="Repository root containing kag/indexes.")
    parser.add_argument(
        "--mode",
        choices=("exact", "lexical", "graph", "hybrid"),
        default="hybrid",
    )
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument(
        "--access-scope",
        action="append",
        choices=("public", "private", "local", "runtime"),
        dest="access_scopes",
    )
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    source_index, family = load_family(repo_root)
    query = RepoKagQuery(source_index, family)
    payload = query.query(
        args.query,
        mode=args.mode,
        limit=max(args.limit, 1),
        access_scopes=set(args.access_scopes or ["public"]),
    )
    if args.pretty:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
