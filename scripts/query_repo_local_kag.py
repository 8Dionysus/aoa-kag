#!/usr/bin/env python3
"""Query a validated repo-local KAG index family."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

try:
    from scripts.repo_local.portable_family import (
        MANIFEST_RELATIVE_PATH,
        PortableFamilyError,
        load_portable_family_with_state,
    )
    from scripts.repo_local.query import RepoKagQuery
    from scripts.repo_local.tiered_family import (
        DISTRIBUTION_SCHEMA_VERSION,
        TieredFamilyError,
        TieredFamilyUnavailable,
    )
    from scripts.validators.repo_local_kag_index import (
        load_repo_local_kag_repository_index_family,
        validate_repo_local_kag_repository_index_family,
    )
except ImportError:  # pragma: no cover - direct script execution
    from repo_local.portable_family import (  # type: ignore
        MANIFEST_RELATIVE_PATH,
        PortableFamilyError,
        load_portable_family_with_state,
    )
    from repo_local.query import RepoKagQuery  # type: ignore
    from repo_local.tiered_family import (  # type: ignore
        DISTRIBUTION_SCHEMA_VERSION,
        TieredFamilyError,
        TieredFamilyUnavailable,
    )
    from validators.repo_local_kag_index import (  # type: ignore
        load_repo_local_kag_repository_index_family,
        validate_repo_local_kag_repository_index_family,
    )


MISSING_OBJECT_PREVIEW_LIMIT = 16


def build_unavailable_payload(
    *,
    repo_name: str,
    state: str,
    missing_objects: Sequence[str],
    next_action: str,
    corpus_digest: str = "",
    distribution_digest: str = "",
) -> dict[str, Any]:
    """Build a bounded machine-readable result for an incomplete family read."""
    missing = tuple(missing_objects)
    return {
        "schema_version": "aoa-repo-local-kag-query-unavailable-v1",
        "repo": repo_name,
        "state": state,
        "complete": False,
        "corpus_digest": corpus_digest,
        "distribution_digest": distribution_digest,
        "missing_object_count": len(missing),
        "missing_objects": list(missing[:MISSING_OBJECT_PREVIEW_LIMIT]),
        "missing_objects_truncated": len(missing) > MISSING_OBJECT_PREVIEW_LIMIT,
        "next_action": next_action,
    }


def load_family(
    repo_root: Path,
    *,
    artifact_root: Path | None = None,
    allow_shadow_git: bool = True,
) -> tuple[
    dict[str, Any],
    dict[str, dict[str, Any]],
    dict[str, Any] | None,
    dict[str, Any] | None,
]:
    if not (repo_root / MANIFEST_RELATIVE_PATH).is_file():
        source_index, family = load_repo_local_kag_repository_index_family(
            repo_root,
            label=f"{repo_root.name} query family",
        )
        return source_index, family, None, None
    source_index, family, manifest, state = load_portable_family_with_state(
        repo_root,
        artifact_root=artifact_root,
        allow_shadow_git=allow_shadow_git,
    )
    validated = validate_repo_local_kag_repository_index_family(
        family,
        source_payload=source_index,
        label=f"{repo_root.name} query family",
    )
    return source_index, validated, manifest, state


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Query a repo-local KAG index family.")
    parser.add_argument("query", help="Exact or natural-language query text.")
    parser.add_argument("--repo-root", default=".", help="Repository root containing kag/indexes.")
    parser.add_argument(
        "--artifact-root",
        help="Verified local CAS containing externalized tiered KAG objects.",
    )
    parser.add_argument(
        "--no-shadow-git",
        action="store_true",
        help="Reject cold objects served from the migration shadow copy in Git.",
    )
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
    artifact_root = Path(args.artifact_root).resolve() if args.artifact_root else None
    try:
        source_index, family, manifest, state = load_family(
            repo_root,
            artifact_root=artifact_root,
            allow_shadow_git=not args.no_shadow_git,
        )
    except TieredFamilyUnavailable as exc:
        payload = build_unavailable_payload(
            repo_name=repo_root.name,
            state=exc.state,
            missing_objects=exc.missing,
            corpus_digest=exc.corpus_digest,
            distribution_digest=exc.distribution_digest,
            next_action=(
                "provide --artifact-root or import a verified offline bundle"
                if exc.state in {"artifact_required", "artifact_unavailable"}
                else "repair or rebuild the family"
            ),
        )
        print(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2 if args.pretty else None,
                sort_keys=True,
                separators=None if args.pretty else (",", ":"),
            )
        )
        return 2
    except (PortableFamilyError, TieredFamilyError) as exc:
        payload = build_unavailable_payload(
            repo_name=repo_root.name,
            state="digest_mismatch",
            missing_objects=(),
            next_action=str(exc),
        )
        print(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2 if args.pretty else None,
                sort_keys=True,
                separators=None if args.pretty else (",", ":"),
            )
        )
        return 2
    query = RepoKagQuery(source_index, family)
    payload = query.query(
        args.query,
        mode=args.mode,
        limit=max(args.limit, 1),
        access_scopes=set(args.access_scopes or ["public"]),
    )
    if manifest is not None and state is not None:
        is_tiered = manifest.get("schema_version") == DISTRIBUTION_SCHEMA_VERSION
        payload["delivery"] = {
            "family_storage": (
                "v4-tiered-content-addressed"
                if is_tiered
                else "v3-portable-shards"
            ),
            "corpus_digest": state["corpus_digest"],
            "distribution_digest": state["distribution_digest"],
            "state": state["state"],
            "complete": state["complete"],
            "routes": state["routes"],
            "manifest_ref": MANIFEST_RELATIVE_PATH.as_posix(),
        }
    if args.pretty:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
