#!/usr/bin/env python3
"""Run unittest discovery for active aoa-kag test homes."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


TEST_DIRS = (
    Path("tests"),
    Path("mechanics/agon/parts/promotion-candidates/tests"),
    Path("mechanics/agon/parts/sophian-threshold-packets/tests"),
    Path("mechanics/antifragility/parts/projection-health/tests"),
    Path("mechanics/antifragility/parts/projection-quarantine/tests"),
    Path("mechanics/antifragility/parts/retrieval-outage-regrounding/tests"),
    Path("mechanics/audit/parts/proof-expectation-refs/tests"),
    Path("mechanics/audit/parts/exposure-review/tests"),
    Path("mechanics/boundary-bridge/parts/counterpart-edge/tests"),
    Path("mechanics/boundary-bridge/parts/source-owned-export/tests"),
    Path("mechanics/boundary-bridge/parts/tos-retrieval-axis/tests"),
    Path("mechanics/boundary-bridge/parts/cross-source-projection/tests"),
    Path("mechanics/boundary-bridge/parts/federation-spine/tests"),
    Path("mechanics/boundary-bridge/parts/tiny-consumer-bundle/tests"),
    Path("mechanics/checkpoint/parts/reasoning-handoff/tests"),
    Path("mechanics/distillation/parts/technique-lift/tests"),
    Path("mechanics/distillation/parts/tos-text-chunk-map/tests"),
    Path("mechanics/distillation/parts/tos-route-lift/tests"),
    Path("mechanics/experience/parts/governance-precedent/tests"),
    Path("mechanics/experience/parts/release-patterns/tests"),
    Path("mechanics/experience/parts/office-service-patterns/tests"),
    Path("mechanics/method-growth/parts/pattern-candidate-lineage/tests"),
    Path("mechanics/method-growth/parts/promotion-dossier/tests"),
    Path("mechanics/method-growth/parts/owner-downlink/tests"),
    Path("mechanics/method-growth/parts/retirement/tests"),
    Path("mechanics/growth-cycle/parts/surface-growth-stop-rule/tests"),
    Path("mechanics/questbook/parts/quest-store/tests"),
    Path("mechanics/recurrence/parts/return-regrounding/tests"),
    Path("mechanics/release-support/parts/release-lane/tests"),
)


def has_unittest_files(test_dir: Path) -> bool:
    return test_dir.is_dir() and any(test_dir.glob("test_*.py"))


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    ran = 0

    for test_dir in TEST_DIRS:
        if not has_unittest_files(repo_root / test_dir):
            continue
        command = (
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            str(test_dir),
            "-p",
            "test_*.py",
        )
        print(f"[run] {' '.join(command)}", flush=True)
        subprocess.run(command, cwd=repo_root, check=True)
        ran += 1

    if ran == 0:
        print("[error] no unittest directories were discovered", file=sys.stderr)
        return 1

    print(f"[ok] completed unittest discovery across {ran} test directories")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
