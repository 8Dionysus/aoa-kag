#!/usr/bin/env python3
"""Assemble the seven-file v2 compatibility view from a portable v3 family."""

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
except ImportError:  # pragma: no cover - direct script execution
    from generate_repo_local_kag_index import normalized_json  # type: ignore
    from repo_local.portable_family import (  # type: ignore
        PortableFamilyError,
        load_portable_family,
        write_compatibility_view,
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    try:
        source, family, manifest = load_portable_family(repo_root)
    except PortableFamilyError as exc:
        raise SystemExit(str(exc)) from exc
    write_compatibility_view(
        output_dir,
        source,
        family,
        normalized_json=normalized_json,
    )
    print(
        "[repo-local-kag-family] assembled "
        f"{output_dir} digest={manifest['family_identity']['content_digest']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
