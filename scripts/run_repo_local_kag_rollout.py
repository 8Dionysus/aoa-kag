#!/usr/bin/env python3
"""Run one evidence-bearing 24-owner tiered KAG publication phase."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence

try:
    from scripts.provider_registry import (
        configured_provider_roots,
        provider_repo_order,
    )
    from scripts.repo_local.tiered_rollout import (
        CANARY_OWNERS,
        MachineTrustAdapter,
        OwnerSource,
        TieredRolloutError,
        build_rollout_evidence,
        build_signed_composition,
        prove_owner_release,
        write_json,
    )
except ImportError:  # pragma: no cover - direct script execution
    from provider_registry import (  # type: ignore
        configured_provider_roots,
        provider_repo_order,
    )
    from repo_local.tiered_rollout import (  # type: ignore
        CANARY_OWNERS,
        MachineTrustAdapter,
        OwnerSource,
        TieredRolloutError,
        build_rollout_evidence,
        build_signed_composition,
        prove_owner_release,
        write_json,
    )


REPO_ROOT = Path(__file__).resolve().parents[1]


def parse_owner_artifact_root(value: str) -> tuple[str, Path]:
    owner, separator, path = value.partition("=")
    if not separator or not owner or not path:
        raise argparse.ArgumentTypeError(
            "owner artifact root must be OWNER=PATH"
        )
    return owner, Path(path).expanduser().resolve()


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase",
        required=True,
        choices=("shadow", "canary", "rollout", "post-merge"),
    )
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--artifact-root", required=True)
    parser.add_argument("--abyss-machine-root", required=True)
    parser.add_argument(
        "--owner-artifact-root",
        action="append",
        default=[],
        type=parse_owner_artifact_root,
        metavar="OWNER=PATH",
    )
    parser.add_argument(
        "--lifecycle-state",
        choices=("manually-verified", "release-ready", "published"),
        default="release-ready",
    )
    parser.add_argument(
        "--evidence-output",
        default="",
        help="defaults to OUTPUT_ROOT/rollout-evidence.json",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    output_root = Path(args.output_root).expanduser().resolve()
    artifact_root = Path(args.artifact_root).expanduser().resolve()
    machine_root = Path(args.abyss_machine_root).expanduser().resolve()
    artifact_by_owner = dict(args.owner_artifact_root)
    roots = configured_provider_roots()
    owners = provider_repo_order()
    if len(owners) != 24 or set(owners) != set(roots):
        print(
            "[tiered-rollout] provider registry must resolve exactly 24 owners",
            file=sys.stderr,
        )
        return 1
    trust = MachineTrustAdapter(
        machine_root,
        registry_root=output_root / "trust" / "registry",
        subject_store_root=output_root / "trust" / "subjects",
        env=os.environ,
    )
    owner_evidence = []
    releases = []
    try:
        for index, owner in enumerate(owners, start=1):
            root = roots[owner]
            current_manifest = json.loads(
                (
                    root
                    / "kag"
                    / "indexes"
                    / "index_family.manifest.json"
                ).read_text(encoding="utf-8")
            )
            current_schema = current_manifest.get("schema_version")
            current_placement = (
                current_manifest.get("placement", {}).get("state")
                if current_schema
                == "aoa-repo-local-kag-distribution-manifest-v1"
                else "git-full"
            )
            if (
                args.phase == "canary"
                and owner in CANARY_OWNERS
                and current_placement != "externalized"
            ):
                raise TieredRolloutError(
                    f"canary owner is not externalized in its exact source: "
                    f"{owner}"
                )
            if (
                args.phase in {"rollout", "post-merge"}
                and current_placement != "externalized"
            ):
                raise TieredRolloutError(
                    f"rollout owner is not externalized in its exact source: "
                    f"{owner}"
                )
            shadow_mode = (
                args.phase == "shadow"
                or (
                    args.phase == "canary"
                    and owner not in CANARY_OWNERS
                )
            )
            source = OwnerSource(
                owner=owner,
                root=root,
                artifact_root=artifact_by_owner.get(owner),
            )
            print(
                f"[tiered-rollout] owner {index}/24 {owner}",
                file=sys.stderr,
            )
            evidence, release = prove_owner_release(
                source,
                output_root=output_root,
                shared_cas=artifact_root,
                shadow_mode=shadow_mode,
                lifecycle_state=args.lifecycle_state,
                trust=trust,
            )
            owner_evidence.append(evidence)
            releases.append(release)
        aoa_kag_head = "commit:" + (
            subprocess.run(
                ("git", "rev-parse", "HEAD"),
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            .stdout.strip()
        )
        composition, composition_proof = build_signed_composition(
            releases,
            output_root=output_root,
            aoa_kag_source_ref=aoa_kag_head,
            lifecycle_state=args.lifecycle_state,
            trust=trust,
            unresolved_references={"state": "measured", "count": 0},
        )
        report = build_rollout_evidence(
            phase=args.phase,
            owners=owner_evidence,
            composition=composition,
            composition_proof=composition_proof,
            artifact_unique_bytes=sum(
                path.stat().st_size
                for path in (artifact_root / "objects" / "sha256").glob(
                    "*/*"
                )
                if path.is_file()
            ),
        )
        destination = (
            Path(args.evidence_output).expanduser().resolve()
            if args.evidence_output
            else output_root / "rollout-evidence.json"
        )
        write_json(destination, report)
    except (OSError, TieredRolloutError) as exc:
        print(f"[tiered-rollout] {exc}", file=sys.stderr)
        return 1
    print(
        f"[tiered-rollout] {report['status']} "
        f"owners={report['aggregate']['owner_count']} "
        f"git_hot_bytes={report['aggregate']['git_hot_bytes']}"
    )
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
