#!/usr/bin/env python3
"""Project one exact KAG owner-result review into a stack evidence overlay."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from review_kag_mcp_result import (
    CAPTURE_RECEIPT_SCHEMAS,
    KAG_RESULT_SCHEMA,
    REVIEW_SCHEMA,
    KagOwnerReviewError,
    _assert_content_address,
    _aware_time,
    _digest,
    _git_revision,
    _require_reviewable_source_revision,
    _pinned_sdk_review_schema,
    _read_private_json,
    _write_private_json,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MAX_FUTURE_SKEW_SECONDS = 30


class KagOwnerReviewProjectionError(ValueError):
    """The owner review cannot support a usable stack overlay fragment."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _capture_path(capture_root: Path, relative_ref: Any) -> Path:
    if not isinstance(relative_ref, str) or not relative_ref:
        raise KagOwnerReviewProjectionError("capture receipt ref is unavailable")
    ref = PurePosixPath(relative_ref)
    if ref.is_absolute() or ".." in ref.parts:
        raise KagOwnerReviewProjectionError("capture receipt ref is not bounded")
    try:
        root = capture_root.expanduser().resolve(strict=True)
        candidate = (root / Path(*ref.parts)).resolve(strict=True)
        candidate.relative_to(root)
    except (OSError, ValueError) as exc:
        raise KagOwnerReviewProjectionError(
            "capture receipt ref escapes the capture root"
        ) from exc
    return candidate


def _validate_review(
    review: dict[str, Any],
    *,
    source_revision: str,
    schema_loader: Callable[[str], dict[str, Any]],
) -> None:
    schema = schema_loader(source_revision)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(
        validator.iter_errors(review),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        raise KagOwnerReviewProjectionError(
            "owner review does not satisfy the pinned SDK contract"
        )
    statement = dict(review)
    claimed = statement.pop("review_id", None)
    if claimed != _digest(statement, ensure_ascii=True):
        raise KagOwnerReviewProjectionError("owner review content address is invalid")
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
        "self_report_is_security_authority": False,
    }
    if any(review.get(field) != value for field, value in required.items()):
        raise KagOwnerReviewProjectionError(
            "owner review exceeds or does not meet the projection claim boundary"
        )
    owners = review.get("owners")
    expected_owners = {
        "source_owner": "aoa-kag",
        "access_owner": "aoa-kag",
        "control_owner": "aoa-sdk",
        "runtime_owner": "abyss-stack",
        "proof_owner": "aoa-evals",
        "acceptance_owner": "aoa-kag",
    }
    if owners != expected_owners:
        raise KagOwnerReviewProjectionError("owner review roles do not match KAG")
    if review.get("reason_codes") not in ([], ()):
        raise KagOwnerReviewProjectionError("exact owner review carries reason codes")
    watermark = review.get("provider_watermark")
    if not isinstance(watermark, str) or not watermark.startswith(
        "aoa-kag-source-index:"
    ):
        raise KagOwnerReviewProjectionError("owner freshness watermark is invalid")


def project_owner_review(
    *,
    review_path: Path,
    capture_root: Path,
    clock: Callable[[], datetime] = _utc_now,
    schema_loader: Callable[[str], dict[str, Any]] = _pinned_sdk_review_schema,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    review, _, _ = _read_private_json(review_path, "owner review")
    source = review.get("source_revision")
    source_revision = source.get("revision") if isinstance(source, dict) else None
    if not isinstance(source_revision, str):
        raise KagOwnerReviewProjectionError(
            "owner review source revision is unavailable"
        )
    try:
        _require_reviewable_source_revision(source_revision, repo_root=repo_root)
    except KagOwnerReviewError as exc:
        raise KagOwnerReviewProjectionError(str(exc)) from exc
    _validate_review(
        review,
        source_revision=source_revision,
        schema_loader=schema_loader,
    )

    now = clock().astimezone(timezone.utc)
    reviewed_at = _aware_time(review["reviewed_at"], "reviewed_at")
    expires_at = _aware_time(review["expires_at"], "review expires_at")
    if reviewed_at > now.replace(microsecond=now.microsecond) and (
        reviewed_at - now
    ).total_seconds() > MAX_FUTURE_SKEW_SECONDS:
        raise KagOwnerReviewProjectionError("owner review is causally future-dated")
    if expires_at <= now:
        raise KagOwnerReviewProjectionError("owner review is expired")

    capture = review.get("capture")
    if not isinstance(capture, dict):
        raise KagOwnerReviewProjectionError("owner review capture binding is absent")
    receipt_path = _capture_path(capture_root, capture.get("capture_receipt_ref"))
    receipt, _, _ = _read_private_json(receipt_path, "capture receipt")
    _assert_content_address(receipt, "receipt_id", "capture receipt")
    receipt_schema = receipt.get("schema_version")
    if receipt_schema not in CAPTURE_RECEIPT_SCHEMAS:
        raise KagOwnerReviewProjectionError("capture receipt schema is unsupported")
    if (
        receipt_schema != "abyss_stack_mcp_canary_receipt_v3"
        and source_revision != _git_revision(repo_root)
    ):
        raise KagOwnerReviewProjectionError(
            "legacy owner review projection is restricted to current aoa-kag HEAD"
        )
    expected_receipt = {
        "issuer": "abyss-stack",
        "consumer_id": "abyss-stack-mcp-canary",
        "organ_id": "aoa-kag",
        "policy_family": "read",
        "tool_name": "kag_discover",
        "call_succeeded": True,
        "result_contract_matched": True,
        "result_schema_identity": KAG_RESULT_SCHEMA,
        "contains_secrets": False,
        "content_trust": "untrusted_data",
        "instruction_authority": "none",
    }
    if any(receipt.get(field) != value for field, value in expected_receipt.items()):
        raise KagOwnerReviewProjectionError(
            "capture receipt does not support a successful grounded canary"
        )
    receipt_bindings = {
        "capture_receipt_id": "receipt_id",
        "result_digest": "result_digest",
        "result_schema_identity": "result_schema_identity",
        "server_schema_digest": "server_schema_digest",
    }
    if any(
        capture.get(review_field) != receipt.get(receipt_field)
        for review_field, receipt_field in receipt_bindings.items()
    ):
        raise KagOwnerReviewProjectionError(
            "owner review and capture receipt identities differ"
        )
    receipt_observed_at = _aware_time(receipt["observed_at"], "receipt observed_at")
    receipt_expires_at = _aware_time(receipt["expires_at"], "receipt expires_at")
    if (
        _aware_time(capture["observed_at"], "review capture observed_at")
        != receipt_observed_at
        or _aware_time(capture["expires_at"], "review capture expires_at")
        != receipt_expires_at
    ):
        raise KagOwnerReviewProjectionError(
            "owner review and capture receipt timestamps differ"
        )
    effective_expiry = min(expires_at, receipt_expires_at)
    if effective_expiry <= now:
        raise KagOwnerReviewProjectionError("owner-reviewed canary is expired")

    receipt_ref = receipt_path.as_posix()
    review_ref = review_path.expanduser().absolute().as_posix()
    canary_evidence = {
        "state": "exact",
        "observed_at": reviewed_at.isoformat(),
        "expires_at": effective_expiry.isoformat(),
        "evidence_refs": [
            {
                "owner": "abyss-stack",
                "evidence_ref": receipt_ref,
                "revision": receipt["receipt_id"],
                "observed_at": receipt_observed_at.isoformat(),
                "expires_at": receipt_expires_at.isoformat(),
            },
            {
                "owner": "aoa-kag",
                "evidence_ref": review_ref,
                "revision": review["review_id"],
                "observed_at": reviewed_at.isoformat(),
                "expires_at": expires_at.isoformat(),
            },
        ],
        "reason_codes": [],
    }
    endpoint_evidence = {
        "state": "exact",
        "observed_at": receipt_observed_at.isoformat(),
        "expires_at": receipt_expires_at.isoformat(),
        "evidence_refs": [canary_evidence["evidence_refs"][0]],
        "reason_codes": [],
    }
    freshness_evidence = {
        "state": "exact",
        "observed_at": reviewed_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "evidence_refs": [canary_evidence["evidence_refs"][1]],
        "reason_codes": [],
        "provider_watermark": review["provider_watermark"],
    }
    return {
        "schema_version": "abyss_stack_runtime_evidence_overlay_v1",
        "generated_at": reviewed_at.isoformat(),
        "expires_at": effective_expiry.isoformat(),
        "contains_secrets": False,
        "subjects": [
            {
                "organ_id": "aoa-kag",
                "policy_family": "read",
                "endpoint": {
                    "transport": "streamable-http",
                    "endpoint_ref": receipt["endpoint_ref"],
                    "protocol_versions": [receipt["protocol_version"]],
                    "ready": True,
                    "server_schema_digest": receipt["server_schema_digest"],
                    "evidence": endpoint_evidence,
                },
                "freshness": freshness_evidence,
                "canary": {
                    "succeeded": True,
                    "result_grounded": True,
                    "canary_route": receipt["canary_route"],
                    "canary_ref": receipt_ref,
                    "evidence": canary_evidence,
                },
            }
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--capture-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        overlay = project_owner_review(
            review_path=args.review,
            capture_root=args.capture_root,
        )
        _write_private_json(args.output, overlay)
    except (KagOwnerReviewError, KagOwnerReviewProjectionError) as exc:
        print(f"aoa-kag MCP owner-review projection: {exc}", file=sys.stderr)
        return 1
    subject = overlay["subjects"][0]
    print(f"overlay_path={args.output.expanduser().absolute()}")
    print(f"canary_ref={subject['canary']['canary_ref']}")
    print(f"expires_at={overlay['expires_at']}")
    print("result_grounded=true")
    print("freshness_state=exact")
    print("owner_accepted=false")
    print("central_proof_asserted=false")
    print("contains_secrets=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
