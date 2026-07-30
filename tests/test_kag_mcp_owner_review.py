from __future__ import annotations

import base64
import hashlib
import json
import os
import stat
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator

from scripts.review_kag_mcp_result import (
    KAG_RESULT_SCHEMA,
    KagOwnerReviewError,
    _assert_distinct_io_paths,
    _canonical_source_index_identity,
    _digest,
    _pinned_sdk_review_schema,
    _trusted_stack_signer,
    _write_private_json,
    review_kag_capture,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 7, 28, 12, 0, tzinfo=timezone.utc)
TEST_PRIVATE_KEY_RAW = bytes(range(32))
TEST_PUBLIC_KEY_RAW = bytes.fromhex(
    "03a107bff3ce10be1d70dd18e74bc09967e4d6309ba50d5f1ddc8664125531b8"
)
TEST_SIGNER_ID = "sha256:" + hashlib.sha256(TEST_PUBLIC_KEY_RAW).hexdigest()
TEST_PRIVATE_KEY_DER = (
    bytes.fromhex("302e020100300506032b657004220420") + TEST_PRIVATE_KEY_RAW
)


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


def _attested_payload(body: dict, identity: str) -> dict:
    unsigned_body = {
        "signer_id": TEST_SIGNER_ID,
        "attestation_algorithm": "ed25519",
        **body,
    }
    statement = {
        identity: _digest(unsigned_body),
        **unsigned_body,
    }
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        private_path = root / "private.der"
        statement_path = root / "statement.json"
        attestation_path = root / "attestation.bin"
        private_path.write_bytes(TEST_PRIVATE_KEY_DER)
        statement_path.write_text(
            json.dumps(
                statement,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                "openssl",
                "pkeyutl",
                "-sign",
                "-inkey",
                str(private_path),
                "-keyform",
                "DER",
                "-rawin",
                "-in",
                str(statement_path),
                "-out",
                str(attestation_path),
            ],
            check=False,
            capture_output=True,
        )
        if result.returncode != 0:
            raise AssertionError("test capture attestation failed")
        attestation = base64.urlsafe_b64encode(
            attestation_path.read_bytes()
        ).decode("ascii").rstrip("=")
    return {
        **statement,
        "attestation": attestation,
    }


def _capture(root: Path, payload: dict) -> tuple[Path, Path]:
    result_digest = _digest(payload)
    result_ref = f"results/aoa-kag/{result_digest.removeprefix('sha256:')}.json"
    receipt_body = {
        "schema_version": "abyss_stack_mcp_canary_receipt_v2",
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
    receipt = _attested_payload(receipt_body, "receipt_id")
    artifact_body = {
        "schema_version": "abyss_stack_mcp_canary_result_artifact_v2",
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
    artifact = _attested_payload(artifact_body, "artifact_id")
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
    def setUp(self) -> None:
        self.stack_signer = patch(
            "scripts.review_kag_mcp_result._trusted_stack_signer",
            return_value=(TEST_SIGNER_ID, TEST_PUBLIC_KEY_RAW),
        )
        self.stack_signer.start()
        self.addCleanup(self.stack_signer.stop)

    def _review(
        self,
        root: Path,
        payload: dict,
    ) -> tuple[dict, Path, Path]:
        receipt_path, result_path = _capture(root, payload)
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        with patch(
            "scripts.review_kag_mcp_result._utc_now",
            return_value=NOW + timedelta(seconds=1),
        ):
            review = review_kag_capture(
                capture_root=root,
                receipt_path=receipt_path,
                artifact_path=result_path,
                source_revision=revision,
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

    def test_actual_review_clock_cannot_authorize_an_expired_capture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt_path, result_path = _capture(root, _capture_payload())
            revision = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            with (
                patch(
                    "scripts.review_kag_mcp_result._utc_now",
                    return_value=NOW + timedelta(minutes=11),
                ),
                self.assertRaisesRegex(
                    KagOwnerReviewError,
                    "outside the live capture window",
                ),
            ):
                review_kag_capture(
                    capture_root=root,
                    receipt_path=receipt_path,
                    artifact_path=result_path,
                    source_revision=revision,
                )

    def test_sdk_review_schema_is_read_from_the_pinned_commit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            sdk_root = Path(directory)
            schema_path = (
                sdk_root
                / "schemas"
                / "organ-access"
                / "organ-owner-result-review.schema.json"
            )
            schema_path.parent.mkdir(parents=True)
            pinned_schema = {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "required": ["pinned_contract_marker"],
            }
            schema_path.write_text(json.dumps(pinned_schema), encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=sdk_root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.invalid"],
                cwd=sdk_root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "SDK test"],
                cwd=sdk_root,
                check=True,
            )
            subprocess.run(["git", "add", "."], cwd=sdk_root, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "pin schema"],
                cwd=sdk_root,
                check=True,
            )
            pinned_ref = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=sdk_root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            schema_path.write_text(
                json.dumps(
                    {
                        "$schema": (
                            "https://json-schema.org/draft/2020-12/schema"
                        ),
                        "type": "object",
                    }
                ),
                encoding="utf-8",
            )
            provider_registry = {
                "providers": [
                    {
                        "repo": "aoa-sdk",
                        "checkout_mode": "pinned",
                        "env": "AOA_SDK_ROOT",
                        "pinned_ref": pinned_ref,
                    }
                ]
            }
            with (
                patch(
                    "scripts.review_kag_mcp_result"
                    "._read_committed_public_json",
                    return_value=(
                        provider_registry,
                        json.dumps(provider_registry).encode("utf-8"),
                    ),
                ),
                patch.dict(
                    os.environ,
                    {"AOA_SDK_ROOT": str(sdk_root)},
                ),
            ):
                loaded = _pinned_sdk_review_schema("a" * 40)

            self.assertEqual(pinned_schema, loaded)

    def test_stack_signer_is_bound_to_committed_trust_registry(self) -> None:
        trust = {
            "schema_version": "aoa_kag_runtime_capture_trust_v1",
            "issuers": [
                {
                    "issuer": "abyss-stack",
                    "purpose": "mcp-canary-capture",
                    "state": "active",
                    "attestation_algorithm": "ed25519",
                    "signer_id": TEST_SIGNER_ID,
                    "public_key_base64url": base64.urlsafe_b64encode(
                        TEST_PUBLIC_KEY_RAW
                    ).decode("ascii").rstrip("="),
                }
            ],
        }
        with patch(
            "scripts.review_kag_mcp_result._read_committed_public_json",
            return_value=(trust, json.dumps(trust).encode("utf-8")),
        ):
            signer_id, public_key = _trusted_stack_signer("a" * 40)

        self.assertEqual(TEST_SIGNER_ID, signer_id)
        self.assertEqual(TEST_PUBLIC_KEY_RAW, public_key)

        trust["issuers"][0]["signer_id"] = "sha256:" + ("0" * 64)
        with (
            patch(
                "scripts.review_kag_mcp_result._read_committed_public_json",
                return_value=(trust, json.dumps(trust).encode("utf-8")),
            ),
            self.assertRaisesRegex(
                KagOwnerReviewError,
                "identity does not match",
            ),
        ):
            _trusted_stack_signer("a" * 40)

    def test_portable_manifest_cannot_be_shadowed_by_legacy_index(self) -> None:
        manifest_digest = "a" * 64
        manifest = {
            "repo": {"name": "aoa-kag"},
            "family_identity": {
                "source_snapshot": f"sha256:{manifest_digest}",
            },
            "source_index_header": {
                "index_identity": {
                    "content_digest": manifest_digest,
                },
            },
            "compatibility": {
                "files": [
                    {
                        "kind": "source",
                        "content_digest": manifest_digest,
                    },
                ],
            },
        }
        with (
            patch(
                "scripts.review_kag_mcp_result._committed_path_exists",
                return_value=True,
            ),
            patch(
                "scripts.review_kag_mcp_result._read_committed_public_json",
                return_value=(manifest, json.dumps(manifest).encode("utf-8")),
            ),
        ):
            digest, evidence_ref = _canonical_source_index_identity("a" * 40)

        self.assertEqual(manifest_digest, digest)
        self.assertEqual(
            "kag/indexes/index_family.manifest.json",
            evidence_ref,
        )

    def test_dirty_manifest_cannot_change_committed_canonical_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = root / "kag" / "indexes" / "index_family.manifest.json"
            manifest_path.parent.mkdir(parents=True)

            def manifest(digest: str) -> dict:
                return {
                    "repo": {"name": "aoa-kag"},
                    "family_identity": {
                        "source_snapshot": f"sha256:{digest}",
                    },
                    "source_index_header": {
                        "index_identity": {
                            "content_digest": digest,
                        },
                    },
                    "compatibility": {
                        "files": [
                            {
                                "kind": "source",
                                "content_digest": digest,
                            },
                        ],
                    },
                }

            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.invalid"],
                cwd=root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "KAG test"],
                cwd=root,
                check=True,
            )
            committed_digest = "a" * 64
            dirty_digest = "b" * 64
            manifest_path.write_text(
                json.dumps(manifest(committed_digest)),
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "fixture"],
                cwd=root,
                check=True,
            )
            revision = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            manifest_path.write_text(
                json.dumps(manifest(dirty_digest)),
                encoding="utf-8",
            )

            with patch("scripts.review_kag_mcp_result.REPO_ROOT", root):
                digest, evidence_ref = _canonical_source_index_identity(revision)

            self.assertEqual(committed_digest, digest)
            self.assertNotEqual(dirty_digest, digest)
            self.assertEqual(
                "kag/indexes/index_family.manifest.json",
                evidence_ref,
            )

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

    def test_capability_schema_rejects_unknown_degradation_field(self) -> None:
        payload = _capture_payload()
        degradation = {
            "target": "semantic",
            "state": "degraded",
            "fallback": "lexical",
            "unsupported_claim": "must-not-pass",
        }
        payload["distribution"]["degradation"] = [degradation]
        payload["projection"]["distribution"]["degradation"] = [degradation]
        schema = json.loads(
            (REPO_ROOT / "schemas" / "kag-mcp-capabilities.schema.json").read_text(
                encoding="utf-8"
            )
        )

        errors = list(Draft202012Validator(schema).iter_errors(payload))

        self.assertTrue(errors)
        self.assertTrue(
            any(
                "Additional properties are not allowed" in error.message
                and "unsupported_claim" in error.message
                for error in errors
            )
        )

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

    def test_v1_distribution_fields_are_independently_optional(self) -> None:
        for omitted_from in ("top-level", "projection"):
            with self.subTest(omitted_from=omitted_from):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    payload = _capture_payload()
                    if omitted_from == "top-level":
                        payload.pop("distribution")
                    else:
                        payload["projection"].pop("distribution")

                    review, _, _ = self._review(root, payload)

                    self.assertEqual("grounded", review["grounding_state"])
                    self.assertEqual("exact", review["freshness_state"])
                    self.assertNotIn(
                        "distribution-projection-binding-mismatch",
                        review["reason_codes"],
                    )

    def test_present_distribution_fields_must_still_match(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            payload = _capture_payload()
            payload["projection"]["distribution"] = {
                **payload["projection"]["distribution"],
                "state": "stale",
            }

            review, _, _ = self._review(Path(directory), payload)

            self.assertEqual("rejected", review["grounding_state"])
            self.assertEqual("blocked", review["freshness_state"])
            self.assertIn(
                "distribution-projection-binding-mismatch",
                review["reason_codes"],
            )

    def test_review_labels_are_fixed_to_captured_kag_discover_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            review, _, _ = self._review(Path(directory), _capture_payload())

            self.assertEqual("knowledge-retrieval", review["capability_id"])
            self.assertEqual("retrieve-knowledge", review["primitive_id"])
            self.assertEqual(
                review["capability_id"],
                review["capture"]["capability_id"],
            )
            self.assertEqual(
                review["primitive_id"],
                review["capture"]["primitive_id"],
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

    def test_duplicate_aoa_kag_owner_evidence_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = _capture_payload()
            duplicate = json.loads(
                json.dumps(
                    next(
                        item
                        for item in payload["owners"]
                        if item["repo"] == "aoa-kag"
                    )
                )
            )
            duplicate["runtime_source_digest"] = "1" * 64
            duplicate["freshness"]["runtime_source_digest"] = "1" * 64
            payload["owners"].append(duplicate)

            review, _, _ = self._review(root, payload)

            self.assertEqual("rejected", review["grounding_state"])
            self.assertEqual("blocked", review["freshness_state"])
            self.assertIn(
                "aoa-kag-owner-evidence-ambiguous",
                review["reason_codes"],
            )
            self.assertIsNone(review["provider_watermark"])

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
            receipt_body.pop("attestation")
            receipt = _attested_payload(
                {
                    key: value
                    for key, value in receipt_body.items()
                    if key not in {"signer_id", "attestation_algorithm"}
                },
                "receipt_id",
            )
            _write_private_json(receipt_path, receipt)

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
                with patch(
                    "scripts.review_kag_mcp_result._utc_now",
                    return_value=NOW + timedelta(seconds=1),
                ):
                    review_kag_capture(
                        capture_root=root,
                        receipt_path=receipt_path,
                        artifact_path=lexical_path,
                        source_revision=revision,
                    )

    def test_recomputed_hashes_cannot_forge_stack_capture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt_path, result_path = _capture(root, _capture_payload())
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            forged_body = dict(receipt)
            forged_body.pop("receipt_id")
            forged_body.pop("attestation")
            forged_body["server_version"] = "forged"
            forged = {
                "receipt_id": _digest(forged_body),
                **forged_body,
                "attestation": "A" * 86,
            }
            forged_path = (
                root
                / "records"
                / "aoa-kag"
                / f"{forged['receipt_id'].removeprefix('sha256:')}.json"
            )
            _write_private_json(forged_path, forged)
            revision = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()

            with (
                patch(
                    "scripts.review_kag_mcp_result._utc_now",
                    return_value=NOW + timedelta(seconds=1),
                ),
                self.assertRaisesRegex(
                    KagOwnerReviewError,
                    "attestation does not verify",
                ),
            ):
                review_kag_capture(
                    capture_root=root,
                    receipt_path=forged_path,
                    artifact_path=result_path,
                    source_revision=revision,
                )

    def test_review_output_cannot_overwrite_capture_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt_path, result_path = _capture(root, _capture_payload())
            for output in (receipt_path, result_path):
                with self.subTest(output=output):
                    with self.assertRaisesRegex(
                        KagOwnerReviewError,
                        "must be distinct",
                    ):
                        _assert_distinct_io_paths(
                            receipt_path,
                            result_path,
                            output,
                        )

    def test_tampered_capture_and_public_inputs_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt_path, result_path = _capture(root, _capture_payload())
            os.chmod(result_path, 0o644)
            revision = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            with self.assertRaisesRegex(KagOwnerReviewError, "group/world"):
                with patch(
                    "scripts.review_kag_mcp_result._utc_now",
                    return_value=NOW + timedelta(seconds=1),
                ):
                    review_kag_capture(
                        capture_root=root,
                        receipt_path=receipt_path,
                        artifact_path=result_path,
                        source_revision=revision,
                    )
            os.chmod(result_path, 0o600)
            artifact = json.loads(result_path.read_text(encoding="utf-8"))
            artifact["owner_payload"]["owners"] = []
            _write_private_json(result_path, artifact)
            with self.assertRaisesRegex(KagOwnerReviewError, "content address"):
                with patch(
                    "scripts.review_kag_mcp_result._utc_now",
                    return_value=NOW + timedelta(seconds=1),
                ):
                    review_kag_capture(
                        capture_root=root,
                        receipt_path=receipt_path,
                        artifact_path=result_path,
                        source_revision=revision,
                    )

    def test_private_writer_keeps_review_mode_0600(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "reviews" / "review.json"
            _write_private_json(output, {"review": "bounded"})
            self.assertEqual(0o600, stat.S_IMODE(output.stat().st_mode))
            self.assertEqual(0o700, stat.S_IMODE(output.parent.stat().st_mode))

    def test_private_writer_does_not_chmod_existing_shared_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            shared = Path(directory) / "shared"
            shared.mkdir(mode=0o755)
            os.chmod(shared, 0o755)
            output = shared / "review.json"

            with self.assertRaisesRegex(
                KagOwnerReviewError,
                "must already be private",
            ):
                _write_private_json(output, {"review": "bounded"})

            self.assertEqual(0o755, stat.S_IMODE(shared.stat().st_mode))
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
