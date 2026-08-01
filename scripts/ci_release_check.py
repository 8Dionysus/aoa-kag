#!/usr/bin/env python3
"""Run the CI release continuation, falling back to the full release lane."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Mapping

try:  # Supports direct and package-style execution.
    from scripts.coverage_run import coverage_run_scope
    from scripts import release_check, source_fast_handoff
except ImportError:  # pragma: no cover - direct script execution
    from coverage_run import coverage_run_scope  # type: ignore
    import release_check  # type: ignore
    import source_fast_handoff  # type: ignore


REPO_ROOT = Path(__file__).resolve().parents[1]
CONTINUATION_LANE_ID = "release_continuation"
FALLBACK_LANE_ID = "release"


def select_lane(
    encoded_receipt: str,
    *,
    repo_root: Path = REPO_ROOT,
    env: Mapping[str, str] = os.environ,
) -> tuple[str, source_fast_handoff.VerificationResult]:
    result = source_fast_handoff.verify_encoded_receipt(
        encoded_receipt,
        repo_root=repo_root,
        env=env,
    )
    return (CONTINUATION_LANE_ID if result.accepted else FALLBACK_LANE_ID, result)


def main() -> int:
    encoded = os.environ.get(source_fast_handoff.RECEIPT_ENV, "")
    lane_id, verification = select_lane(encoded)
    if verification.accepted:
        print(
            "[ci-release] accepted exact source-fast handoff "
            f"digest={verification.receipt_digest}; running release continuation"
        )
    else:
        print(
            "[ci-release] source-fast handoff rejected; "
            f"falling back to full release check: {verification.reason}",
            file=sys.stderr,
        )
    with coverage_run_scope(lane=lane_id):
        return release_check.run_release_check(REPO_ROOT, lane_id=lane_id)


if __name__ == "__main__":
    raise SystemExit(main())
