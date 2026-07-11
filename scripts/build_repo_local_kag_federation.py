#!/usr/bin/env python3
"""Build a validated OS Abyss repo-self KAG federation projection."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

try:
    from scripts.generate_repo_local_kag_index import REPOSITORY_INDEX_FILENAMES
    from scripts.provider_registry import configured_provider_roots
    from scripts.repo_local.federation import RepoKagFederation
except ImportError:  # pragma: no cover - direct script execution
    from generate_repo_local_kag_index import REPOSITORY_INDEX_FILENAMES  # type: ignore
    from provider_registry import configured_provider_roots  # type: ignore
    from repo_local.federation import RepoKagFederation  # type: ignore


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def load_owner_bundle(repo_root: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    index_root = repo_root / "kag" / "indexes"
    source = read_json(index_root / "source_surface_index.json")
    family = {
        kind: read_json(index_root / filename)
        for kind, filename in REPOSITORY_INDEX_FILENAMES.items()
    }
    return source, family


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a federated graph projection from repo-owned KAG families."
    )
    parser.add_argument("--os-root", type=Path, default=Path("/srv/AbyssOS"))
    parser.add_argument("--home-src-root", type=Path, default=Path("/home/dionysus/src"))
    parser.add_argument("--repo", action="append", dest="repos")
    parser.add_argument("--output", default="-", help="Projection path or '-' for stdout.")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    roots = configured_provider_roots(
        os_root=args.os_root.resolve(),
        home_src_root=args.home_src_root.resolve(),
    )
    selected = set(args.repos or roots)
    unknown = sorted(selected - set(roots))
    if unknown:
        raise SystemExit(f"unknown provider repos: {', '.join(unknown)}")
    bundles = {
        repo: load_owner_bundle(roots[repo])
        for repo in sorted(selected)
    }
    projection = RepoKagFederation(bundles).projection()
    rendered = json.dumps(
        projection,
        ensure_ascii=False,
        indent=2 if args.pretty else None,
        sort_keys=True,
        separators=None if args.pretty else (",", ":"),
    ) + "\n"
    if args.output == "-":
        if args.check:
            raise SystemExit("--check requires a file --output")
        sys.stdout.write(rendered)
        return 0
    output = Path(args.output).resolve()
    if args.check:
        if not output.is_file() or output.read_text(encoding="utf-8") != rendered:
            print(f"[repo-local-kag-federation] drift in {output}", file=sys.stderr)
            return 1
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    print(f"[repo-local-kag-federation] wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
