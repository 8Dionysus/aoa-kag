#!/usr/bin/env python3
"""Build a validated retrieval projection plan from repo-owned KAG families."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

try:
    from scripts.build_repo_local_kag_federation import load_owner_bundle, read_json
    from scripts.provider_registry import configured_provider_roots
    from scripts.repo_local.projections import build_federated_retrieval_plan
    from scripts.validators.expected.core import REPO_LOCAL_KAG_RETRIEVAL_PLAN_SCHEMA_PATH
    from scripts.validators.repo_local_kag_index import repo_local_kag_validate_payload
except ImportError:  # pragma: no cover - direct script execution
    from build_repo_local_kag_federation import load_owner_bundle, read_json  # type: ignore
    from provider_registry import configured_provider_roots  # type: ignore
    from repo_local.projections import build_federated_retrieval_plan  # type: ignore
    from validators.expected.core import REPO_LOCAL_KAG_RETRIEVAL_PLAN_SCHEMA_PATH  # type: ignore
    from validators.repo_local_kag_index import repo_local_kag_validate_payload  # type: ignore


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build exact, lexical, vector, hybrid, and graph projection inputs."
    )
    parser.add_argument("--embedding-profile", type=Path, required=True)
    parser.add_argument("--os-root", type=Path, default=Path("/srv/AbyssOS"))
    parser.add_argument("--home-src-root", type=Path, default=Path("/home/dionysus/src"))
    parser.add_argument("--repo", action="append", dest="repos")
    parser.add_argument("--max-chunk-chars", type=int, default=1800)
    parser.add_argument("--overlap-chars", type=int, default=180)
    parser.add_argument("--output", default="-", help="Plan path or '-' for stdout.")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args(argv)


def _embedding_profile(path: Path) -> dict[str, Any]:
    payload = read_json(path.resolve())
    profile = payload.get("embedding_profile", payload)
    if not isinstance(profile, dict):
        raise ValueError(f"{path} embedding profile must be a JSON object")
    return profile


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
    selected_roots = {repo: roots[repo] for repo in sorted(selected)}
    bundles = {
        repo: load_owner_bundle(selected_roots[repo])
        for repo in sorted(selected_roots)
    }
    plan = build_federated_retrieval_plan(
        selected_roots,
        bundles,
        embedding_profile=_embedding_profile(args.embedding_profile),
        max_chunk_chars=args.max_chunk_chars,
        overlap=args.overlap_chars,
    )
    repo_local_kag_validate_payload(
        plan,
        schema_path=REPO_LOCAL_KAG_RETRIEVAL_PLAN_SCHEMA_PATH,
        label="repo-local KAG retrieval plan",
    )
    rendered = json.dumps(
        plan,
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
            print(f"[repo-local-kag-retrieval-plan] drift in {output}", file=sys.stderr)
            return 1
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    print(f"[repo-local-kag-retrieval-plan] wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
