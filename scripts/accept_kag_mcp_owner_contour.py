#!/usr/bin/env python3
"""Accept one exact proved KAG MCP read contour without admitting it."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from review_kag_mcp_result import (
    REVIEW_SCHEMA,
    KagOwnerReviewError,
    _aware_time,
    _digest,
    _pinned_sdk_review_schema,
    _read_private_json,
    _require_reviewable_source_revision,
    _write_private_json,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE_SCHEMA = REPO_ROOT / "schemas" / "kag-mcp-owner-acceptance-receipt.schema.json"
SOURCE_SCHEMA = REPO_ROOT / "schemas" / "kag-mcp-source-identity-receipt.schema.json"
SCHEMA_VERSION = "aoa_kag_mcp_owner_acceptance_receipt_v1"
MAX_ACCEPTANCE_TTL_SECONDS = 300
MAX_FUTURE_SKEW_SECONDS = 30


class KagMcpAcceptanceError(ValueError):
    """The supplied evidence cannot support KAG owner acceptance."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise KagMcpAcceptanceError(f"{label} must be an object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise KagMcpAcceptanceError(f"{label} must be an array")
    return value


def _validate_schema(payload: dict[str, Any], path: Path, label: str) -> None:
    schema = json.loads(path.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(
            schema, format_checker=FormatChecker()
        ).iter_errors(payload),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        raise KagMcpAcceptanceError(f"{label} failed its owner schema")


def _validate_source_receipt(
    receipt: dict[str, Any],
    *,
    source_revision: str,
) -> tuple[datetime, str]:
    _validate_schema(receipt, SOURCE_SCHEMA, "source identity receipt")
    unsigned = dict(receipt)
    claimed = unsigned.pop("receipt_digest", None)
    if claimed != _digest(unsigned):
        raise KagMcpAcceptanceError("source identity content address is invalid")
    if (
        receipt.get("revision") != source_revision
        or receipt.get("owner") != "aoa-kag"
        or receipt.get("tree_digest") != receipt.get("expected_sync_tree_digest")
        or receipt.get("contains_secrets") is not False
    ):
        raise KagMcpAcceptanceError(
            "source identity does not name the selected deployed KAG revision"
        )
    return (
        _aware_time(receipt["expires_at"], "source receipt expires_at"),
        str(claimed),
    )


def _validate_owner_review(
    review: dict[str, Any],
    *,
    source_revision: str,
    schema_loader: Callable[[str], dict[str, Any]],
) -> tuple[datetime, str, dict[str, Any]]:
    errors = sorted(
        Draft202012Validator(
            schema_loader(source_revision), format_checker=FormatChecker()
        ).iter_errors(review),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        raise KagMcpAcceptanceError("owner result review failed the pinned SDK schema")
    statement = dict(review)
    claimed = statement.pop("review_id", None)
    if claimed != _digest(statement, ensure_ascii=True):
        raise KagMcpAcceptanceError("owner result review content address is invalid")
    source = _mapping(review.get("source_revision"), "owner review source")
    required = {
        "schema_version": REVIEW_SCHEMA,
        "review_owner": "aoa-kag",
        "organ_id": "aoa-kag",
        "capability_id": "knowledge-retrieval",
        "primitive_id": "retrieve-knowledge",
        "grounding_state": "grounded",
        "freshness_state": "exact",
        "owner_accepted": False,
        "central_proof_asserted": False,
        "admission_asserted": False,
        "cross_organ_proven": False,
        "rollback_proven": False,
        "contains_secrets": False,
    }
    if (
        any(review.get(field) != value for field, value in required.items())
        or source.get("revision") != source_revision
        or review.get("reason_codes") not in ([], ())
    ):
        raise KagMcpAcceptanceError("owner result review is not exact and bounded")
    capture = _mapping(review.get("capture"), "owner review capture")
    return (
        _aware_time(review["expires_at"], "owner review expires_at"),
        str(claimed),
        capture,
    )


def _validate_deployment_bound_capture(
    receipt: dict[str, Any],
    *,
    capture: dict[str, Any],
    package: dict[str, Any],
    deploy: dict[str, Any],
    endpoint: dict[str, Any],
    canary: dict[str, Any],
) -> datetime:
    if receipt.get("schema_version") != "abyss_stack_mcp_canary_receipt_v3":
        raise KagMcpAcceptanceError(
            "owner acceptance requires a deployment-bound v3 canary receipt"
        )
    body = dict(receipt)
    claimed = body.pop("receipt_id", None)
    body.pop("attestation", None)
    if claimed != _digest(body):
        raise KagMcpAcceptanceError(
            "deployment-bound canary content address is invalid"
        )
    required = {
        "issuer": "abyss-stack",
        "consumer_id": "abyss-stack-mcp-canary",
        "organ_id": "aoa-kag",
        "policy_family": "read",
        "service_id": "aoa-kag-mcp",
        "deployment_service_id": "aoa-kag-mcp",
        "tool_name": "kag_discover",
        "call_succeeded": True,
        "result_contract_matched": True,
        "contains_secrets": False,
        "content_trust": "untrusted_data",
        "instruction_authority": "none",
    }
    if any(receipt.get(field) != value for field, value in required.items()):
        raise KagMcpAcceptanceError("deployment-bound canary is not an exact KAG read")
    if receipt.get("reason_codes") not in ([], ()):
        raise KagMcpAcceptanceError("deployment-bound canary carries failure reasons")
    review_binding = {
        "capture_receipt_id": claimed,
        "result_digest": receipt.get("result_digest"),
        "result_schema_identity": receipt.get("result_schema_identity"),
        "server_schema_digest": receipt.get("server_schema_digest"),
        "primitive_schema_digest": receipt.get("selected_tool_schema_digest"),
        "observed_at": receipt.get("observed_at"),
        "expires_at": receipt.get("expires_at"),
    }
    if any(capture.get(field) != value for field, value in review_binding.items()):
        raise KagMcpAcceptanceError(
            "owner review does not bind the exact deployment canary"
        )
    runtime_binding = {
        "deployment_manifest_id": deploy.get("manifest_digest"),
        # This is the abyss-stack service-package source revision, not the
        # independently owner-reviewed aoa-kag canonical source revision.
        "deployment_source_revision": deploy.get("revision"),
        "deployment_package_digest": package.get("artifact_digest"),
        "deployment_tree_digest": deploy.get("tree_digest"),
        "canary_route": canary.get("canary_route"),
        "server_schema_digest": endpoint.get("server_schema_digest"),
    }
    if any(receipt.get(field) != value for field, value in runtime_binding.items()):
        raise KagMcpAcceptanceError(
            "deployment-bound canary targets a different runtime deployment"
        )
    protocols = endpoint.get("protocol_versions")
    if (
        not isinstance(protocols, list)
        or receipt.get("protocol_version") not in protocols
    ):
        raise KagMcpAcceptanceError(
            "deployment-bound canary protocol is absent from runtime endpoint"
        )
    observed_at = _aware_time(
        receipt.get("observed_at"), "deployment canary observed_at"
    )
    expires_at = _aware_time(
        receipt.get("expires_at"), "deployment canary expires_at"
    )
    deployed_at = _aware_time(
        receipt.get("deployment_deployed_at"), "deployment canary deployed_at"
    )
    if not deployed_at <= observed_at < expires_at:
        raise KagMcpAcceptanceError("deployment-bound canary time window is invalid")
    return expires_at


def _validate_proof_report(
    report: dict[str, Any],
    packet: dict[str, Any],
    *,
    report_path: Path,
    packet_path: Path,
) -> tuple[datetime, str]:
    required = {
        "schema_version": "aoa_organ_access_packet_review_v1",
        "eval_name": "aoa-organ-access-admission-integrity",
        "bundle_status": "bounded",
        "verdict": "supported_bounded",
        "central_proof_asserted": True,
        "owner_acceptance_inferred": False,
        "admission_change_authorized": False,
        "higher_effect_authorized": False,
        "cross_organ_benefit_asserted": False,
        "rollback_proven": False,
    }
    if (
        any(report.get(field) != value for field, value in required.items())
        or report.get("actual_effects") not in ([], ())
    ):
        raise KagMcpAcceptanceError("central proof report exceeds its bounded verdict")
    packet_binding = _mapping(report.get("packet"), "central proof packet binding")
    if (
        packet_binding.get("packet_ref") != packet_path.expanduser().absolute().as_posix()
        or packet_binding.get("packet_digest") != _digest(packet)
        or packet_binding.get("packet_id") != packet.get("packet_id")
        or packet_binding.get("organ_id") != "aoa-kag"
        or packet_binding.get("capability_id") != "knowledge-retrieval"
    ):
        raise KagMcpAcceptanceError("central proof report names a different packet")
    validation = _mapping(report.get("packet_validation"), "proof packet validation")
    suite = _mapping(report.get("negative_suite"), "proof negative suite")
    if (
        validation.get("accepted_by_source_contract") is not True
        or validation.get("issues") not in ([], ())
        or suite.get("verdict") != "supports bounded claim"
        or suite.get("failed_count") != 0
        or suite.get("passed_count") != suite.get("scenario_count")
    ):
        raise KagMcpAcceptanceError("central proof checks did not pass")
    report_digest = _digest(report)
    if report_path.stem != report_digest.removeprefix("sha256:"):
        raise KagMcpAcceptanceError("central proof record path is not content-addressed")
    return (
        _aware_time(report["reviewed_at"], "central proof reviewed_at"),
        report_digest,
    )


def _exact_link_expiry(link: dict[str, Any], label: str) -> datetime:
    if link.get("state") != "exact":
        raise KagMcpAcceptanceError(f"{label} is not exact")
    expiry = _aware_time(link.get("expires_at"), f"{label} expires_at")
    refs = _list(link.get("evidence_refs"), f"{label} evidence refs")
    if not refs:
        raise KagMcpAcceptanceError(f"{label} has no evidence refs")
    return min(
        [expiry]
        + [
            _aware_time(_mapping(ref, f"{label} evidence ref").get("expires_at"), f"{label} evidence ref expires_at")
            for ref in refs
            if _mapping(ref, f"{label} evidence ref").get("expires_at") is not None
        ]
    )


def _select_subject(observation: dict[str, Any]) -> dict[str, Any]:
    if (
        observation.get("schema_version") != "abyss_stack_runtime_observation_v1"
        or observation.get("provider") != "abyss-stack"
        or observation.get("contains_secrets") is not False
    ):
        raise KagMcpAcceptanceError("runtime observation is not a secret-free stack receipt")
    subjects = _list(observation.get("subjects"), "runtime observation subjects")
    matches = [
        subject
        for subject in subjects
        if isinstance(subject, dict)
        and subject.get("organ_id") == "aoa-kag"
        and subject.get("policy_family") == "read"
    ]
    if len(matches) != 1:
        raise KagMcpAcceptanceError("runtime observation lacks one KAG read contour")
    return matches[0]


def issue_acceptance(
    *,
    observation_path: Path,
    source_receipt_path: Path,
    owner_review_path: Path,
    proof_record_path: Path,
    packet_path: Path,
    clock: Callable[[], datetime] = _utc_now,
    schema_loader: Callable[[str], dict[str, Any]] = _pinned_sdk_review_schema,
    repo_root: Path = REPO_ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    observation, _, _ = _read_private_json(observation_path, "runtime observation")
    source_receipt, _, _ = _read_private_json(source_receipt_path, "source identity receipt")
    owner_review, _, _ = _read_private_json(owner_review_path, "owner result review")
    proof_report, _, _ = _read_private_json(proof_record_path, "central proof record")
    packet, _, _ = _read_private_json(packet_path, "central proof packet")
    subject = _select_subject(observation)
    source = _mapping(subject.get("source"), "runtime source")
    source_revision = source.get("revision")
    if not isinstance(source_revision, str):
        raise KagMcpAcceptanceError("runtime source revision is unavailable")
    _require_reviewable_source_revision(source_revision, repo_root=repo_root)
    source_expiry, source_receipt_digest = _validate_source_receipt(
        source_receipt, source_revision=source_revision
    )
    review_expiry, review_id, review_capture = _validate_owner_review(
        owner_review,
        source_revision=source_revision,
        schema_loader=schema_loader,
    )
    proof_time, proof_digest = _validate_proof_report(
        proof_report,
        packet,
        report_path=proof_record_path,
        packet_path=packet_path,
    )
    owners = _mapping(subject.get("owners"), "runtime owners")
    expected_owners = {
        "source_owner": "aoa-kag",
        "access_owner": "aoa-kag",
        "runtime_owner": "abyss-stack",
        "proof_owner": "aoa-evals",
        "acceptance_owner": "aoa-kag",
    }
    if owners != expected_owners:
        raise KagMcpAcceptanceError("runtime owner roles differ from KAG contract")

    package = _mapping(subject.get("package"), "runtime package")
    deploy = _mapping(subject.get("deploy"), "runtime deploy")
    process = _mapping(subject.get("process"), "runtime process")
    endpoint = _mapping(subject.get("endpoint"), "runtime endpoint")
    freshness = _mapping(subject.get("freshness"), "runtime freshness")
    canary = _mapping(subject.get("canary"), "runtime canary")
    proof = _mapping(subject.get("proof"), "runtime proof")
    consumers = _list(subject.get("consumers"), "runtime consumers")
    canary_ref = canary.get("canary_ref")
    if not isinstance(canary_ref, str) or not canary_ref.startswith("/"):
        raise KagMcpAcceptanceError(
            "runtime canary ref must be an absolute private record path"
        )
    canary_receipt, _, _ = _read_private_json(
        Path(canary_ref), "deployment-bound canary receipt"
    )
    canary_expiry = _validate_deployment_bound_capture(
        canary_receipt,
        capture=review_capture,
        package=package,
        deploy=deploy,
        endpoint=endpoint,
        canary=canary,
    )
    if (
        source.get("tree_digest") != source_receipt.get("tree_digest")
        or source.get("expected_sync_tree_digest") != source_receipt.get("tree_digest")
        or package.get("name") != "aoa-kag-mcp"
        or package.get("artifact_digest") != deploy.get("tree_digest")
        or process.get("active") is not True
        or endpoint.get("ready") is not True
        or freshness.get("state") != "exact"
        or freshness.get("provider_watermark") != owner_review.get("provider_watermark")
        or canary.get("succeeded") is not True
        or canary.get("result_grounded") is not True
        or proof.get("verdict") != "passed"
        or proof.get("proof_ref") != proof_record_path.expanduser().absolute().as_posix()
        or _aware_time(proof.get("evaluated_at"), "runtime proof evaluated_at")
        != proof_time
    ):
        raise KagMcpAcceptanceError("runtime contour does not match accepted evidence")
    proof_evidence = _mapping(proof.get("evidence"), "runtime proof evidence")
    proof_refs = _list(proof_evidence.get("evidence_refs"), "runtime proof refs")
    if not any(
        isinstance(ref, dict)
        and ref.get("owner") == "aoa-evals"
        and ref.get("evidence_ref") == proof.get("proof_ref")
        and ref.get("revision") == proof_digest
        for ref in proof_refs
    ):
        raise KagMcpAcceptanceError("runtime proof is not attributed to aoa-evals")
    proof_targets = {
        "proved_source_revision": source.get("revision"),
        "proved_source_tree_digest": source.get("tree_digest"),
        "proved_package_digest": package.get("artifact_digest"),
        "proved_deploy_revision": deploy.get("revision"),
        "proved_deploy_tree_digest": deploy.get("tree_digest"),
        "proved_deploy_manifest_digest": deploy.get("manifest_digest"),
        "proved_process_identity": process.get("process_identity"),
        "proved_server_schema_digest": endpoint.get("server_schema_digest"),
        "proved_canary_route": canary.get("canary_route"),
        "proved_canary_ref": canary.get("canary_ref"),
    }
    if any(proof.get(field) != value for field, value in proof_targets.items()):
        raise KagMcpAcceptanceError("central proof targets differ from runtime contour")
    registration_ref = proof.get("proved_consumer_registration_ref")
    compatible = [
        consumer
        for consumer in consumers
        if isinstance(consumer, dict)
        and consumer.get("registered") is True
        and consumer.get("registration_ref") == registration_ref
        and consumer.get("observed_schema_digest") == endpoint.get("server_schema_digest")
        and set(consumer.get("observed_protocol_versions", []))
        & set(endpoint.get("protocol_versions", []))
        and _mapping(consumer.get("evidence"), "consumer evidence").get("state") == "exact"
    ]
    if len(compatible) != 1:
        raise KagMcpAcceptanceError("proof-selected consumer is not exact and compatible")
    maturity = _mapping(packet.get("maturity"), "proof packet maturity")
    consumer_axis = _mapping(maturity.get("consumer_registered"), "packet consumer axis")
    if (
        consumer_axis.get("state") != "asserted"
        or consumer_axis.get("evidence_kind") != "consumer_registration"
        or consumer_axis.get("evidence_ref") != registration_ref
    ):
        raise KagMcpAcceptanceError("proof packet does not assert selected consumer")
    for forbidden in ("owner_accepted", "cross_organ_proven", "rollback_proven"):
        if _mapping(maturity.get(forbidden), f"packet {forbidden}").get("state") == "asserted":
            raise KagMcpAcceptanceError(f"pre-acceptance packet asserts {forbidden}")
    result = _mapping(packet.get("result"), "proof packet result")
    if (
        result.get("admission_change_authorized") is not False
        or result.get("owner_acceptance_inferred") is not False
        or result.get("higher_effect_authorized") is not False
    ):
        raise KagMcpAcceptanceError("proof packet exceeds its authority ceiling")
    source_refs = _list(_mapping(source.get("evidence"), "source evidence").get("evidence_refs"), "source refs")
    if not any(
        isinstance(ref, dict) and ref.get("evidence_ref") == source_receipt.get("source_ref")
        for ref in source_refs
    ):
        raise KagMcpAcceptanceError("runtime source does not carry source receipt ref")
    canary_refs = _list(_mapping(canary.get("evidence"), "canary evidence").get("evidence_refs"), "canary refs")
    if not any(
        isinstance(ref, dict)
        and ref.get("owner") == "aoa-kag"
        and ref.get("evidence_ref") == owner_review_path.expanduser().absolute().as_posix()
        and ref.get("revision") == review_id
        for ref in canary_refs
    ):
        raise KagMcpAcceptanceError("runtime canary does not carry exact owner review")

    now = clock().astimezone(timezone.utc)
    observation_expiry = _aware_time(observation.get("expires_at"), "observation expires_at")
    expiries = [
        observation_expiry,
        canary_expiry,
        source_expiry,
        review_expiry,
        _exact_link_expiry(_mapping(source.get("evidence"), "source evidence"), "source evidence"),
        _exact_link_expiry(_mapping(package.get("evidence"), "package evidence"), "package evidence"),
        _exact_link_expiry(_mapping(deploy.get("evidence"), "deploy evidence"), "deploy evidence"),
        _exact_link_expiry(_mapping(process.get("evidence"), "process evidence"), "process evidence"),
        _exact_link_expiry(_mapping(endpoint.get("evidence"), "endpoint evidence"), "endpoint evidence"),
        _exact_link_expiry(freshness, "freshness evidence"),
        _exact_link_expiry(_mapping(canary.get("evidence"), "canary evidence"), "canary evidence"),
        _exact_link_expiry(proof_evidence, "proof evidence"),
        _exact_link_expiry(_mapping(compatible[0].get("evidence"), "consumer evidence"), "consumer evidence"),
    ]
    if proof_time > now + timedelta(seconds=MAX_FUTURE_SKEW_SECONDS):
        raise KagMcpAcceptanceError("central proof is causally future-dated")
    if min(expiries) <= now:
        raise KagMcpAcceptanceError("acceptance input evidence is expired")
    accepted_at = now
    if accepted_at < proof_time:
        raise KagMcpAcceptanceError("owner acceptance cannot precede central proof")
    expires_at = min(
        min(expiries),
        accepted_at + timedelta(seconds=MAX_ACCEPTANCE_TTL_SECONDS),
    )
    source_contract = _mapping(proof_report.get("source_contract"), "proof source contract")
    packet_binding = _mapping(proof_report.get("packet"), "proof packet binding")
    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "organ_id": "aoa-kag",
        "capability_id": "knowledge-retrieval",
        "policy_family": "read",
        "decision": "accepted",
        "owners": {
            "source": "aoa-kag",
            "access": "aoa-kag",
            "control": "aoa-sdk",
            "runtime": "abyss-stack",
            "proof": "aoa-evals",
            "acceptance": "aoa-kag",
        },
        "accepted_at": accepted_at.isoformat().replace("+00:00", "Z"),
        "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
        "source": {
            "revision": source_revision,
            "tree_digest": source["tree_digest"],
            "source_ref": source_receipt["source_ref"],
            "source_receipt_digest": source_receipt_digest,
        },
        "package": {
            "name": package["name"],
            "version": package["version"],
            "artifact_digest": package["artifact_digest"],
            "deploy_revision": deploy["revision"],
            "deploy_tree_digest": deploy["tree_digest"],
            "deploy_manifest_digest": deploy["manifest_digest"],
        },
        "runtime_target": {
            "process_identity": process["process_identity"],
            "server_schema_digest": endpoint["server_schema_digest"],
            "consumer_registration_ref": registration_ref,
            "canary_route": canary["canary_route"],
            "canary_ref": canary["canary_ref"],
        },
        "central_proof": {
            "proof_ref": proof["proof_ref"],
            "proof_digest": proof_digest,
            "evaluated_at": proof_report["reviewed_at"],
            "eval_name": proof_report["eval_name"],
            "packet_ref": packet_binding["packet_ref"],
            "packet_digest": packet_binding["packet_digest"],
            "packet_id": packet_binding["packet_id"],
            "eval_digest": source_contract["eval_digest"],
            "manifest_digest": source_contract["manifest_digest"],
            "packet_schema_digest": source_contract["packet_schema_digest"],
        },
        "owner_result_review": {
            "review_ref": owner_review_path.expanduser().absolute().as_posix(),
            "review_id": review_id,
            "result_digest": owner_review["capture"]["result_digest"],
            "provider_watermark": owner_review["provider_watermark"],
        },
        "admission_authorized": False,
        "higher_effect_authorized": False,
        "cross_organ_benefit_asserted": False,
        "rollback_proven": False,
        "contains_secrets": False,
        "claim_limits": [
            "This receipt accepts one exact KAG MCP read contour at the named source and package identities.",
            "Acceptance follows the named aoa-evals bounded proof and does not reinterpret or strengthen that proof.",
            "This receipt does not authorize registry admission, process lifecycle changes, consumer reload, or higher effects.",
            "This receipt does not prove rollback, cross-organ benefit, protocol migration, or consumer-zero.",
        ],
    }
    receipt["receipt_digest"] = _digest(receipt)
    _validate_schema(receipt, ACCEPTANCE_SCHEMA, "acceptance receipt")
    return receipt, {}


def build_overlay(receipt: dict[str, Any], receipt_ref: str) -> dict[str, Any]:
    evidence = {
        "state": "exact",
        "observed_at": receipt["accepted_at"],
        "expires_at": receipt["expires_at"],
        "evidence_refs": [
            {
                "owner": "aoa-kag",
                "evidence_ref": receipt_ref,
                "revision": receipt["receipt_digest"],
                "observed_at": receipt["accepted_at"],
                "expires_at": receipt["expires_at"],
            }
        ],
        "reason_codes": [],
    }
    return {
        "schema_version": "abyss_stack_runtime_evidence_overlay_v1",
        "generated_at": receipt["accepted_at"],
        "expires_at": receipt["expires_at"],
        "contains_secrets": False,
        "subjects": [
            {
                "organ_id": "aoa-kag",
                "policy_family": "read",
                "acceptance": {
                    "accepted": True,
                    "acceptance_ref": receipt_ref,
                    "accepted_at": receipt["accepted_at"],
                    "accepted_source_revision": receipt["source"]["revision"],
                    "accepted_package_digest": receipt["package"]["artifact_digest"],
                    "evidence": evidence,
                },
            }
        ],
    }


def write_outputs(
    receipt: dict[str, Any], output_root: Path
) -> tuple[Path, Path, dict[str, Any]]:
    root = output_root.expanduser().absolute()
    record = root / "records" / (receipt["receipt_digest"].removeprefix("sha256:") + ".json")
    receipt_ref = record.as_posix()
    overlay = build_overlay(receipt, receipt_ref)
    overlay_path = root / "overlays" / "aoa-kag.read.acceptance.json"
    _write_private_json(record, receipt)
    _write_private_json(overlay_path, overlay)
    return record, overlay_path, overlay


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observation", type=Path, required=True)
    parser.add_argument("--source-receipt", type=Path, required=True)
    parser.add_argument("--owner-review", type=Path, required=True)
    parser.add_argument("--proof-record", type=Path, required=True)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        receipt, _ = issue_acceptance(
            observation_path=args.observation,
            source_receipt_path=args.source_receipt,
            owner_review_path=args.owner_review,
            proof_record_path=args.proof_record,
            packet_path=args.packet,
        )
        record, overlay_path, _ = write_outputs(receipt, args.output_root)
    except (KagOwnerReviewError, KagMcpAcceptanceError, OSError, KeyError) as exc:
        print(f"aoa-kag MCP owner acceptance: {exc}", file=sys.stderr)
        return 1
    print(f"receipt_path={record}")
    print(f"receipt_digest={receipt['receipt_digest']}")
    print(f"overlay_path={overlay_path}")
    print("owner_accepted=true")
    print("admission_authorized=false")
    print("rollback_proven=false")
    print("contains_secrets=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
