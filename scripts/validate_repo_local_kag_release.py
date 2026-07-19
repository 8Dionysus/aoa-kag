#!/usr/bin/env python3
"""Validate one complete repo-local KAG artifact release and exact v2 parity."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

try:
    from scripts.repo_local.tiered_family import (
        TieredFamilyError,
        validate_tiered_artifact_release,
    )
except ImportError:  # pragma: no cover - direct script execution
    from repo_local.tiered_family import (  # type: ignore
        TieredFamilyError,
        validate_tiered_artifact_release,
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--artifact-root", required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        receipt = validate_tiered_artifact_release(
            Path(args.repo_root).resolve(),
            Path(args.artifact_root).resolve(),
        )
    except (TieredFamilyError, OSError) as exc:
        print(f"[repo-local-kag-release] {exc}", file=sys.stderr)
        return 1
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
