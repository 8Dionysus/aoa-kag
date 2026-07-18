#!/usr/bin/env python3
"""Build or check one tiered repo-local KAG family and artifact release."""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path
from typing import Sequence

try:
    from scripts.generate_repo_local_kag_index import (
        effective_event_history_ref,
        effective_history_ref,
        main as generate_main,
    )
except ImportError:  # pragma: no cover - direct script execution
    from generate_repo_local_kag_index import (  # type: ignore
        effective_event_history_ref,
        effective_history_ref,
        main as generate_main,
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--artifact-root",
        help=(
            "persistent content-addressed artifact root; when omitted, use "
            "one bounded transient validation root"
        ),
    )
    parser.add_argument("--externalize-cold", action="store_true")
    parser.add_argument("--incremental", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--materialize-artifact-on-check", action="store_true")
    parser.add_argument("--max-pack-bytes", type=int, default=8 * 1024 * 1024)
    parser.add_argument("--history-ref")
    parser.add_argument("--event-history-ref")
    return parser.parse_args(argv)


def _run(args: argparse.Namespace, artifact_root: Path, *, transient: bool) -> int:
    repo_root = Path(args.repo_root).resolve()
    history_ref = effective_history_ref(repo_root, args.history_ref)
    event_history_ref = effective_event_history_ref(
        repo_root,
        args.event_history_ref,
        fallback=history_ref,
    )
    routed = [
        "--repo-root",
        str(repo_root),
        "--tiered-family",
        "--artifact-root",
        str(artifact_root.resolve()),
        "--max-pack-bytes",
        str(args.max_pack_bytes),
    ]
    if args.externalize_cold:
        routed.append("--externalize-cold")
    if args.incremental:
        routed.append("--incremental")
    if args.check:
        routed.append("--check")
    if args.materialize_artifact_on_check or (transient and args.check):
        routed.append("--materialize-artifact-on-check")
    if history_ref:
        routed.extend(("--history-ref", history_ref))
    if event_history_ref:
        routed.extend(("--event-history-ref", event_history_ref))
    return generate_main(routed)


def _transient_parent() -> Path | None:
    selected = (
        os.environ.get("AOA_KAG_VALIDATION_ARTIFACT_PARENT")
        or os.environ.get("RUNNER_TEMP")
        or os.environ.get("TMPDIR")
    )
    if not selected:
        return None
    parent = Path(selected).resolve()
    if not parent.is_dir():
        raise OSError(f"transient artifact parent does not exist: {parent}")
    return parent


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.artifact_root:
        return _run(
            args,
            Path(args.artifact_root),
            transient=False,
        )
    with tempfile.TemporaryDirectory(
        prefix="aoa-kag-generated-lane-",
        dir=_transient_parent(),
    ) as tmpdir:
        return _run(args, Path(tmpdir), transient=True)


if __name__ == "__main__":
    raise SystemExit(main())
