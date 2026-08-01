#!/usr/bin/env python3
"""Issue the KAG owner's exact source identity and stack overlay fragment."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections.abc import Callable, Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from review_kag_mcp_result import (
    GIT_NO_REPLACE,
    _canonical_source_index_identity,
    _digest,
    _git_revision,
    _write_private_json,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "schemas" / "kag-mcp-source-identity-receipt.schema.json"
SCHEMA_VERSION = "aoa_kag_mcp_source_identity_receipt_v1"
MAX_TTL_SECONDS = 7 * 24 * 60 * 60


class KagSourceIdentityError(ValueError):
    """The owner source cannot support an exact MCP identity receipt."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _time_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def _require_clean_git(repo_root: Path) -> None:
    for command in (
        [*GIT_NO_REPLACE, "diff", "--quiet", "HEAD", "--"],
        [*GIT_NO_REPLACE, "diff", "--cached", "--quiet", "HEAD", "--"],
    ):
        completed = subprocess.run(command, cwd=repo_root, check=False)
        if completed.returncode != 0:
            raise KagSourceIdentityError(
                "owner source identity requires a clean tracked Git snapshot"
            )


def _validate_receipt(receipt: dict[str, Any]) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(
        validator.iter_errors(receipt),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(item) for item in error.absolute_path) or "<root>"
        raise KagSourceIdentityError(
            f"source identity receipt failed schema at {location}: {error.message}"
        )
    unsigned = dict(receipt)
    claimed = unsigned.pop("receipt_digest")
    if _digest(unsigned) != claimed:
        raise KagSourceIdentityError("source identity receipt digest mismatch")


def issue_source_identity(
    *,
    repo_root: Path = REPO_ROOT,
    ttl_seconds: int = 24 * 60 * 60,
    clock: Callable[[], datetime] = _utc_now,
    require_clean: bool = True,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not 60 <= ttl_seconds <= MAX_TTL_SECONDS:
        raise KagSourceIdentityError("ttl-seconds must be between 60 and 604800")
    if require_clean:
        _require_clean_git(repo_root)
    revision = _git_revision(repo_root)
    source_digest, canonical_source_ref = _canonical_source_index_identity(revision)
    tree_digest = "sha256:" + source_digest.removeprefix("sha256:")
    issued_at = clock().astimezone(timezone.utc).replace(microsecond=0)
    expires_at = issued_at + timedelta(seconds=ttl_seconds)
    source_subject = {
        "owner": "aoa-kag",
        "revision": revision,
        "tree_digest": tree_digest,
        "expected_sync_tree_digest": tree_digest,
        "canonical_source_ref": canonical_source_ref,
        "issued_at": _time_text(issued_at),
        "expires_at": _time_text(expires_at),
    }
    subject_digest = _digest(source_subject).removeprefix("sha256:")
    source_ref = f"owner-source://aoa-kag/{revision}/{subject_digest}"
    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        **source_subject,
        "source_ref": source_ref,
        "contains_secrets": False,
        "claim_limits": [
            "This owner receipt identifies one clean committed KAG logical source tree.",
            "The tree digest is the canonical source-index identity, not a runtime projection digest.",
            "The receipt does not prove package deployment, consumer compatibility, central proof, acceptance, admission, or rollback.",
        ],
    }
    receipt["receipt_digest"] = _digest(receipt)
    _validate_receipt(receipt)
    evidence = {
        "state": "exact",
        "observed_at": receipt["issued_at"],
        "expires_at": receipt["expires_at"],
        "evidence_refs": [
            {
                "owner": "aoa-kag",
                "evidence_ref": source_ref,
                "revision": revision,
                "observed_at": receipt["issued_at"],
                "expires_at": receipt["expires_at"],
            }
        ],
        "reason_codes": [],
    }
    overlay = {
        "schema_version": "abyss_stack_runtime_evidence_overlay_v1",
        "generated_at": receipt["issued_at"],
        "expires_at": receipt["expires_at"],
        "contains_secrets": False,
        "subjects": [
            {
                "organ_id": "aoa-kag",
                "policy_family": "read",
                "source": {
                    "revision": revision,
                    "tree_digest": tree_digest,
                    "expected_sync_tree_digest": tree_digest,
                    "evidence": evidence,
                },
            }
        ],
    }
    return receipt, overlay


def write_outputs(
    receipt: dict[str, Any],
    overlay: dict[str, Any],
    output_root: Path,
) -> tuple[Path, Path]:
    root = output_root.expanduser().absolute()
    receipt_path = (
        root
        / "records"
        / (receipt["receipt_digest"].removeprefix("sha256:") + ".json")
    )
    overlay_path = root / "overlays" / "aoa-kag.read.source.json"
    _write_private_json(receipt_path, receipt)
    _write_private_json(overlay_path, overlay)
    return receipt_path, overlay_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--ttl-seconds", type=int, default=24 * 60 * 60)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        receipt, overlay = issue_source_identity(ttl_seconds=args.ttl_seconds)
        receipt_path, overlay_path = write_outputs(receipt, overlay, args.output_root)
    except KagSourceIdentityError as exc:
        print(f"aoa-kag MCP source identity: {exc}", file=__import__("sys").stderr)
        return 1
    print(f"receipt_path={receipt_path}")
    print(f"receipt_digest={receipt['receipt_digest']}")
    print(f"source_ref={receipt['source_ref']}")
    print(f"tree_digest={receipt['tree_digest']}")
    print(f"overlay_path={overlay_path}")
    print("owner_accepted=false")
    print("central_proof_asserted=false")
    print("contains_secrets=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
