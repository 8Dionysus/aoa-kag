#!/usr/bin/env python3
"""Validate a repository-owned KAG index family."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

try:
    from scripts.validators.common import ValidationError
    from scripts.validators.repo_local_kag_index import (
        load_repo_local_kag_repository_index_family,
        load_repo_local_kag_repository_index_family_with_manifest,
    )
except ImportError:  # pragma: no cover - direct script execution
    from validators.common import ValidationError  # type: ignore
    from validators.repo_local_kag_index import (  # type: ignore
        load_repo_local_kag_repository_index_family,
        load_repo_local_kag_repository_index_family_with_manifest,
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--source-index",
        default="kag/indexes/source_surface_index.json",
        help="Source index path, relative to the repository root.",
    )
    parser.add_argument("--artifact-root")
    parser.add_argument("--no-shadow-git", action="store_true")
    parser.add_argument(
        "--probe-source",
        help="Validate the provider home and print one exact portable source identity as JSON.",
    )
    parser.add_argument(
        "--segmented-manifest",
        default="kag/indexes/index_family.manifest.json",
        help="Segmented-family control manifest path, relative to the repository root.",
    )
    return parser.parse_args(argv)


def probe_source(args: argparse.Namespace, repo_root: Path) -> dict[str, object]:
    """Keep consumer probing at the KAG validator owner, without a prebuild."""
    path = args.probe_source
    if (
        not isinstance(path, str)
        or not path
        or len(path.encode("utf-8")) > 4096
        or "\\" in path
        or any(ord(char) < 32 for char in path)
        or any(part in {"", ".", ".."} for part in path.split("/"))
    ):
        raise ValidationError("probe source must be a normalized repository-relative path")
    source, _family, manifest = load_repo_local_kag_repository_index_family_with_manifest(
        repo_root,
        source_index=Path(args.source_index),
        artifact_root=Path(args.artifact_root).resolve() if args.artifact_root else None,
        allow_shadow_git=not args.no_shadow_git,
    )
    try:
        from scripts.validators.local_kag_subtree import _validate_provider_home
    except ImportError:  # pragma: no cover - direct script execution
        from validators.local_kag_subtree import _validate_provider_home  # type: ignore
    owner = source.get("repo") if isinstance(source, dict) else None
    owner = owner.get("name") if isinstance(owner, dict) else None
    if not isinstance(owner, str) or not owner:
        raise ValidationError("portable source index must identify its repository owner")
    _validate_provider_home(owner, repo_root, prebuild=False)
    records = source.get("records")
    if not isinstance(records, list):
        raise ValidationError("portable source index must contain records")
    matches = [
        record for record in records
        if isinstance(record, dict)
        and isinstance(record.get("identity"), dict)
        and record["identity"].get("path") == path
    ]
    if len(matches) != 1:
        raise ValidationError("probe source must select exactly one source record")
    record = matches[0]
    identity = record["identity"]
    if (
        not isinstance(identity.get("content_hash"), str)
        or not identity["content_hash"]
        or not isinstance(record.get("owner_return_route"), dict)
        or not isinstance(manifest, dict)
        or not isinstance(manifest.get("distribution_identity"), dict)
    ):
        raise ValidationError("portable source record or distribution identity is incomplete")
    return {
        "primary_source": {
            "identity": {"path": path, "content_hash": identity["content_hash"]},
            "owner_return_route": record["owner_return_route"],
        },
        "distribution_identity": manifest["distribution_identity"],
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    if args.probe_source is not None:
        try:
            result = probe_source(args, repo_root)
        except (ValidationError, OSError, ValueError) as exc:
            print(f"[repo-local-kag-family] {exc}", file=sys.stderr)
            return 1
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 0
    segmented_path = repo_root / args.segmented_manifest
    try:
        segmented = json.loads(segmented_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
        segmented = None
    if isinstance(segmented, dict) and segmented.get("schema_version") == (
        "aoa-repo-local-kag-segmented-family-v1"
    ):
        try:
            from scripts.repo_local.segmented_family import (
                validate_segmented_manifest,
                validate_segmented_segments,
            )
            validate_segmented_manifest(segmented)
            counts = validate_segmented_segments(repo_root, segmented)
        except (ValueError, OSError) as exc:
            print(f"[repo-local-kag-family] {exc}", file=sys.stderr)
            return 1
        print(
            "[repo-local-kag-family] valid segmented owner="
            f"{repo_root.name} segments={counts['segments']} "
            f"records={counts['records']} bytes={counts['bytes']}"
        )
        return 0
    try:
        source, family = load_repo_local_kag_repository_index_family(
            repo_root,
            source_index=Path(args.source_index),
            artifact_root=(
                Path(args.artifact_root).resolve()
                if args.artifact_root
                else None
            ),
            allow_shadow_git=not args.no_shadow_git,
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
