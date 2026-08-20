#!/usr/bin/env python3
"""Import and verify an offline repo-local KAG family into a local CAS."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

try:
    from scripts.repo_local.tiered_family import (
        TieredFamilyError,
        import_portable_bundle,
    )
except ImportError:  # pragma: no cover - direct script execution
    from repo_local.tiered_family import (  # type: ignore
        TieredFamilyError,
        import_portable_bundle,
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-root", required=True)
    parser.add_argument("--artifact-root", required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        receipt = import_portable_bundle(
            Path(args.bundle_root).resolve(),
            Path(args.artifact_root).resolve(),
        )
    except (TieredFamilyError, OSError) as exc:
        print(f"[repo-local-kag-import] {exc}", file=sys.stderr)
        return 1
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
