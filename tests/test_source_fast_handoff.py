from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import ci_release_check, source_fast_handoff, validation_lanes


REPO_ROOT = Path(__file__).resolve().parents[1]


class SourceFastHandoffTests(unittest.TestCase):
    def sample_env(self) -> dict[str, str]:
        return {
            "GITHUB_REPOSITORY": "8Dionysus/aoa-kag",
            "GITHUB_RUN_ID": "12345",
            "GITHUB_RUN_ATTEMPT": "1",
            "GITHUB_WORKFLOW_REF": (
                "8Dionysus/aoa-kag/.github/workflows/repo-validation.yml@refs/pull/1/merge"
            ),
            "GITHUB_SHA": "a" * 40,
            source_fast_handoff.EXPECTED_HISTORY_ENV: "b" * 40,
            source_fast_handoff.EXPECTED_EVENT_HISTORY_ENV: "b" * 40,
        }

    def sample_receipt(self) -> dict[str, object]:
        repository = {
            "commit_sha": "a" * 40,
            "index_tree": "c" * 40,
            "index_entries_sha256": "d" * 64,
        }
        authority = {
            "path": "config/validation_lanes.json",
            "sha256": "e" * 64,
            "source_fast_sequence_sha256": "f" * 64,
        }
        donors = [
            {
                "repo": "aoa-demo",
                "env": "AOA_DEMO_ROOT",
                "expected_pin": "1" * 40,
                "observed_head": "1" * 40,
            }
        ]
        owner_family = {
            "result": "verified",
            "manifest_schema_version": "aoa-repo-local-kag-family-manifest-v3",
            "family_content_digest": "2" * 64,
            "source_index_content_digest": "3" * 64,
            "history_ref": "b" * 40,
            "event_history_ref": "b" * 40,
        }
        with patch.object(
            source_fast_handoff, "_repository_identity", return_value=repository
        ), patch.object(
            source_fast_handoff, "_command_authority", return_value=authority
        ), patch.object(
            source_fast_handoff, "_donor_identities", return_value=donors
        ), patch.object(
            source_fast_handoff, "_owner_family_identity", return_value=owner_family
        ):
            return source_fast_handoff.build_receipt(REPO_ROOT, self.sample_env())

    def test_exact_receipt_is_accepted_only_when_recomputation_matches(self) -> None:
        receipt = self.sample_receipt()
        with patch.object(source_fast_handoff, "build_receipt", return_value=receipt):
            result = source_fast_handoff.verify_receipt(
                receipt,
                REPO_ROOT,
                self.sample_env(),
            )

        self.assertTrue(result.accepted)
        self.assertEqual("accepted", result.reason)
        self.assertEqual(receipt["receipt_digest"], result.receipt_digest)

    def test_tampered_or_ambiguous_receipt_is_rejected(self) -> None:
        original = self.sample_receipt()

        tampered = copy.deepcopy(original)
        tampered["workflow"]["run_id"] = "999"  # type: ignore[index]
        result = source_fast_handoff.verify_receipt(
            tampered,
            REPO_ROOT,
            self.sample_env(),
        )
        self.assertFalse(result.accepted)
        self.assertIn("digest", result.reason)

        resigned = copy.deepcopy(tampered)
        unsigned = dict(resigned)
        del unsigned["receipt_digest"]
        resigned["receipt_digest"] = source_fast_handoff._digest(unsigned)
        with patch.object(source_fast_handoff, "build_receipt", return_value=original):
            result = source_fast_handoff.verify_receipt(
                resigned,
                REPO_ROOT,
                self.sample_env(),
            )
        self.assertFalse(result.accepted)
        self.assertIn("does not match", result.reason)

        missing = copy.deepcopy(original)
        del missing["builder_inputs"]
        result = source_fast_handoff.verify_receipt(
            missing,
            REPO_ROOT,
            self.sample_env(),
        )
        self.assertFalse(result.accepted)
        self.assertIn("ambiguous", result.reason)

    def test_encoded_receipt_round_trip_and_invalid_input(self) -> None:
        receipt = self.sample_receipt()
        encoded = source_fast_handoff.encode_receipt(receipt)
        self.assertEqual(receipt, source_fast_handoff.decode_receipt(encoded))

        result = source_fast_handoff.verify_encoded_receipt("not-base64")
        self.assertFalse(result.accepted)
        self.assertIn("encoding", result.reason)

    def test_ci_lane_selection_falls_back_closed(self) -> None:
        accepted = source_fast_handoff.VerificationResult(
            True,
            "accepted",
            "4" * 64,
        )
        rejected = source_fast_handoff.VerificationResult(False, "mismatch")
        with patch.object(
            source_fast_handoff,
            "verify_encoded_receipt",
            return_value=accepted,
        ):
            lane, result = ci_release_check.select_lane("receipt")
        self.assertEqual("release_continuation", lane)
        self.assertTrue(result.accepted)

        with patch.object(
            source_fast_handoff,
            "verify_encoded_receipt",
            return_value=rejected,
        ):
            lane, result = ci_release_check.select_lane("")
        self.assertEqual("release", lane)
        self.assertFalse(result.accepted)

    def test_repository_identity_rejects_dirty_and_unmerged_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(("git", "init", "-q"), cwd=root, check=True)
            subprocess.run(
                ("git", "config", "user.email", "test@example.invalid"),
                cwd=root,
                check=True,
            )
            subprocess.run(
                ("git", "config", "user.name", "Test"), cwd=root, check=True
            )
            (root / "tracked.txt").write_text("stable\n", encoding="utf-8")
            subprocess.run(("git", "add", "tracked.txt"), cwd=root, check=True)
            subprocess.run(("git", "commit", "-qm", "initial"), cwd=root, check=True)

            identity = source_fast_handoff._repository_identity(root)
            self.assertRegex(identity["commit_sha"], r"^[0-9a-f]{40}$")
            self.assertRegex(identity["index_tree"], r"^[0-9a-f]{40}$")
            self.assertEqual(64, len(identity["index_entries_sha256"]))

            (root / "tracked.txt").write_text("dirty\n", encoding="utf-8")
            with self.assertRaisesRegex(source_fast_handoff.HandoffError, "not clean"):
                source_fast_handoff._repository_identity(root)

    def test_continuation_sequence_omits_only_source_fast(self) -> None:
        full = validation_lanes.RELEASE_CHECK_COMMAND_SEQUENCE
        continuation = validation_lanes.RELEASE_CONTINUATION_COMMAND_SEQUENCE
        source_fast = ("python", "scripts/ci_gate.py", "--mode", "source-fast")
        generated = ("python", "scripts/ci_gate.py", "--mode", "generated")
        bundle = ("python", "scripts/validate_abyss_machine_kag_registry_bundle.py")

        self.assertEqual((source_fast, generated, bundle), full)
        self.assertEqual((generated, bundle), continuation)

    def test_workflow_transfers_same_run_receipt_and_uses_registry_pins(self) -> None:
        workflow = (
            REPO_ROOT / ".github" / "workflows" / "repo-validation.yml"
        ).read_text(encoding="utf-8")
        source_job = workflow.split("  source_fast:\n", 1)[1].split(
            "  release_audit:\n", 1
        )[0]
        release_job = workflow.split("  release_audit:\n", 1)[1].split(
            "  required_summary:\n", 1
        )[0]

        self.assertIn("source_fast_handoff: ${{ steps.source_fast_handoff.outputs.receipt }}", source_job)
        self.assertIn("python scripts/source_fast_handoff.py issue", source_job)
        self.assertIn(
            "history-ref: ${{ env.AOA_KAG_EXPECTED_HISTORY_REF }}",
            source_job,
        )
        self.assertIn(
            "event-history-ref: ${{ env.AOA_KAG_EXPECTED_EVENT_HISTORY_REF }}",
            source_job,
        )
        self.assertIn("AOA_KAG_SOURCE_FAST_HANDOFF: ${{ needs.source_fast.outputs.source_fast_handoff }}", release_job)
        self.assertIn("python scripts/ci_release_check.py", release_job)
        self.assertNotIn("python scripts/release_check.py", release_job)
        provider_registry = json.loads(
            (REPO_ROOT / "manifests" / "provider_registry.json").read_text(
                encoding="utf-8"
            )
        )
        source_fast_repos = {
            "Tree-of-Sophia",
            "aoa-agents",
            "aoa-evals",
            "aoa-memo",
            "aoa-playbooks",
            "aoa-sdk",
            "aoa-stats",
            "aoa-techniques",
        }
        registry_pins = {
            provider["repo"]: provider["pinned_ref"]
            for provider in provider_registry["providers"]
            if provider["repo"] in source_fast_repos
        }
        self.assertEqual(source_fast_repos, set(registry_pins))
        for repo, pin in registry_pins.items():
            self.assertIn(f"repository: 8Dionysus/{repo}", source_job)
            self.assertIn(f"ref: {pin}", source_job)


if __name__ == "__main__":
    unittest.main()
