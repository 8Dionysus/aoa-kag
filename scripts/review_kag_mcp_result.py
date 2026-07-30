#!/usr/bin/env python3
"""Review one private stack-captured kag_discover result as the KAG owner."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[1]
OWNER_PAYLOAD_SCHEMA_REF = "owner://aoa-kag/schema/payload"
MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_REVIEW_TTL_SECONDS = 300
CAPTURE_RECEIPT_SCHEMA = "abyss_stack_mcp_canary_receipt_v1"
RESULT_ARTIFACT_SCHEMA = "abyss_stack_mcp_canary_result_artifact_v1"
REVIEW_SCHEMA = "aoa_organ_owner_result_review_v1"
KAG_RESULT_SCHEMA = "aoa-kag-mcp-capabilities-v1"
CAPABILITY_ID = "knowledge-retrieval"
PRIMITIVE_ID = "retrieve-knowledge"
REVIEW_CLAIM_LIMIT = (
    "This owner-issued review proves only the named owner's schema grounding "
    "and freshness assessment for one content-addressed captured result. It "
    "does not prove owner acceptance, central proof, admission, cross-organ "
    "benefit, execution authorization, or rollback."
)


class KagOwnerReviewError(ValueError):
    """The private capture cannot support an owner-bounded KAG review."""


def _canonical_json_bytes(value: Any, *, ensure_ascii: bool) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=ensure_ascii,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _digest(value: Any, *, ensure_ascii: bool = False) -> str:
    return (
        "sha256:"
        + hashlib.sha256(
            _canonical_json_bytes(value, ensure_ascii=ensure_ascii)
        ).hexdigest()
    )


def _aware_time(value: str | datetime, label: str) -> datetime:
    try:
        parsed = (
            value
            if isinstance(value, datetime)
            else datetime.fromisoformat(value.replace("Z", "+00:00"))
        )
    except ValueError as exc:
        raise KagOwnerReviewError(f"{label} is not a valid timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise KagOwnerReviewError(f"{label} must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _require_regular_private_file(path: Path, label: str) -> Path:
    absolute = path.expanduser().absolute()
    for component in (*reversed(absolute.parents), absolute):
        if component.is_symlink():
            raise KagOwnerReviewError(f"{label} cannot traverse a symlink")
    try:
        metadata = absolute.stat()
    except OSError as exc:
        raise KagOwnerReviewError(f"{label} is unavailable") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise KagOwnerReviewError(f"{label} must be a regular file")
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise KagOwnerReviewError(f"{label} must not be group/world accessible")
    if not 1 <= metadata.st_size <= MAX_INPUT_BYTES:
        raise KagOwnerReviewError(f"{label} has an invalid bounded size")
    return absolute


def _read_private_json(path: Path, label: str) -> dict[str, Any]:
    absolute = _require_regular_private_file(path, label)
    try:
        value = json.loads(absolute.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise KagOwnerReviewError(f"{label} is not valid JSON") from exc
    if not isinstance(value, dict):
        raise KagOwnerReviewError(f"{label} must be a JSON object")
    return value


def _read_public_json(path: Path, label: str) -> dict[str, Any]:
    absolute = path.expanduser().resolve()
    try:
        value = json.loads(absolute.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise KagOwnerReviewError(f"{label} is unavailable or invalid") from exc
    if not isinstance(value, dict):
        raise KagOwnerReviewError(f"{label} must be a JSON object")
    return value


def _read_public_schema(path: Path, label: str) -> dict[str, Any]:
    value = _read_public_json(path, label)
    Draft202012Validator.check_schema(value)
    return value


def _read_committed_public_json(
    source_revision: str,
    relative_path: str,
    label: str,
) -> tuple[dict[str, Any], bytes]:
    try:
        raw = subprocess.run(
            [
                "git",
                "show",
                f"{source_revision}:{relative_path}",
            ],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        ).stdout
        value = json.loads(raw.decode("utf-8"))
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
    ) as exc:
        raise KagOwnerReviewError(
            f"{label} is unavailable or invalid at source revision"
        ) from exc
    if not isinstance(value, dict):
        raise KagOwnerReviewError(
            f"{label} must be a JSON object at source revision"
        )
    return value, raw


def _committed_path_exists(source_revision: str, relative_path: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "cat-file", "-e", f"{source_revision}:{relative_path}"],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
        )
    except OSError as exc:
        raise KagOwnerReviewError(
            "aoa-kag committed evidence is unavailable"
        ) from exc
    return result.returncode == 0


def _relative_ref(root: Path, path: Path, label: str) -> str:
    try:
        resolved_root = root.expanduser().resolve(strict=True)
        resolved_path = path.expanduser().resolve(strict=True)
        return resolved_path.relative_to(resolved_root).as_posix()
    except (OSError, ValueError) as exc:
        raise KagOwnerReviewError(f"{label} is outside the capture root") from exc


def _assert_content_address(payload: dict[str, Any], identity: str, label: str) -> None:
    claimed = payload.get(identity)
    body = dict(payload)
    body.pop(identity, None)
    expected = _digest(body)
    if claimed != expected:
        raise KagOwnerReviewError(f"{label} content address does not match")


def _validate_capture(
    receipt: dict[str, Any],
    artifact: dict[str, Any],
    *,
    capture_root: Path,
    receipt_path: Path,
    artifact_path: Path,
) -> tuple[dict[str, Any], datetime, datetime, str, str]:
    if receipt.get("schema_version") != CAPTURE_RECEIPT_SCHEMA:
        raise KagOwnerReviewError("capture receipt schema is unsupported")
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
    for field, expected in expected_receipt.items():
        if receipt.get(field) != expected:
            raise KagOwnerReviewError(f"capture receipt {field} does not match")
    if receipt.get("reason_codes") not in ([], ()):
        raise KagOwnerReviewError("successful capture receipt carries failure reasons")
    _assert_content_address(receipt, "receipt_id", "capture receipt")

    if artifact.get("schema_version") != RESULT_ARTIFACT_SCHEMA:
        raise KagOwnerReviewError("result artifact schema is unsupported")
    expected_artifact = {
        "issuer": "abyss-stack",
        "organ_id": "aoa-kag",
        "policy_family": "read",
        "service_id": receipt.get("service_id"),
        "canary_route": receipt.get("canary_route"),
        "tool_name": "kag_discover",
        "tool_arguments_digest": receipt.get("tool_arguments_digest"),
        "observed_at": receipt.get("observed_at"),
        "result_schema_identity": KAG_RESULT_SCHEMA,
        "result_digest": receipt.get("result_digest"),
        "contains_secrets": False,
        "content_trust": "untrusted_data",
        "instruction_authority": "none",
    }
    for field, expected in expected_artifact.items():
        if artifact.get(field) != expected:
            raise KagOwnerReviewError(f"result artifact {field} does not match")
    _assert_content_address(artifact, "artifact_id", "result artifact")

    owner_payload = artifact.get("owner_payload")
    if not isinstance(owner_payload, dict):
        raise KagOwnerReviewError("result artifact owner payload must be an object")
    if _digest(owner_payload) != receipt.get("result_digest"):
        raise KagOwnerReviewError("owner payload digest does not match receipt")

    receipt_ref = _relative_ref(capture_root, receipt_path, "capture receipt")
    artifact_ref = _relative_ref(capture_root, artifact_path, "result artifact")
    if receipt.get("result_artifact_ref") != artifact_ref:
        raise KagOwnerReviewError("result artifact path does not match receipt")
    if not receipt_ref.startswith("records/aoa-kag/"):
        raise KagOwnerReviewError("capture receipt is outside the aoa-kag record lane")
    if not artifact_ref.startswith("results/aoa-kag/"):
        raise KagOwnerReviewError("result artifact is outside the aoa-kag result lane")

    observed_at = _aware_time(str(receipt.get("observed_at") or ""), "observed_at")
    expires_at = _aware_time(str(receipt.get("expires_at") or ""), "expires_at")
    if expires_at <= observed_at:
        raise KagOwnerReviewError("capture receipt expiry is invalid")
    return owner_payload, observed_at, expires_at, receipt_ref, artifact_ref


def _valid_digest(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )


def _canonical_source_index_identity(
    source_revision: str | None = None,
) -> tuple[str, str]:
    revision = source_revision or _git_revision(REPO_ROOT)
    manifest_ref = "kag/indexes/index_family.manifest.json"
    if _committed_path_exists(revision, manifest_ref):
        manifest, _ = _read_committed_public_json(
            revision,
            manifest_ref,
            "canonical KAG portable family manifest",
        )
        repo = manifest.get("repo")
        if not isinstance(repo, dict) or repo.get("name") != "aoa-kag":
            raise KagOwnerReviewError(
                "canonical KAG portable family owner does not match"
            )
        family_identity = manifest.get("family_identity")
        source_snapshot = (
            family_identity.get("source_snapshot")
            if isinstance(family_identity, dict)
            else None
        )
        source_header = manifest.get("source_index_header")
        header_identity = (
            source_header.get("index_identity")
            if isinstance(source_header, dict)
            else None
        )
        header_digest = (
            header_identity.get("content_digest")
            if isinstance(header_identity, dict)
            else None
        )
        compatibility = manifest.get("compatibility")
        files = compatibility.get("files") if isinstance(compatibility, dict) else None
        source_file_digests = (
            {
                str(item.get("content_digest"))
                for item in files
                if isinstance(item, dict)
                and item.get("kind") == "source"
                and _valid_digest(item.get("content_digest"))
            }
            if isinstance(files, list)
            else set()
        )
        digests = {
            str(source_snapshot).removeprefix("sha256:") if source_snapshot else "",
            str(header_digest or ""),
            *source_file_digests,
        }
        digests.discard("")
        if len(digests) != 1 or not _valid_digest(next(iter(digests), None)):
            raise KagOwnerReviewError(
                "canonical KAG portable source-index identities do not agree"
            )
        return next(iter(digests)), manifest_ref

    source_ref = "kag/indexes/source_surface_index.json"
    payload, _ = _read_committed_public_json(
        revision,
        source_ref,
        "canonical KAG source index",
    )
    identity = payload.get("index_identity")
    digest = identity.get("content_digest") if isinstance(identity, dict) else None
    if not _valid_digest(digest):
        raise KagOwnerReviewError(
            "canonical KAG source index identity is unavailable"
        )
    return str(digest), source_ref


def _freshness_assessment(
    payload: dict[str, Any],
    *,
    owner_canonical_digest: str,
) -> tuple[str, str | None, list[str], bool]:
    owners = payload.get("owners")
    matching_owners = (
        [
            item
            for item in owners
            if isinstance(item, dict) and item.get("repo") == "aoa-kag"
        ]
        if isinstance(owners, list)
        else []
    )
    if not matching_owners:
        return "blocked", None, ["aoa-kag-owner-evidence-missing"], False
    if len(matching_owners) != 1:
        return "blocked", None, ["aoa-kag-owner-evidence-ambiguous"], False
    owner = matching_owners[0]
    freshness = owner.get("freshness")
    if not isinstance(freshness, dict):
        return "blocked", None, ["aoa-kag-freshness-evidence-missing"], False
    owner_runtime_digest = owner.get("runtime_source_digest")
    runtime_digest = freshness.get("runtime_source_digest")
    canonical_digest = freshness.get("canonical_source_digest")
    state = freshness.get("state")
    if (
        owner_runtime_digest is not None
        and owner_runtime_digest != runtime_digest
    ):
        return (
            "blocked",
            f"aoa-kag-source-index:{owner_canonical_digest}",
            ["aoa-kag-runtime-source-digest-conflict"],
            False,
        )
    if (
        not _valid_digest(canonical_digest)
        or canonical_digest != owner_canonical_digest
    ):
        return (
            "blocked",
            f"aoa-kag-source-index:{owner_canonical_digest}",
            ["aoa-kag-canonical-source-digest-mismatch"],
            False,
        )
    if (
        state == "current"
        and _valid_digest(runtime_digest)
        and runtime_digest == canonical_digest
    ):
        return "exact", f"aoa-kag-source-index:{canonical_digest}", [], True
    if state in {"stale", "canonical_only"} and (
        _valid_digest(canonical_digest) or _valid_digest(runtime_digest)
    ):
        watermark = (
            canonical_digest if _valid_digest(canonical_digest) else runtime_digest
        )
        return (
            "stale_readable",
            f"aoa-kag-source-index:{watermark}",
            [f"aoa-kag-owner-freshness-{state}"],
            True,
        )
    return (
        "blocked",
        f"aoa-kag-source-index:{owner_canonical_digest}",
        ["aoa-kag-owner-freshness-blocked"],
        True,
    )


def _git_revision(repo_root: Path) -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise KagOwnerReviewError("aoa-kag source revision is unavailable") from exc


def review_kag_capture(
    *,
    capture_root: Path,
    receipt_path: Path,
    artifact_path: Path,
    sdk_review_schema_path: Path,
    source_revision: str,
    reviewed_at: datetime,
) -> dict[str, Any]:
    if source_revision != _git_revision(REPO_ROOT):
        raise KagOwnerReviewError(
            "requested source revision is not current aoa-kag HEAD"
        )
    reviewed_at = _aware_time(reviewed_at, "reviewed_at")
    receipt = _read_private_json(receipt_path, "capture receipt")
    artifact = _read_private_json(artifact_path, "result artifact")
    (
        owner_payload,
        observed_at,
        capture_expires_at,
        receipt_ref,
        artifact_ref,
    ) = _validate_capture(
        receipt,
        artifact,
        capture_root=capture_root,
        receipt_path=receipt_path,
        artifact_path=artifact_path,
    )
    if reviewed_at < observed_at or reviewed_at >= capture_expires_at:
        raise KagOwnerReviewError("review time is outside the live capture window")

    owner_schema, owner_schema_bytes = _read_committed_public_json(
        source_revision,
        "schemas/kag-mcp-capabilities.schema.json",
        "KAG capability schema",
    )
    Draft202012Validator.check_schema(owner_schema)
    sdk_schema = _read_public_schema(
        sdk_review_schema_path,
        "SDK owner-review schema",
    )
    schema_errors = sorted(
        Draft202012Validator(owner_schema).iter_errors(owner_payload),
        key=lambda error: list(error.absolute_path),
    )
    grounding_state = "rejected" if schema_errors else "grounded"
    reason_codes = ["owner-payload-schema-invalid"] if schema_errors else []
    owner_canonical_digest, canonical_evidence_ref = (
        _canonical_source_index_identity(source_revision)
    )
    (
        freshness_state,
        provider_watermark,
        freshness_reasons,
        canonical_identity_matched,
    ) = (
        _freshness_assessment(
            owner_payload,
            owner_canonical_digest=owner_canonical_digest,
        )
        if not schema_errors
        else ("blocked", None, [], False)
    )
    reason_codes.extend(freshness_reasons)
    if not schema_errors and not canonical_identity_matched:
        grounding_state = "rejected"
    distribution = owner_payload.get("distribution")
    projection = owner_payload.get("projection")
    if (
        not schema_errors
        and isinstance(projection, dict)
        and "distribution" in owner_payload
        and "distribution" in projection
        and distribution != projection.get("distribution")
    ):
        grounding_state = "rejected"
        freshness_state = "blocked"
        provider_watermark = None
        reason_codes.append("distribution-projection-binding-mismatch")

    expires_at = min(
        capture_expires_at,
        reviewed_at + timedelta(seconds=MAX_REVIEW_TTL_SECONDS),
    )
    schema_digest = "sha256:" + hashlib.sha256(owner_schema_bytes).hexdigest()
    statement = {
        "schema_version": REVIEW_SCHEMA,
        "review_owner": "aoa-kag",
        "organ_id": "aoa-kag",
        "capability_id": CAPABILITY_ID,
        "primitive_id": PRIMITIVE_ID,
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
            "result_artifact_ref": artifact_ref,
            "result_artifact_id": artifact["artifact_id"],
            "organ_id": "aoa-kag",
            "capability_id": CAPABILITY_ID,
            "primitive_id": PRIMITIVE_ID,
            "result_digest": receipt["result_digest"],
            "result_schema_identity": KAG_RESULT_SCHEMA,
            "server_schema_digest": receipt["server_schema_digest"],
            "primitive_schema_digest": receipt["selected_tool_schema_digest"],
            "observed_at": observed_at.isoformat(),
            "expires_at": capture_expires_at.isoformat(),
        },
        "source_revision": {
            "revision": source_revision,
            "schema_digest": schema_digest,
        },
        "owner_payload_schema_ref": OWNER_PAYLOAD_SCHEMA_REF,
        "owner_payload_schema_digest": schema_digest,
        "reviewed_at": reviewed_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "grounding_state": grounding_state,
        "freshness_state": freshness_state,
        "freshness_policy": {
            "policy_id": "kag-owner-source-parity-v1",
            "max_age_seconds": MAX_REVIEW_TTL_SECONDS,
            "stale_readable_seconds": 0,
            "cache_scope": "task",
            "provider_watermark_required": True,
        },
        "provider_watermark": provider_watermark,
        "grounding_evidence": (
            [
                {
                    "owner": "aoa-kag",
                    "evidence_ref": evidence_ref,
                    "revision": source_revision,
                    "observed_at": reviewed_at.isoformat(),
                    "expires_at": expires_at.isoformat(),
                }
                for evidence_ref in (
                    "schemas/kag-mcp-capabilities.schema.json",
                    canonical_evidence_ref,
                )
            ]
            if grounding_state == "grounded"
            else []
        ),
        "reason_codes": list(dict.fromkeys(reason_codes)),
        "owner_accepted": False,
        "central_proof_asserted": False,
        "admission_asserted": False,
        "cross_organ_proven": False,
        "rollback_proven": False,
        "contains_secrets": False,
        "self_report_is_security_authority": False,
        "claim_limit": REVIEW_CLAIM_LIMIT,
    }
    review = {
        **statement,
        "review_id": _digest(statement, ensure_ascii=True),
    }
    errors = sorted(
        Draft202012Validator(sdk_schema).iter_errors(review),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        raise KagOwnerReviewError(
            "produced owner review does not satisfy the SDK contract"
        )
    return review


def _write_private_json(path: Path, payload: dict[str, Any]) -> None:
    absolute = path.expanduser().absolute()
    for component in reversed(absolute.parents):
        if component.is_symlink():
            raise KagOwnerReviewError("review output cannot traverse a symlink")
    missing_parents: list[Path] = []
    cursor = absolute.parent
    while not cursor.exists():
        missing_parents.append(cursor)
        cursor = cursor.parent
    if not cursor.is_dir():
        raise KagOwnerReviewError("review output parent is not a directory")
    for parent in reversed(missing_parents):
        parent.mkdir(mode=0o700)
        os.chmod(parent, 0o700)
    parent_mode = stat.S_IMODE(absolute.parent.stat().st_mode)
    if parent_mode & 0o077:
        raise KagOwnerReviewError(
            "existing review output directory must already be private"
        )
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{absolute.name}.",
        dir=absolute.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, absolute)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture-root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--sdk-review-schema", type=Path, required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--reviewed-at")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    reviewed_at = (
        _aware_time(args.reviewed_at, "reviewed_at")
        if args.reviewed_at
        else datetime.now(timezone.utc)
    )
    review = review_kag_capture(
        capture_root=args.capture_root,
        receipt_path=args.receipt,
        artifact_path=args.result,
        sdk_review_schema_path=args.sdk_review_schema,
        source_revision=args.source_revision,
        reviewed_at=reviewed_at,
    )
    _write_private_json(args.output, review)
    print(
        json.dumps(
            {
                "review_id": review["review_id"],
                "grounding_state": review["grounding_state"],
                "freshness_state": review["freshness_state"],
                "output": str(args.output.expanduser().absolute()),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
