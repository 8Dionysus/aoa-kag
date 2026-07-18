from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.generate_repo_local_kag_index import (
    build_index,
    build_repository_indexes,
)
from scripts.repo_local.portable_family import (
    build_portable_family,
    write_portable_output,
)
from scripts.repo_local.tiered_rollout import (
    CANARY_OWNERS,
    OwnerSource,
    TieredRolloutError,
    build_rollout_evidence,
    prepare_owner_externalization,
    prove_owner_release,
    read_json,
    write_json,
)
from scripts.repo_local.tiered_family import load_tiered_family
from tests.test_repo_local_kag_repository_indexes import write_fixture


REPO_ROOT = Path(__file__).resolve().parents[1]


class FakeTrust:
    def sign_identity(self, payload_path: Path) -> dict[str, object]:
        payload = read_json(payload_path, "identity payload")
        if "release_identity" in payload:
            digest = payload["release_identity"]["content_digest"]
            payload["signature"] = {
                "algorithm": "ed25519",
                "subject_digest": digest,
                "signature_ref": "fake:owner-signature",
                "verification_state": "verified",
            }
        else:
            digest = payload["composition_identity"]["content_digest"]
            payload["signature"] = {
                "algorithm": "ed25519",
                "key_id": "fake:composition-key",
                "subject_digest": digest,
                "signature_ref": "fake:composition-signature",
                "verification_state": "verified",
            }
        write_json(payload_path, payload)
        return {"ok": True}

    def admit(self, **_: object) -> dict[str, object]:
        return {
            "sidecars_ok": True,
            "outer_signature_ok": True,
            "bundle_verification_ok": True,
            "record_id": "sha256:" + ("a" * 64),
            "materialized_ok": True,
            "trust_gate_verdict": "allow",
        }


def build_committed_v3_owner(root: Path, owner: str) -> None:
    root.mkdir(parents=True)
    write_fixture(root)
    (root / "kag" / "manifest.json").write_text(
        json.dumps({"repo": owner}),
        encoding="utf-8",
    )
    subprocess.run(("git", "init", "-q"), cwd=root, check=True)
    subprocess.run(
        ("git", "config", "user.name", "Tiered Rollout Test"),
        cwd=root,
        check=True,
    )
    subprocess.run(
        ("git", "config", "user.email", "tiered-rollout@example.invalid"),
        cwd=root,
        check=True,
    )
    subprocess.run(("git", "add", "."), cwd=root, check=True)
    subprocess.run(
        ("git", "commit", "-qm", "fixture source"),
        cwd=root,
        check=True,
    )
    source_commit = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    source = build_index(root, history_ref=source_commit)
    family = build_repository_indexes(
        source,
        repo_root=root,
        history_ref=source_commit,
        event_history_ref=source_commit,
    )
    manifest, shards = build_portable_family(source, family)
    write_portable_output(root, manifest, shards)
    subprocess.run(("git", "add", "."), cwd=root, check=True)
    subprocess.run(
        ("git", "commit", "-qm", "fixture KAG"),
        cwd=root,
        check=True,
    )


class RepoLocalKagTieredRolloutTests(unittest.TestCase):
    def test_one_owner_shadow_proof_is_exact_offline_and_fail_closed(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            root = base / "owner"
            build_committed_v3_owner(root, "owner-demo")
            evidence, release = prove_owner_release(
                OwnerSource(owner="owner-demo", root=root),
                output_root=base / "evidence",
                shared_cas=base / "cas",
                shadow_mode=True,
                lifecycle_state="release-ready",
                trust=FakeTrust(),  # type: ignore[arg-type]
            )

        self.assertEqual("shadow", evidence["placement_state"])
        self.assertEqual("passed", evidence["checks"]["v2_compatibility"])
        self.assertEqual(
            "artifact_required",
            evidence["checks"]["artifact_outage"],
        )
        self.assertEqual("allow", evidence["trust"]["trust_gate_verdict"])
        self.assertEqual(
            "verified",
            release["signature"]["verification_state"],
        )

    def test_externalization_preparation_removes_only_cold_current_tree(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            root = base / "owner"
            build_committed_v3_owner(root, "owner-demo")
            (root / "staged-source.md").write_text(
                "# Staged authored source\n",
                encoding="utf-8",
            )
            subprocess.run(
                ("git", "add", "staged-source.md"),
                cwd=root,
                check=True,
            )
            receipt = prepare_owner_externalization(
                OwnerSource(owner="owner-demo", root=root),
                artifact_root=base / "cas",
            )
            distribution = read_json(
                root / "kag/indexes/index_family.manifest.json",
                "distribution",
            )
            source_index, _, _, state = load_tiered_family(
                root,
                artifact_root=base / "cas",
                allow_shadow_git=False,
            )

        self.assertEqual(
            "externalized",
            distribution["placement"]["state"],
        )
        self.assertGreater(receipt["artifact_cold_bytes"], 0)
        self.assertTrue(receipt["changed_paths"])
        self.assertTrue(receipt["budget_receipt"])
        self.assertTrue(state["complete"])
        self.assertIn(
            "staged-source.md",
            {
                record["identity"]["path"]
                for record in source_index["records"]
            },
        )
        self.assertEqual(
            "pending-owner-commit",
            receipt["head_commit_state"],
        )

    def test_externalization_preparation_rejects_unstaged_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "owner"
            build_committed_v3_owner(root, "owner-demo")
            (root / "unstaged-source.md").write_text(
                "# Unstaged source\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                TieredRolloutError,
                "staged and no untracked files",
            ):
                prepare_owner_externalization(
                    OwnerSource(owner="owner-demo", root=root),
                    artifact_root=Path(tmpdir) / "cas",
                )

    def test_operator_entrypoints_support_direct_help(self) -> None:
        for relative in (
            "scripts/run_repo_local_kag_rollout.py",
            "scripts/prepare_repo_local_kag_externalization.py",
        ):
            with self.subTest(script=relative):
                result = subprocess.run(
                    (sys.executable, relative, "--help"),
                    cwd=REPO_ROOT,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(0, result.returncode, result.stderr)

    def test_complete_24_owner_report_matches_schema_and_hard_limits(
        self,
    ) -> None:
        owners = []
        for index in range(24):
            owner = f"owner-{index:02d}"
            owners.append(
                {
                    "owner": owner,
                    "source_ref": "commit:" + f"{index:040x}",
                    "input_schema": (
                        "aoa-repo-local-kag-distribution-manifest-v1"
                    ),
                    "placement_state": "externalized",
                    "corpus_digest": "sha256:" + f"{index + 1:064x}",
                    "distribution_digest": (
                        "sha256:" + f"{index + 101:064x}"
                    ),
                    "release_digest": (
                        "sha256:" + f"{index + 201:064x}"
                    ),
                    "measurements": {
                        "git_hot_bytes": 1024,
                        "corpus_total_bytes": 4096,
                        "artifact_cold_bytes": 3072,
                    },
                    "checks": {"v2_compatibility": "passed"},
                    "offline_import": {},
                    "location_pack_proof": {},
                    "source_rebuild_proof": {},
                    "trust": {"trust_gate_verdict": "allow"},
                    "bundle_digest": (
                        "sha256:" + f"{index + 301:064x}"
                    ),
                }
            )
        composition = {
            "composition_identity": {
                "content_digest": "sha256:" + ("f" * 64)
            },
            "federation": {"owner_count": 24},
        }
        report = build_rollout_evidence(
            phase="rollout",
            owners=owners,
            composition=composition,
            composition_proof={"inner_signature": "passed"},
        )
        schema = json.loads(
            (
                REPO_ROOT
                / "schemas"
                / "kag-tiered-rollout-evidence.schema.json"
            ).read_text(encoding="utf-8")
        )

        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(report)
        self.assertEqual("passed", report["status"])
        self.assertEqual(24, report["aggregate"]["owner_count"])
        self.assertEqual(list(CANARY_OWNERS), report["canaries"])
        self.assertEqual([], report["blocking_obligations"])


if __name__ == "__main__":
    unittest.main()
