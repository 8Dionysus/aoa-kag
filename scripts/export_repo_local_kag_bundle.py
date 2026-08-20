#!/usr/bin/env python3
"""Export a complete verified repo-local KAG family for offline transfer."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

try:
    from scripts.repo_local.tiered_family import (
        OWNER_RELEASE_LIFECYCLE_STATES,
        TieredFamilyError,
        export_portable_bundle,
    )
except ImportError:  # pragma: no cover - direct script execution
    from repo_local.tiered_family import (  # type: ignore
        OWNER_RELEASE_LIFECYCLE_STATES,
        TieredFamilyError,
        export_portable_bundle,
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--artifact-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--lifecycle-state",
        choices=OWNER_RELEASE_LIFECYCLE_STATES,
    )
    parser.add_argument(
        "--source-ref",
        default="",
        help="exact owner commit as <hex> or commit:<hex>",
    )
    parser.add_argument("--verification-receipt", default="")
    parser.add_argument("--supersedes", default="")
    parser.add_argument("--rollback-to", default="")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        manifest = export_portable_bundle(
            Path(args.repo_root).resolve(),
            Path(args.artifact_root).resolve(),
            Path(args.output).resolve(),
            lifecycle_state=args.lifecycle_state,
            source_ref=args.source_ref,
            verification_receipt=args.verification_receipt,
            supersedes=args.supersedes,
            rollback_to=args.rollback_to,
        )
    except (TieredFamilyError, OSError) as exc:
        print(f"[repo-local-kag-export] {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
