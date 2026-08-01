from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from project_kag_mcp_owner_review import (  # noqa: E402
    KagOwnerReviewProjectionError,
    project_owner_review,
)
from review_kag_mcp_result import (  # noqa: E402
    KagOwnerReviewError,
    _digest,
    _write_private_json,
)


NOW = datetime(2026, 8, 1, 3, 16, 16, tzinfo=timezone.utc)
DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64


def _source_revision() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _schema() -> dict:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["schema_version", "review_id"],
        "properties": {
            "schema_version": {"const": "aoa_organ_owner_result_review_v1"},
            "review_id": {"type": "string"},
        },
    }


def _inputs(root: Path) -> tuple[Path, Path]:
    capture_root = root / "capture"
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
        "tool_arguments_digest": DIGEST_A,
        "observed_at": NOW.isoformat(),
        "expires_at": (NOW + timedelta(minutes=10)).isoformat(),
        "protocol_version": "2025-11-25",
        "server_name": "aoa-kag-mcp",
        "server_version": "0.1.0",
        "server_schema_digest": DIGEST_A,
        "selected_tool_schema_digest": DIGEST_B,
        "inventory_counts": {"tools": 5, "resources": 0, "resource_templates": 9, "prompts": 0},
        "call_succeeded": True,
        "result_contract_matched": True,
        "result_schema_identity": "aoa-kag-mcp-capabilities-v1",
        "result_digest": DIGEST_B,
        "result_artifact_ref": "results/aoa-kag/example.json",
        "call_latency_ms": 4,
        "total_latency_ms": 12,
        "reason_codes": [],
        "contains_secrets": False,
        "content_trust": "untrusted_data",
        "instruction_authority": "none",
        "claim_limit": "stack capture only",
        "signer_id": DIGEST_A,
        "attestation_algorithm": "ed25519",
    }
    receipt = {"receipt_id": _digest(receipt_body), **receipt_body, "attestation": "A" * 86}
    receipt_ref = "records/aoa-kag/" + receipt["receipt_id"].removeprefix("sha256:") + ".json"
    receipt_path = capture_root / receipt_ref
    _write_private_json(receipt_path, receipt)

    revision = _source_revision()
    statement = {
        "schema_version": "aoa_organ_owner_result_review_v1",
        "review_owner": "aoa-kag",
        "organ_id": "aoa-kag",
        "capability_id": "knowledge-retrieval",
        "primitive_id": "retrieve-knowledge",
        "owners": {
            "source_owner": "aoa-kag",
            "access_owner": "aoa-kag",
            "control_owner": "aoa-sdk",
            "runtime_owner": "abyss-stack",
            "proof_owner": "aoa-evals",
            "acceptance_owner": "aoa-kag",
        },
        "capture": {
            "capture_owner": "abyss-stack",
            "capture_receipt_ref": receipt_ref,
            "capture_receipt_id": receipt["receipt_id"],
            "result_artifact_ref": receipt["result_artifact_ref"],
            "result_artifact_id": DIGEST_A,
            "organ_id": "aoa-kag",
            "capability_id": "knowledge-retrieval",
            "primitive_id": "retrieve-knowledge",
            "result_digest": receipt["result_digest"],
            "result_schema_identity": receipt["result_schema_identity"],
            "server_schema_digest": receipt["server_schema_digest"],
            "primitive_schema_digest": receipt["selected_tool_schema_digest"],
            "observed_at": receipt["observed_at"],
            "expires_at": receipt["expires_at"],
        },
        "source_revision": {"revision": revision, "schema_digest": DIGEST_A},
        "owner_payload_schema_ref": "owner://aoa-kag/schema/payload",
        "owner_payload_schema_digest": DIGEST_A,
        "reviewed_at": (NOW + timedelta(seconds=1)).isoformat(),
        "expires_at": (NOW + timedelta(minutes=5)).isoformat(),
        "grounding_state": "grounded",
        "freshness_state": "exact",
        "freshness_policy": {
            "policy_id": "kag-owner-source-parity-v1",
            "max_age_seconds": 300,
            "stale_readable_seconds": 0,
            "cache_scope": "task",
            "provider_watermark_required": True,
        },
        "provider_watermark": "aoa-kag-source-index:" + "c" * 64,
        "grounding_evidence": [],
        "reason_codes": [],
        "owner_accepted": False,
        "central_proof_asserted": False,
        "admission_asserted": False,
        "cross_organ_proven": False,
        "rollback_proven": False,
        "contains_secrets": False,
        "self_report_is_security_authority": False,
        "claim_limit": "bounded owner review only",
    }
    review = {**statement, "review_id": _digest(statement, ensure_ascii=True)}
    review_path = root / "review.json"
    _write_private_json(review_path, review)
    return review_path, capture_root


def _project(root: Path) -> dict:
    review, capture_root = _inputs(root)
    return project_owner_review(
        review_path=review,
        capture_root=capture_root,
        clock=lambda: NOW + timedelta(seconds=2),
        schema_loader=lambda _: _schema(),
    )


def test_projects_exact_grounding_and_freshness(tmp_path: Path) -> None:
    overlay = _project(tmp_path)
    subject = overlay["subjects"][0]

    assert subject["canary"]["succeeded"] is True
    assert subject["canary"]["result_grounded"] is True
    assert subject["canary"]["canary_ref"].endswith(".json")
    assert subject["canary"]["evidence"]["evidence_refs"][1]["owner"] == "aoa-kag"
    assert subject["endpoint"]["ready"] is True
    assert subject["endpoint"]["evidence"]["evidence_refs"][0]["owner"] == "abyss-stack"
    assert subject["freshness"]["state"] == "exact"
    assert subject["freshness"]["provider_watermark"].startswith("aoa-kag-source-index:")
    assert overlay["contains_secrets"] is False
    assert "acceptance" not in subject
    assert "proof" not in subject


def test_rejects_acceptance_laundering(tmp_path: Path) -> None:
    review_path, capture_root = _inputs(tmp_path)
    review = json.loads(review_path.read_text(encoding="utf-8"))
    review["owner_accepted"] = True
    statement = dict(review)
    statement.pop("review_id")
    review["review_id"] = _digest(statement, ensure_ascii=True)
    _write_private_json(review_path, review)

    with pytest.raises(KagOwnerReviewProjectionError, match="claim boundary"):
        project_owner_review(
            review_path=review_path,
            capture_root=capture_root,
            clock=lambda: NOW + timedelta(seconds=2),
            schema_loader=lambda _: _schema(),
        )


def test_rejects_changed_capture_receipt(tmp_path: Path) -> None:
    review_path, capture_root = _inputs(tmp_path)
    review = json.loads(review_path.read_text(encoding="utf-8"))
    receipt_path = capture_root / review["capture"]["capture_receipt_ref"]
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["server_schema_digest"] = DIGEST_B
    _write_private_json(receipt_path, receipt)

    with pytest.raises(KagOwnerReviewError, match="content address"):
        project_owner_review(
            review_path=review_path,
            capture_root=capture_root,
            clock=lambda: NOW + timedelta(seconds=2),
            schema_loader=lambda _: _schema(),
        )


def test_rejects_expired_review(tmp_path: Path) -> None:
    review_path, capture_root = _inputs(tmp_path)

    with pytest.raises(KagOwnerReviewProjectionError, match="expired"):
        project_owner_review(
            review_path=review_path,
            capture_root=capture_root,
            clock=lambda: NOW + timedelta(minutes=6),
            schema_loader=lambda _: _schema(),
        )
