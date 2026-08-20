#!/usr/bin/env python3
"""Prepare externalized v4 KAG surfaces in explicit isolated owner worktrees."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

try:
    from scripts.repo_local.tiered_rollout import (
        CANARY_OWNERS,
        OwnerSource,
        TieredRolloutError,
        prepare_owner_externalization,
        write_json,
    )
except ImportError:  # pragma: no cover - direct script execution
    from repo_local.tiered_rollout import (  # type: ignore
        CANARY_OWNERS,
        OwnerSource,
        TieredRolloutError,
        prepare_owner_externalization,
        write_json,
    )


def parse_binding(value: str) -> tuple[str, Path]:
    owner, separator, path = value.partition("=")
    if not separator or not owner or not path:
        raise argparse.ArgumentTypeError(
            "binding must be OWNER=PATH"
        )
    return owner, Path(path).expanduser().resolve()


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--owner-root",
        action="append",
        required=True,
        type=parse_binding,
        metavar="OWNER=PATH",
        help="isolated owner worktree to mutate",
    )
    parser.add_argument(
        "--owner-artifact-root",
        action="append",
        default=[],
        type=parse_binding,
        metavar="OWNER=PATH",
        help="existing CAS needed when an input owner is already v4",
    )
    parser.add_argument("--artifact-root", required=True)
    parser.add_argument("--receipt-output", required=True)
    parser.add_argument(
        "--canary-only",
        action="store_true",
        help="fail unless the exact five ordered canary owners are selected",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    roots = dict(args.owner_root)
    artifact_roots = dict(args.owner_artifact_root)
    selected = tuple(roots)
    if len(args.owner_root) != len(roots):
        print("[kag-externalize] duplicate owner binding", file=sys.stderr)
        return 1
    if args.canary_only and selected != CANARY_OWNERS:
        print(
            "[kag-externalize] --canary-only requires the exact ordered "
            + ", ".join(CANARY_OWNERS),
            file=sys.stderr,
        )
        return 1
    artifact_root = Path(args.artifact_root).expanduser().resolve()
    receipts = []
    try:
        for index, owner in enumerate(selected, start=1):
            print(
                f"[kag-externalize] owner {index}/{len(selected)} {owner}",
                file=sys.stderr,
            )
            receipts.append(
                prepare_owner_externalization(
                    OwnerSource(
                        owner=owner,
                        root=roots[owner],
                        artifact_root=artifact_roots.get(owner),
                    ),
                    artifact_root=artifact_root,
                )
            )
        report = {
            "schema_version": (
                "aoa-kag-tiered-externalization-preparation-v1"
            ),
            "status": "prepared",
            "owner_count": len(receipts),
            "owners": receipts,
            "stop_line": (
                "prepared surfaces require owner commits, CI, merge, and "
                "exact-source signed publication before consumption"
            ),
        }
        write_json(
            Path(args.receipt_output).expanduser().resolve(),
            report,
        )
    except (OSError, TieredRolloutError) as exc:
        print(f"[kag-externalize] {exc}", file=sys.stderr)
        return 1
    print(f"[kag-externalize] prepared owners={len(receipts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
