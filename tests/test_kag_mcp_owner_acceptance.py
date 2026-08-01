from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker


REPO_ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE_EXAMPLE = REPO_ROOT / "examples" / "kag_mcp_owner_acceptance_receipt.example.json"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from accept_kag_mcp_owner_contour import (  # noqa: E402
    ACCEPTANCE_SCHEMA,
    KagMcpAcceptanceError,
    issue_acceptance,
    write_outputs,
)
from review_kag_mcp_result import _digest, _write_private_json  # noqa: E402


NOW = datetime(2026, 8, 1, 4, 0, tzinfo=timezone.utc)
DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64
DIGEST_C = "sha256:" + "c" * 64
DIGEST_D = "sha256:" + "d" * 64


def _revision() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _review_schema() -> dict:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["schema_version", "review_id"],
        "properties": {
            "schema_version": {"const": "aoa_organ_owner_result_review_v1"},
            "review_id": {"type": "string"},
        },
    }


def _link(owner: str, ref: str, revision: str) -> dict:
    return {
        "state": "exact",
        "observed_at": NOW.isoformat(),
        "expires_at": (NOW + timedelta(minutes=10)).isoformat(),
        "evidence_refs": [
            {
                "owner": owner,
                "evidence_ref": ref,
                "revision": revision,
                "observed_at": NOW.isoformat(),
                "expires_at": (NOW + timedelta(minutes=10)).isoformat(),
            }
        ],
        "reason_codes": [],
    }


def _inputs(root: Path) -> dict[str, Path]:
    revision = _revision()
    source_statement = {
        "schema_version": "aoa_kag_mcp_source_identity_receipt_v1",
        "owner": "aoa-kag",
        "revision": revision,
        "tree_digest": DIGEST_A,
        "expected_sync_tree_digest": DIGEST_A,
        "canonical_source_ref": "kag/indexes/index_family.manifest.json",
        "issued_at": (NOW - timedelta(minutes=1)).isoformat(),
        "expires_at": (NOW + timedelta(hours=1)).isoformat(),
        "source_ref": f"owner-source://aoa-kag/{revision}/" + "1" * 64,
        "contains_secrets": False,
        "claim_limits": ["source only", "not proof", "not acceptance"],
    }
    source_receipt = {
        **source_statement,
        "receipt_digest": _digest(source_statement),
    }
    source_path = root / "source.json"
    _write_private_json(source_path, source_receipt)

    review_statement = {
        "schema_version": "aoa_organ_owner_result_review_v1",
        "review_owner": "aoa-kag",
        "organ_id": "aoa-kag",
        "capability_id": "knowledge-retrieval",
        "primitive_id": "retrieve-knowledge",
        "source_revision": {"revision": revision, "schema_digest": DIGEST_A},
        "capture": {
            "result_digest": DIGEST_B,
            "capture_receipt_ref": "records/aoa-kag/canary.json",
        },
        "reviewed_at": NOW.isoformat(),
        "expires_at": (NOW + timedelta(minutes=10)).isoformat(),
        "grounding_state": "grounded",
        "freshness_state": "exact",
        "provider_watermark": "aoa-kag-source-index:" + "a" * 64,
        "reason_codes": [],
        "owner_accepted": False,
        "central_proof_asserted": False,
        "admission_asserted": False,
        "cross_organ_proven": False,
        "rollback_proven": False,
        "contains_secrets": False,
    }
    review = {
        **review_statement,
        "review_id": _digest(review_statement, ensure_ascii=True),
    }
    review_path = root / "owner-review.json"
    _write_private_json(review_path, review)

    registration_ref = "consumer-registration://8Dionysus/codex/aoa_kag/" + "2" * 64
    canary_ref = "/private/canaries/records/aoa-kag/canary.json"
    packet = {
        "schema_version": "organ_access_proof_packet_v1",
        "packet_id": "live.aoa-kag.read.acceptance-test",
        "organ_id": "aoa-kag",
        "capability_id": "knowledge-retrieval",
        "maturity": {
            "consumer_registered": {
                "state": "asserted",
                "evidence_kind": "consumer_registration",
                "evidence_ref": registration_ref,
            },
            "owner_accepted": {"state": "not_asserted"},
            "cross_organ_proven": {"state": "not_asserted"},
            "rollback_proven": {"state": "not_asserted"},
        },
        "result": {
            "verdict": "insufficient_evidence",
            "admission_change_authorized": False,
            "owner_acceptance_inferred": False,
            "higher_effect_authorized": False,
        },
    }
    packet_path = root / "packet.json"
    _write_private_json(packet_path, packet)
    report = {
        "schema_version": "aoa_organ_access_packet_review_v1",
        "eval_name": "aoa-organ-access-admission-integrity",
        "bundle_status": "bounded",
        "reviewed_at": (NOW + timedelta(seconds=1)).isoformat(),
        "packet": {
            "packet_ref": packet_path.absolute().as_posix(),
            "packet_digest": _digest(packet),
            "packet_id": packet["packet_id"],
            "organ_id": "aoa-kag",
            "capability_id": "knowledge-retrieval",
        },
        "source_contract": {
            "eval_digest": DIGEST_A,
            "manifest_digest": DIGEST_B,
            "packet_schema_digest": DIGEST_C,
        },
        "packet_validation": {"accepted_by_source_contract": True, "issues": []},
        "negative_suite": {
            "verdict": "supports bounded claim",
            "scenario_count": 11,
            "passed_count": 11,
            "failed_count": 0,
        },
        "verdict": "supported_bounded",
        "central_proof_asserted": True,
        "owner_acceptance_inferred": False,
        "admission_change_authorized": False,
        "higher_effect_authorized": False,
        "cross_organ_benefit_asserted": False,
        "rollback_proven": False,
        "actual_effects": [],
    }
    proof_digest = _digest(report)
    proof_path = root / (proof_digest.removeprefix("sha256:") + ".json")
    _write_private_json(proof_path, report)

    proof_link = _link("aoa-evals", proof_path.absolute().as_posix(), proof_digest)
    canary_link = _link("abyss-stack", canary_ref, DIGEST_D)
    canary_link["evidence_refs"].append(
        {
            "owner": "aoa-kag",
            "evidence_ref": review_path.absolute().as_posix(),
            "revision": review["review_id"],
            "observed_at": NOW.isoformat(),
            "expires_at": (NOW + timedelta(minutes=10)).isoformat(),
        }
    )
    subject = {
        "organ_id": "aoa-kag",
        "policy_family": "read",
        "owners": {
            "source_owner": "aoa-kag",
            "access_owner": "aoa-kag",
            "runtime_owner": "abyss-stack",
            "proof_owner": "aoa-evals",
            "acceptance_owner": "aoa-kag",
        },
        "source": {
            "revision": revision,
            "tree_digest": DIGEST_A,
            "expected_sync_tree_digest": DIGEST_A,
            "evidence": _link("aoa-kag", source_receipt["source_ref"], source_receipt["receipt_digest"]),
        },
        "package": {
            "name": "aoa-kag-mcp",
            "version": "0.1.0",
            "artifact_digest": DIGEST_B,
            "evidence": _link("abyss-stack", "deploy://manifest", DIGEST_C),
        },
        "deploy": {
            "revision": "stack-rev-1",
            "tree_digest": DIGEST_B,
            "manifest_digest": DIGEST_C,
            "evidence": _link("abyss-stack", "deploy://manifest", DIGEST_C),
        },
        "process": {
            "active": True,
            "process_identity": "systemd-user:aoa-kag:pid:1:start:1",
            "evidence": _link("abyss-stack", "process://aoa-kag", "stack-rev-1"),
        },
        "endpoint": {
            "ready": True,
            "server_schema_digest": DIGEST_D,
            "protocol_versions": ["2025-11-25"],
            "evidence": _link("abyss-stack", canary_ref, DIGEST_D),
        },
        "freshness": {
            **_link("aoa-kag", review_path.absolute().as_posix(), review["review_id"]),
            "provider_watermark": review["provider_watermark"],
        },
        "canary": {
            "succeeded": True,
            "result_grounded": True,
            "canary_route": "runbook://mcp-canary/aoa-kag/read",
            "canary_ref": canary_ref,
            "evidence": canary_link,
        },
        "proof": {
            "verdict": "passed",
            "proof_ref": proof_path.absolute().as_posix(),
            "evaluated_at": report["reviewed_at"],
            "proved_source_revision": revision,
            "proved_source_tree_digest": DIGEST_A,
            "proved_package_digest": DIGEST_B,
            "proved_deploy_revision": "stack-rev-1",
            "proved_deploy_tree_digest": DIGEST_B,
            "proved_deploy_manifest_digest": DIGEST_C,
            "proved_process_identity": "systemd-user:aoa-kag:pid:1:start:1",
            "proved_server_schema_digest": DIGEST_D,
            "proved_consumer_registration_ref": registration_ref,
            "proved_canary_route": "runbook://mcp-canary/aoa-kag/read",
            "proved_canary_ref": canary_ref,
            "evidence": proof_link,
        },
        "consumers": [
            {
                "consumer_id": "codex",
                "registration_ref": registration_ref,
                "registered": True,
                "observed_schema_digest": DIGEST_D,
                "observed_protocol_versions": ["2025-11-25"],
                "evidence": _link("8Dionysus", registration_ref, DIGEST_D),
            }
        ],
    }
    observation = {
        "schema_version": "abyss_stack_runtime_observation_v1",
        "provider": "abyss-stack",
        "contains_secrets": False,
        "generated_at": NOW.isoformat(),
        "expires_at": (NOW + timedelta(minutes=10)).isoformat(),
        "subjects": [subject],
    }
    observation_path = root / "observation.json"
    _write_private_json(observation_path, observation)
    return {
        "observation": observation_path,
        "source": source_path,
        "review": review_path,
        "proof": proof_path,
        "packet": packet_path,
    }


def _issue(paths: dict[str, Path], when: datetime = NOW + timedelta(seconds=2)):
    return issue_acceptance(
        observation_path=paths["observation"],
        source_receipt_path=paths["source"],
        owner_review_path=paths["review"],
        proof_record_path=paths["proof"],
        packet_path=paths["packet"],
        clock=lambda: when,
        schema_loader=lambda _: _review_schema(),
    )


def test_accepts_exact_proved_contour_without_admission(tmp_path: Path) -> None:
    receipt, _ = _issue(_inputs(tmp_path))
    schema = json.loads(ACCEPTANCE_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(receipt)
    unsigned = dict(receipt)
    claimed = unsigned.pop("receipt_digest")

    assert claimed == _digest(unsigned)
    assert receipt["decision"] == "accepted"
    assert receipt["admission_authorized"] is False
    assert receipt["rollback_proven"] is False
    assert receipt["central_proof"]["proof_digest"].startswith("sha256:")


def test_public_example_is_schema_valid_and_content_addressed() -> None:
    receipt = json.loads(ACCEPTANCE_EXAMPLE.read_text(encoding="utf-8"))
    schema = json.loads(ACCEPTANCE_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(receipt)
    unsigned = dict(receipt)
    claimed = unsigned.pop("receipt_digest")

    assert claimed == _digest(unsigned)


def test_outputs_private_acceptance_overlay(tmp_path: Path) -> None:
    receipt, _ = _issue(_inputs(tmp_path / "inputs"))
    record, overlay_path, overlay = write_outputs(receipt, tmp_path / "out")

    assert record.stat().st_mode & 0o777 == 0o600
    assert overlay_path.stat().st_mode & 0o777 == 0o600
    acceptance = overlay["subjects"][0]["acceptance"]
    assert acceptance["accepted"] is True
    assert acceptance["acceptance_ref"] == record.absolute().as_posix()
    assert acceptance["evidence"]["evidence_refs"][0]["owner"] == "aoa-kag"


def test_rejects_proof_target_drift(tmp_path: Path) -> None:
    paths = _inputs(tmp_path)
    observation = json.loads(paths["observation"].read_text(encoding="utf-8"))
    observation["subjects"][0]["proof"]["proved_server_schema_digest"] = DIGEST_A
    _write_private_json(paths["observation"], observation)

    with pytest.raises(KagMcpAcceptanceError, match="targets differ"):
        _issue(paths)


def test_rejects_expired_evidence(tmp_path: Path) -> None:
    paths = _inputs(tmp_path)

    with pytest.raises(KagMcpAcceptanceError, match="expired"):
        _issue(paths, NOW + timedelta(minutes=11))


def test_rejects_unbound_consumer(tmp_path: Path) -> None:
    paths = _inputs(tmp_path)
    observation = json.loads(paths["observation"].read_text(encoding="utf-8"))
    observation["subjects"][0]["consumers"][0]["observed_schema_digest"] = DIGEST_A
    _write_private_json(paths["observation"], observation)

    with pytest.raises(KagMcpAcceptanceError, match="consumer is not exact and compatible"):
        _issue(paths)


def test_rejects_non_content_addressed_proof_path(tmp_path: Path) -> None:
    paths = _inputs(tmp_path)
    wrong_path = tmp_path / "not-the-proof-digest.json"
    _write_private_json(
        wrong_path,
        json.loads(paths["proof"].read_text(encoding="utf-8")),
    )
    paths["proof"] = wrong_path

    with pytest.raises(KagMcpAcceptanceError, match="path is not content-addressed"):
        _issue(paths)


def test_rejects_future_dated_proof(tmp_path: Path) -> None:
    paths = _inputs(tmp_path)

    with pytest.raises(KagMcpAcceptanceError, match="causally future-dated"):
        _issue(paths, NOW - timedelta(minutes=1))
