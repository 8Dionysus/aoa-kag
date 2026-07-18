from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.generate_repo_local_kag_index import (
    build_index,
    build_repository_indexes,
)
from scripts.repo_local.portable_family import build_portable_family
from scripts.repo_local.tiered_family import (
    TieredFamilyBuild,
    TieredFamilyError,
    attach_owner_release_signature,
    build_tiered_family,
    prepare_owner_release_lifecycle,
    validate_owner_release,
)
from scripts.repo_local.tiered_governance import (
    build_metrics_report,
    build_os_composition,
    build_owner_change_receipt,
    build_receipt_governance_report,
    receipt_governance_contract,
    update_os_composition,
    validate_os_composition,
)
from tests.test_repo_local_kag_repository_indexes import write_fixture


REPO_ROOT = Path(__file__).resolve().parents[1]


def build_owner(root: Path, owner: str) -> TieredFamilyBuild:
    root.mkdir(parents=True)
    write_fixture(root)
    (root / "kag" / "manifest.json").write_text(
        json.dumps({"repo": owner}),
        encoding="utf-8",
    )
    source = build_index(root)
    family = build_repository_indexes(source, repo_root=root)
    portable, shards = build_portable_family(source, family)
    return build_tiered_family(portable, shards, shadow_mode=False)


def rebuild_owner(
    root: Path,
    previous: TieredFamilyBuild,
) -> TieredFamilyBuild:
    source = build_index(root)
    family = build_repository_indexes(source, repo_root=root)
    previous_manifest = {
        "partitioning": previous.corpus_manifest["partitioning"],
        "budgets": {
            "tracked_bytes_max": 48 * 1024 * 1024,
        },
    }
    portable, shards = build_portable_family(
        source,
        family,
        previous_manifest=previous_manifest,
    )
    return build_tiered_family(
        portable,
        shards,
        shadow_mode=False,
        migration=previous.corpus_manifest["migration"],
    )


def promote(build: TieredFamilyBuild) -> dict[str, object]:
    release = prepare_owner_release_lifecycle(
        build.owner_release,
        state="published",
        source_ref="commit:" + ("a" * 40),
        verification_receipt="owner-validator:test:kag-release",
    )
    digest = release["release_identity"]["content_digest"]
    release = attach_owner_release_signature(
        release,
        algorithm="ed25519",
        signature_ref=f"abyss-machine:attestations/{digest}",
        verification_state="verified",
    )
    validate_owner_release(release)
    return release


def sign_composition(digest: str) -> dict[str, str]:
    return {
        "algorithm": "ed25519",
        "key_id": "abyss-machine:test-public-kag",
        "signature_ref": f"abyss-machine:attestations/{digest}",
        "verification_state": "verified",
    }


def validate_schema(name: str, payload: object) -> None:
    schema = json.loads(
        (REPO_ROOT / "schemas" / name).read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(payload)


class TieredKagGovernanceTests(unittest.TestCase):
    def test_owner_change_receipt_and_metrics_are_exact_and_schema_valid(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "owner"
            before = build_owner(root, "owner-demo")
            readme = root / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8")
                + "\nChanged authored material.\n",
                encoding="utf-8",
            )
            after = rebuild_owner(root, before)
            receipt = build_owner_change_receipt(
                before,
                after,
                base_commit="a" * 40,
                head_commit="b" * 40,
            )
            metrics = build_metrics_report(
                after,
                authored_delta_bytes=27,
                authored_delta_units=1,
                generated_delta_bytes=receipt["changed_bytes"],
                generated_delta_records=len(
                    receipt["changed_record_keys"]
                ),
                unique_kag_blob_bytes_added=sum(
                    len(after.object_bytes[digest])
                    for digest in receipt["artifact_objects"]["added"]
                ),
                changed_shards=len(receipt["changed_shards"]),
                changed_records=len(receipt["changed_record_keys"]),
                owner_fanout=1,
                ci_bytes_scanned=after.distribution_manifest["summary"][
                    "git_hot_bytes"
                ],
            )

        validate_schema("kag-owner-change-receipt.schema.json", receipt)
        validate_schema("kag-tiered-metrics.schema.json", metrics)
        self.assertNotEqual(
            receipt["base"]["corpus_digest"],
            receipt["head"]["corpus_digest"],
        )
        self.assertTrue(receipt["changed_record_keys"])
        self.assertTrue(receipt["changed_shards"])
        self.assertGreater(metrics["metrics"]["byte_amplification"], 0)
        self.assertEqual(1, metrics["metrics"]["owner_fanout"])

    def test_receipt_recurrence_routes_second_and_blocks_third(self) -> None:
        contract = receipt_governance_contract(window_value=20)
        receipts = [
            {
                "owner": "owner-demo",
                "scope": "generated_delta",
                "reason_class": "shard_topology_pressure",
                "changed_generated_bytes": 2 * 1024 * 1024,
            }
            for _ in range(3)
        ]
        first = build_receipt_governance_report(receipts[:1])
        second = build_receipt_governance_report(receipts[:2])
        third = build_receipt_governance_report(receipts)

        validate_schema("kag-receipt-governance.schema.json", contract)
        validate_schema(
            "kag-receipt-governance-report.schema.json",
            third,
        )
        self.assertEqual(
            "explicit_exception",
            first["groups"][0]["state"],
        )
        self.assertEqual(
            "topology_review_required",
            second["groups"][0]["state"],
        )
        self.assertEqual(
            "blocked_until_decision_or_topology_fix",
            third["groups"][0]["state"],
        )
        self.assertEqual(1, third["summary"]["blocked_groups"])

    def test_verified_24_owner_composition_and_incremental_replacement(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            builds = [
                build_owner(base / f"owner-{index:02d}", f"owner-{index:02d}")
                for index in range(24)
            ]
            releases = [promote(build) for build in builds]
            composition = build_os_composition(
                releases,
                signer=sign_composition,
                unresolved_references={
                    "state": "measured",
                    "count": 0,
                },
            )
            initial_digest = composition["composition_identity"][
                "content_digest"
            ]
            self.assertEqual(
                "kag_os_composition",
                composition["composition_identity"]["artifact_class"],
            )
            self.assertEqual(
                "aoa-kag-os-composition-v1",
                composition["composition_identity"]["abi_epoch"],
            )
            first_root = base / "owner-00"
            readme = first_root / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8")
                + "\nIncremental composition change.\n",
                encoding="utf-8",
            )
            replacement_build = rebuild_owner(first_root, builds[0])
            replacement = promote(replacement_build)
            by_digest = {
                release["release_identity"]["content_digest"]: release
                for release in releases
            }
            updated = update_os_composition(
                composition,
                [replacement],
                all_releases_by_digest=by_digest,
                signer=sign_composition,
                unresolved_references={
                    "state": "measured",
                    "count": 0,
                },
            )

        validate_os_composition(composition)
        validate_os_composition(updated)
        validate_schema("kag-os-composition.schema.json", composition)
        validate_schema("kag-os-composition.schema.json", updated)
        self.assertEqual(24, len(updated["owners"]))
        self.assertNotEqual(
            initial_digest,
            updated["composition_identity"]["content_digest"],
        )
        changed = [
            owner
            for owner, prior in zip(
                updated["owners"],
                composition["owners"],
                strict=True,
            )
            if owner["release_digest"] != prior["release_digest"]
        ]
        self.assertEqual(1, len(changed))
        self.assertEqual("owner-00", changed[0]["owner"])
        self.assertEqual(
            "owner-release-manifests-only",
            updated["provenance"]["source_scan"],
        )

    def test_composition_rejects_unsigned_owner_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            builds = [
                build_owner(base / f"owner-{index:02d}", f"owner-{index:02d}")
                for index in range(24)
            ]
            releases = [promote(build) for build in builds]
            releases[7] = copy.deepcopy(builds[7].owner_release)

            with self.assertRaisesRegex(
                TieredFamilyError,
                "not verified",
            ):
                build_os_composition(
                    releases,
                    signer=sign_composition,
                )

            for algorithm, signature_ref in (
                ("none", ""),
                ("ed25519", " "),
            ):
                with self.subTest(
                    algorithm=algorithm,
                    signature_ref=signature_ref,
                ):
                    releases[7] = copy.deepcopy(promote(builds[7]))
                    releases[7]["signature"]["algorithm"] = algorithm
                    releases[7]["signature"]["signature_ref"] = signature_ref
                    releases[7]["signature"]["verification_state"] = "verified"
                    validate_owner_release(releases[7])
                    with self.assertRaisesRegex(
                        TieredFamilyError,
                        "not verified",
                    ):
                        build_os_composition(
                            releases,
                            signer=sign_composition,
                        )


if __name__ == "__main__":
    unittest.main()
