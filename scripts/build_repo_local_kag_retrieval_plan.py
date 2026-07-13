#!/usr/bin/env python3
"""Build a validated retrieval projection plan from repo-owned KAG families."""

from __future__ import annotations

import argparse
import filecmp
import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    from scripts.build_repo_local_kag_federation import load_owner_bundle, read_json
    from scripts.provider_registry import configured_provider_roots
    from scripts.repo_local.bundle import (
        retrieval_bundle_matches,
        write_retrieval_bundle,
    )
    from scripts.repo_local.projections import build_federated_retrieval_plan
    from scripts.validators.expected.core import (
        REPO_LOCAL_KAG_RETRIEVAL_BUNDLE_SCHEMA_PATH,
        REPO_LOCAL_KAG_RETRIEVAL_PLAN_SCHEMA_PATH,
    )
    from scripts.validators.repo_local_kag_index import repo_local_kag_validate_payload
except ImportError:  # pragma: no cover - direct script execution
    from build_repo_local_kag_federation import load_owner_bundle, read_json  # type: ignore
    from provider_registry import configured_provider_roots  # type: ignore
    from repo_local.bundle import (  # type: ignore
        retrieval_bundle_matches,
        write_retrieval_bundle,
    )
    from repo_local.projections import build_federated_retrieval_plan  # type: ignore
    from validators.expected.core import (  # type: ignore
        REPO_LOCAL_KAG_RETRIEVAL_BUNDLE_SCHEMA_PATH,
        REPO_LOCAL_KAG_RETRIEVAL_PLAN_SCHEMA_PATH,
    )
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
    parser.add_argument("--bundle-dir", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args(argv)


def _embedding_profile(path: Path) -> dict[str, Any]:
    payload = read_json(path.resolve())
    profile = payload.get("embedding_profile", payload)
    if not isinstance(profile, dict):
        raise ValueError(f"{path} embedding profile must be a JSON object")
    return profile


def _write_or_compare_json(
    path: Path,
    payload: Mapping[str, Any],
    *,
    pretty: bool,
    check: bool,
) -> bool:
    if check and not path.is_file():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(
                payload,
                handle,
                ensure_ascii=False,
                indent=2 if pretty else None,
                sort_keys=True,
                separators=None if pretty else (",", ":"),
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        if check:
            return filecmp.cmp(path, temporary, shallow=False)
        os.replace(temporary, path)
        return True
    finally:
        temporary.unlink(missing_ok=True)


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
    if args.check and args.output == "-" and args.bundle_dir is None:
        raise SystemExit("--check requires a file --output or --bundle-dir")
    failed = False
    if args.output == "-" and args.bundle_dir is None:
        json.dump(
            plan,
            sys.stdout,
            ensure_ascii=False,
            indent=2 if args.pretty else None,
            sort_keys=True,
            separators=None if args.pretty else (",", ":"),
        )
        sys.stdout.write("\n")
        return 0
    if args.output != "-":
        output = Path(args.output).resolve()
        matched = _write_or_compare_json(
            output,
            plan,
            pretty=args.pretty,
            check=args.check,
        )
        if args.check and not matched:
            print(f"[repo-local-kag-retrieval-plan] drift in {output}", file=sys.stderr)
            failed = True
        elif not args.check:
            print(f"[repo-local-kag-retrieval-plan] wrote {output}")
    if args.bundle_dir is not None:
        bundle_dir = args.bundle_dir.resolve()
        if args.check:
            if not retrieval_bundle_matches(plan, bundle_dir):
                print(
                    f"[repo-local-kag-retrieval-bundle] drift in {bundle_dir}",
                    file=sys.stderr,
                )
                failed = True
        else:
            manifest = write_retrieval_bundle(plan, bundle_dir)
            repo_local_kag_validate_payload(
                manifest,
                schema_path=REPO_LOCAL_KAG_RETRIEVAL_BUNDLE_SCHEMA_PATH,
                label="repo-local KAG retrieval bundle manifest",
            )
            print(f"[repo-local-kag-retrieval-bundle] wrote {bundle_dir}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
