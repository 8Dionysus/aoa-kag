#!/usr/bin/env python3
"""Assemble a bounded compatibility view from a repo-local KAG family."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

try:
    from scripts.generate_repo_local_kag_index import normalized_json
    from scripts.repo_local.portable_family import (
        PortableFamilyError,
        load_portable_family,
        write_compatibility_view,
    )
    from scripts.repo_local.segmented_family import (
        SegmentedFamilyError,
        validate_segmented_manifest,
        validate_segmented_segments,
    )
except ImportError:  # pragma: no cover - direct script execution
    from generate_repo_local_kag_index import normalized_json  # type: ignore
    from repo_local.portable_family import (  # type: ignore
        PortableFamilyError,
        load_portable_family,
        write_compatibility_view,
    )
    from repo_local.segmented_family import (  # type: ignore
        SegmentedFamilyError,
        validate_segmented_manifest,
        validate_segmented_segments,
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--artifact-root")
    parser.add_argument("--no-shadow-git", action="store_true")
    parser.add_argument(
        "--segmented-family",
        action="store_true",
        help=(
            "Validate every bounded segment and emit a compact access summary; "
            "do not materialize the complete compatibility view."
        ),
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    if args.segmented_family:
        try:
            import json

            manifest_path = repo_root / "kag/indexes/index_family.manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not isinstance(manifest, dict):
                raise SegmentedFamilyError("segmented family manifest must be an object")
            validate_segmented_manifest(manifest)
            counts = validate_segmented_segments(repo_root, manifest)
            identity = manifest.get("family_identity")
            digest = identity.get("content_digest") if isinstance(identity, dict) else None
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "segmented-compatibility-summary.json").write_text(
                json.dumps(
                    {
                        "schema_version": "aoa-repo-local-kag-segmented-assembly-v1",
                        "family_digest": digest,
                        "source_snapshot": manifest.get("family_identity", {}).get(
                            "source_snapshot"
                        ),
                        "segments": counts["segments"],
                        "records": counts["records"],
                        "bytes": counts["bytes"],
                        "assembly": "bounded-segment-validation-only",
                        "full_materialization": "explicitly_not_performed",
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            raise SystemExit(str(exc)) from exc
        print(
            "[repo-local-kag-family] validated bounded segmented compatibility "
            f"digest={digest} segments={counts['segments']} "
            f"records={counts['records']} bytes={counts['bytes']}"
        )
        return 0
    try:
        source, family, manifest = load_portable_family(
            repo_root,
            artifact_root=(
                Path(args.artifact_root).resolve()
                if args.artifact_root
                else None
            ),
            allow_shadow_git=not args.no_shadow_git,
        )
    except PortableFamilyError as exc:
        raise SystemExit(str(exc)) from exc
    write_compatibility_view(
        output_dir,
        source,
        family,
        normalized_json=normalized_json,
    )
    identity = manifest.get("family_identity")
    if not isinstance(identity, dict):
        identity = manifest.get("distribution_identity")
    digest = identity.get("content_digest") if isinstance(identity, dict) else "unknown"
    print(
        "[repo-local-kag-family] assembled "
        f"{output_dir} digest={digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
