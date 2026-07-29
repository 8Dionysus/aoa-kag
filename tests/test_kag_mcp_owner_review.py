from __future__ import annotations

import json
import os
import stat
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.review_kag_mcp_result import (
    KAG_RESULT_SCHEMA,
    KagOwnerReviewError,
    _canonical_source_index_identity,
    _digest,
    _write_private_json,
    review_kag_capture,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 7, 28, 12, 0, tzinfo=timezone.utc)


def _sdk_schema() -> dict:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": [
            "schema_version",
            "review_id",
            "review_owner",
            "capture",
            "grounding_state",
            "freshness_state",
            "owner_accepted",
            "central_proof_asserted",
            "admission_asserted",
            "cross_organ_proven",
            "rollback_proven",
        ],
        "properties": {
            "schema_version": {"const": "aoa_organ_owner_result_review_v1"},
            "review_id": {
                "type": "string",
                "pattern": "^sha256:[0-9a-f]{64}$",
            },
            "review_owner": {"const": "aoa-kag"},
            "capture": {"type": "object"},
            "grounding_state": {"enum": ["grounded", "rejected", "blocked"]},
            "freshness_state": {
                "enum": [
                    "exact",
                    "compatible_drift",
                    "stale_readable",
                    "blocked",
                    "unknown",
                ]
            },
            "owner_accepted": {"const": False},
            "central_proof_asserted": {"const": False},
            "admission_asserted": {"const": False},
            "cross_organ_proven": {"const": False},
            "rollback_proven": {"const": False},
        },
    }


def _capture_payload() -> dict:
    payload = json.loads(
        (REPO_ROOT / "examples" / "kag_mcp_capabilities.example.json").read_text(
            encoding="utf-8"
        )
    )
    canonical_digest, _ = _canonical_source_index_identity()
    owner = next(item for item in payload["owners"] if item["repo"] == "aoa-kag")
    owner["runtime_source_digest"] = canonical_digest
    owner["freshness"] = {
        "state": "current",
        "runtime_source_digest": canonical_digest,
        "canonical_source_digest": canonical_digest,
    }
    return payload


def _capture(root: Path, payload: dict) -> tuple[Path, Path]:
    result_digest = _digest(payload)
    result_ref = f"results/aoa-kag/{result_digest.removeprefix('sha256:')}.json"
    receipt_body = {
        "schema_version": "abyss_stack_mcp_canary_receipt_v1",
        "issuer": "abyss-stack",
        "consumer_id": "abyss-stack-mcp-canary",
        "organ_id": "aoa-kag",
        "policy_family": "read",
        "service_id": "aoa-kag-mcp",
        "endpoint_ref": "http://127.0.0.1:5425/mcp",
        "canary_route": "runbook://mcp-canary/aoa-kag/read",
        "tool_name": "kag_discover",
        "tool_arguments_digest": "sha256:" + ("d" * 64),
        "observed_at": NOW.isoformat(),
        "expires_at": (NOW + timedelta(minutes=10)).isoformat(),
        "protocol_version": "2025-11-25",
        "server_name": "aoa-kag-mcp",
        "server_version": "0.1.0",
        "server_schema_digest": "sha256:" + ("a" * 64),
        "selected_tool_schema_digest": "sha256:" + ("b" * 64),
        "inventory_counts": {
            "tools": 5,
            "resources": 0,
            "resource_templates": 9,
            "prompts": 0,
        },
        "call_succeeded": True,
        "result_contract_matched": True,
        "result_schema_identity": KAG_RESULT_SCHEMA,
        "result_digest": result_digest,
        "result_artifact_ref": result_ref,
        "call_latency_ms": 4,
        "total_latency_ms": 12,
        "reason_codes": [],
        "contains_secrets": False,
        "content_trust": "untrusted_data",
        "instruction_authority": "none",
        "claim_limit": "stack capture only",
    }
    receipt = {
        "receipt_id": _digest(receipt_body),
        **receipt_body,
    }
    artifact_body = {
        "schema_version": "abyss_stack_mcp_canary_result_artifact_v1",
        "issuer": "abyss-stack",
        "organ_id": "aoa-kag",
        "policy_family": "read",
        "service_id": receipt["service_id"],
        "canary_route": receipt["canary_route"],
        "tool_name": receipt["tool_name"],
        "tool_arguments_digest": receipt["tool_arguments_digest"],
        "observed_at": receipt["observed_at"],
        "result_schema_identity": KAG_RESULT_SCHEMA,
        "result_digest": result_digest,
        "owner_payload": payload,
        "contains_secrets": False,
        "content_trust": "untrusted_data",
        "instruction_authority": "none",
        "claim_limit": "capture is not owner review",
    }
    artifact = {
        "artifact_id": _digest(artifact_body),
        **artifact_body,
    }
    receipt_path = (
        root
        / "records"
        / "aoa-kag"
        / f"{receipt['receipt_id'].removeprefix('sha256:')}.json"
    )
    result_path = root / result_ref
    _write_private_json(receipt_path, receipt)
    _write_private_json(result_path, artifact)
    return receipt_path, result_path


class KagMcpOwnerReviewTests(unittest.TestCase):
    def _review(
        self,
        root: Path,
        payload: dict,
    ) -> tuple[dict, Path, Path]:
        receipt_path, result_path = _capture(root, payload)
        sdk_schema = root / "sdk-review.schema.json"
        sdk_schema.write_text(json.dumps(_sdk_schema()), encoding="utf-8")
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        review = review_kag_capture(
            capture_root=root,
            receipt_path=receipt_path,
            artifact_path=result_path,
            sdk_review_schema_path=sdk_schema,
            source_revision=revision,
            reviewed_at=NOW + timedelta(seconds=1),
        )
        return review, receipt_path, result_path

    def test_current_owner_payload_is_grounded_and_exact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            review, _, _ = self._review(root, _capture_payload())
            self.assertEqual("grounded", review["grounding_state"])
            self.assertEqual("exact", review["freshness_state"])
            self.assertTrue(
                review["provider_watermark"].startswith("aoa-kag-source-index:")
            )
            self.assertFalse(review["owner_accepted"])
            self.assertFalse(review["central_proof_asserted"])
            self.assertFalse(review["admission_asserted"])

    def test_schema_drift_is_rejected_without_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = _capture_payload()
            payload["unknown_owner_claim"] = True
            review, _, _ = self._review(root, payload)
            self.assertEqual("rejected", review["grounding_state"])
            self.assertEqual("blocked", review["freshness_state"])
            self.assertIn(
                "owner-payload-schema-invalid",
                review["reason_codes"],
            )
            self.assertIsNone(review["provider_watermark"])
            self.assertFalse(review["owner_accepted"])

    def test_v1_payload_without_distribution_remains_compatible(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = _capture_payload()
            payload.pop("distribution", None)
            payload["projection"].pop("distribution", None)

            review, _, _ = self._review(root, payload)

            self.assertEqual("grounded", review["grounding_state"])
            self.assertEqual("exact", review["freshness_state"])
            self.assertNotIn(
                "owner-payload-schema-invalid",
                review["reason_codes"],
            )

    def test_self_reported_equal_digests_cannot_override_owner_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = _capture_payload()
            owner = next(
                item for item in payload["owners"] if item["repo"] == "aoa-kag"
            )
            owner["runtime_source_digest"] = "1" * 64
            owner["freshness"] = {
                "state": "current",
                "runtime_source_digest": "1" * 64,
                "canonical_source_digest": "1" * 64,
            }

            review, _, _ = self._review(root, payload)

            self.assertEqual("rejected", review["grounding_state"])
            self.assertEqual("blocked", review["freshness_state"])
            self.assertIn(
                "aoa-kag-canonical-source-digest-mismatch",
                review["reason_codes"],
            )
            self.assertFalse(review["self_report_is_security_authority"])

    def test_owner_verified_canonical_digest_preserves_stale_readable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = _capture_payload()
            owner = next(
                item for item in payload["owners"] if item["repo"] == "aoa-kag"
            )
            canonical_digest = owner["freshness"]["canonical_source_digest"]
            owner["runtime_source_digest"] = "0" * 64
            owner["freshness"] = {
                "state": "stale",
                "runtime_source_digest": "0" * 64,
                "canonical_source_digest": canonical_digest,
            }

            review, _, _ = self._review(root, payload)

            self.assertEqual("grounded", review["grounding_state"])
            self.assertEqual("stale_readable", review["freshness_state"])
            self.assertIn(
                "aoa-kag-owner-freshness-stale",
                review["reason_codes"],
            )

    def test_conflicting_owner_runtime_digests_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = _capture_payload()
            owner = next(
                item for item in payload["owners"] if item["repo"] == "aoa-kag"
            )
            owner["runtime_source_digest"] = "1" * 64

            review, _, _ = self._review(root, payload)

            self.assertEqual("rejected", review["grounding_state"])
            self.assertEqual("blocked", review["freshness_state"])
            self.assertIn(
                "aoa-kag-runtime-source-digest-conflict",
                review["reason_codes"],
            )
            self.assertFalse(review["self_report_is_security_authority"])

    def test_lexical_capture_path_cannot_escape_capture_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            root = parent / "capture"
            receipt_path, result_path = _capture(root, _capture_payload())
            artifact = json.loads(result_path.read_text(encoding="utf-8"))
            outside_path = parent / "outside.json"
            _write_private_json(outside_path, artifact)
            result_path.unlink()

            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            traversal_ref = "results/aoa-kag/../../../outside.json"
            receipt["result_artifact_ref"] = traversal_ref
            receipt_body = dict(receipt)
            receipt_body.pop("receipt_id")
            receipt["receipt_id"] = _digest(receipt_body)
            _write_private_json(receipt_path, receipt)

            sdk_schema = root / "sdk-review.schema.json"
            sdk_schema.write_text(json.dumps(_sdk_schema()), encoding="utf-8")
            revision = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            lexical_path = root / traversal_ref

            with self.assertRaisesRegex(
                KagOwnerReviewError,
                "outside the capture root",
            ):
                review_kag_capture(
                    capture_root=root,
                    receipt_path=receipt_path,
                    artifact_path=lexical_path,
                    sdk_review_schema_path=sdk_schema,
                    source_revision=revision,
                    reviewed_at=NOW + timedelta(seconds=1),
                )

    def test_tampered_capture_and_public_inputs_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt_path, result_path = _capture(root, _capture_payload())
            os.chmod(result_path, 0o644)
            sdk_schema = root / "sdk-review.schema.json"
            sdk_schema.write_text(json.dumps(_sdk_schema()), encoding="utf-8")
            revision = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            with self.assertRaisesRegex(KagOwnerReviewError, "group/world"):
                review_kag_capture(
                    capture_root=root,
                    receipt_path=receipt_path,
                    artifact_path=result_path,
                    sdk_review_schema_path=sdk_schema,
                    source_revision=revision,
                    reviewed_at=NOW + timedelta(seconds=1),
                )
            os.chmod(result_path, 0o600)
            artifact = json.loads(result_path.read_text(encoding="utf-8"))
            artifact["owner_payload"]["owners"] = []
            _write_private_json(result_path, artifact)
            with self.assertRaisesRegex(KagOwnerReviewError, "content address"):
                review_kag_capture(
                    capture_root=root,
                    receipt_path=receipt_path,
                    artifact_path=result_path,
                    sdk_review_schema_path=sdk_schema,
                    source_revision=revision,
                    reviewed_at=NOW + timedelta(seconds=1),
                )

    def test_private_writer_keeps_review_mode_0600(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "reviews" / "review.json"
            _write_private_json(output, {"review": "bounded"})
            self.assertEqual(0o600, stat.S_IMODE(output.stat().st_mode))


if __name__ == "__main__":
    unittest.main()
