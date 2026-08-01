#!/usr/bin/env python3
"""Issue and verify the exact CI source-fast handoff receipt.

The receipt is deliberately ephemeral and workflow-run scoped.  It permits the
full audit job to continue after an already successful source-fast job only
when every local, donor, owner-family, command-authority, and workflow identity
can be recomputed exactly.  It is not a cross-run cache or an owner truth.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

try:  # Supports direct and package-style execution.
    from scripts import validation_lanes
    from scripts.provider_registry import provider_by_repo
    from scripts.repo_local.portable_family import manifest_digest
except ImportError:  # pragma: no cover - direct script execution
    import validation_lanes  # type: ignore
    from provider_registry import provider_by_repo  # type: ignore
    from repo_local.portable_family import manifest_digest  # type: ignore


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "aoa_kag_source_fast_handoff_v1"
RECEIPT_ENV = "AOA_KAG_SOURCE_FAST_HANDOFF"
EXPECTED_HISTORY_ENV = "AOA_KAG_EXPECTED_HISTORY_REF"
EXPECTED_EVENT_HISTORY_ENV = "AOA_KAG_EXPECTED_EVENT_HISTORY_REF"
PRODUCER_JOB = "source_fast"
FAMILY_MANIFEST_PATH = Path("kag/indexes/index_family.manifest.json")
ACTION_PATH = Path(".github/actions/repo-local-kag-index/action.yml")
HEX_40 = re.compile(r"^[0-9a-f]{40}$")
HEX_64 = re.compile(r"^[0-9a-f]{64}$")


class HandoffError(ValueError):
    """Raised when a receipt or one of its exact inputs is invalid."""


@dataclass(frozen=True)
class VerificationResult:
    accepted: bool
    reason: str
    receipt_digest: str = ""


def _canonical_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _digest(payload: object) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(
    repo_root: Path,
    *args: str,
    text: bool = True,
) -> str | bytes:
    result = subprocess.run(
        ("git", *args),
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=text,
    )
    return result.stdout


def _require_clean_git_checkout(repo_root: Path, label: str) -> None:
    status = str(
        _git(repo_root, "status", "--porcelain=v1", "--untracked-files=all")
    )
    if status:
        raise HandoffError(f"{label} checkout is not clean")


def _repository_identity(repo_root: Path) -> dict[str, str]:
    _require_clean_git_checkout(repo_root, "repository")
    commit_sha = str(_git(repo_root, "rev-parse", "HEAD")).strip()
    index_tree = str(_git(repo_root, "write-tree")).strip()
    raw_index = _git(repo_root, "ls-files", "-s", "-z", text=False)
    assert isinstance(raw_index, bytes)
    for entry in raw_index.split(b"\0"):
        if not entry:
            continue
        try:
            metadata, _path = entry.split(b"\t", 1)
            _mode, _object_id, stage = metadata.split(b" ", 2)
        except ValueError as exc:
            raise HandoffError("repository Git index is malformed") from exc
        if stage != b"0":
            raise HandoffError("repository Git index contains unmerged entries")
    if not HEX_40.fullmatch(commit_sha) or not HEX_40.fullmatch(index_tree):
        raise HandoffError("repository commit or index tree is not an exact SHA-1")
    return {
        "commit_sha": commit_sha,
        "index_tree": index_tree,
        "index_entries_sha256": hashlib.sha256(raw_index).hexdigest(),
    }


def _handoff_contract() -> dict[str, Any]:
    contract = validation_lanes.SOURCE_FAST_HANDOFF
    if contract.get("schema_version") != SCHEMA_VERSION:
        raise HandoffError("source-fast handoff schema version is not authoritative")
    donors = contract.get("donors")
    if not isinstance(donors, tuple) or not donors:
        raise HandoffError("source-fast handoff donor set is unavailable")
    return contract


def _donor_identities(env: Mapping[str, str]) -> list[dict[str, str]]:
    providers = provider_by_repo()
    records: list[dict[str, str]] = []
    for repo in _handoff_contract()["donors"]:
        entry = providers.get(repo)
        if entry is None:
            raise HandoffError(f"source-fast donor {repo!r} is missing from provider registry")
        env_name = str(entry.get("env") or "")
        expected_pin = str(entry.get("pinned_ref") or "")
        root_value = env.get(env_name, "")
        if not env_name or not root_value or not HEX_40.fullmatch(expected_pin):
            raise HandoffError(f"source-fast donor {repo!r} lacks an exact rooted pin")
        root = Path(root_value).resolve()
        _require_clean_git_checkout(root, f"donor {repo}")
        observed_head = str(_git(root, "rev-parse", "HEAD")).strip()
        if observed_head != expected_pin:
            raise HandoffError(
                f"source-fast donor {repo!r} HEAD {observed_head!r} does not match pin"
            )
        records.append(
            {
                "repo": repo,
                "env": env_name,
                "expected_pin": expected_pin,
                "observed_head": observed_head,
            }
        )
    return records


def _workflow_identity(env: Mapping[str, str]) -> dict[str, str]:
    fields = {
        "repository": env.get("GITHUB_REPOSITORY", ""),
        "run_id": env.get("GITHUB_RUN_ID", ""),
        "run_attempt": env.get("GITHUB_RUN_ATTEMPT", ""),
        "workflow_ref": env.get("GITHUB_WORKFLOW_REF", ""),
        "github_sha": env.get("GITHUB_SHA", ""),
        "producer_job": PRODUCER_JOB,
    }
    if any(not value for value in fields.values()):
        raise HandoffError("GitHub workflow identity is incomplete")
    if not fields["run_id"].isdigit() or not fields["run_attempt"].isdigit():
        raise HandoffError("GitHub workflow run identity is malformed")
    if not HEX_40.fullmatch(fields["github_sha"]):
        raise HandoffError("GitHub workflow SHA is malformed")
    return fields


def _history_identity(repo_root: Path, env: Mapping[str, str]) -> dict[str, str]:
    history_ref = env.get(EXPECTED_HISTORY_ENV, "")
    event_history_ref = env.get(EXPECTED_EVENT_HISTORY_ENV, "")
    if not HEX_40.fullmatch(history_ref) or not HEX_40.fullmatch(event_history_ref):
        raise HandoffError("owner-family history identity is incomplete")
    for label, ref in (
        ("history_ref", history_ref),
        ("event_history_ref", event_history_ref),
    ):
        try:
            _git(repo_root, "cat-file", "-e", f"{ref}^{{commit}}")
        except subprocess.CalledProcessError as exc:
            raise HandoffError(f"owner-family {label} is not an available commit") from exc
    return {"history_ref": history_ref, "event_history_ref": event_history_ref}


def _owner_family_identity(
    repo_root: Path,
    env: Mapping[str, str],
) -> dict[str, Any]:
    path = repo_root / FAMILY_MANIFEST_PATH
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise HandoffError("owner-family manifest is not an object")
    identity = payload.get("family_identity")
    source_header = payload.get("source_index_header")
    if not isinstance(identity, dict) or not isinstance(source_header, dict):
        raise HandoffError("owner-family manifest identity is incomplete")
    source_identity = source_header.get("index_identity")
    if not isinstance(source_identity, dict):
        raise HandoffError("owner-family source identity is incomplete")
    content_digest = identity.get("content_digest")
    source_digest = source_identity.get("content_digest")
    if not isinstance(content_digest, str) or not HEX_64.fullmatch(content_digest):
        raise HandoffError("owner-family content digest is malformed")
    if not isinstance(source_digest, str) or not HEX_64.fullmatch(source_digest):
        raise HandoffError("owner-family source digest is malformed")
    if content_digest != manifest_digest(payload):
        raise HandoffError("owner-family manifest digest does not verify")
    return {
        "result": "verified",
        "manifest_schema_version": str(payload.get("schema_version") or ""),
        "family_content_digest": content_digest,
        "source_index_content_digest": source_digest,
        **_history_identity(repo_root, env),
    }


def _command_authority(repo_root: Path) -> dict[str, str]:
    sequence = [list(command) for command in validation_lanes.SOURCE_FAST_COMMAND_SEQUENCE]
    return {
        "path": validation_lanes.VALIDATION_LANES_PATH.relative_to(repo_root).as_posix(),
        "sha256": _file_digest(validation_lanes.VALIDATION_LANES_PATH),
        "source_fast_sequence_sha256": _digest(sequence),
    }


def build_receipt(
    repo_root: Path = REPO_ROOT,
    env: Mapping[str, str] = os.environ,
) -> dict[str, Any]:
    repository = _repository_identity(repo_root)
    workflow = _workflow_identity(env)
    if workflow["github_sha"] != repository["commit_sha"]:
        raise HandoffError("GitHub workflow SHA does not match checked-out HEAD")
    authority = _command_authority(repo_root)
    donors = _donor_identities(env)
    owner_family = _owner_family_identity(repo_root, env)
    validator_inputs = {
        "sha256": _digest(
            {
                "repository": repository,
                "source_fast_sequence_sha256": authority[
                    "source_fast_sequence_sha256"
                ],
                "donors": donors,
            }
        )
    }
    builder_inputs = {
        "sha256": _digest(
            {
                "repository": repository,
                "action_sha256": _file_digest(repo_root / ACTION_PATH),
                "owner_family": owner_family,
            }
        ),
        "action_sha256": _file_digest(repo_root / ACTION_PATH),
    }
    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "result": "verified",
        "repository": repository,
        "command_authority": authority,
        "validator_inputs": validator_inputs,
        "builder_inputs": builder_inputs,
        "donors": donors,
        "owner_family": owner_family,
        "workflow": workflow,
    }
    receipt["receipt_digest"] = _digest(receipt)
    return receipt


def encode_receipt(receipt: Mapping[str, Any]) -> str:
    return base64.b64encode(_canonical_bytes(receipt)).decode("ascii")


def decode_receipt(encoded: str) -> dict[str, Any]:
    if not encoded:
        raise HandoffError("source-fast handoff receipt is missing")
    try:
        raw = base64.b64decode(encoded, validate=True)
        payload = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HandoffError("source-fast handoff receipt encoding is invalid") from exc
    if not isinstance(payload, dict):
        raise HandoffError("source-fast handoff receipt must be an object")
    return payload


def _require_exact_keys(payload: Mapping[str, Any], expected: set[str], where: str) -> None:
    actual = set(payload)
    if actual != expected:
        raise HandoffError(
            f"{where} fields are ambiguous: missing={sorted(expected - actual)} "
            f"unexpected={sorted(actual - expected)}"
        )


def _validate_shape(receipt: Mapping[str, Any]) -> None:
    _require_exact_keys(
        receipt,
        {
            "schema_version",
            "result",
            "repository",
            "command_authority",
            "validator_inputs",
            "builder_inputs",
            "donors",
            "owner_family",
            "workflow",
            "receipt_digest",
        },
        "receipt",
    )
    nested = {
        "repository": {"commit_sha", "index_tree", "index_entries_sha256"},
        "command_authority": {"path", "sha256", "source_fast_sequence_sha256"},
        "validator_inputs": {"sha256"},
        "builder_inputs": {"sha256", "action_sha256"},
        "owner_family": {
            "result",
            "manifest_schema_version",
            "family_content_digest",
            "source_index_content_digest",
            "history_ref",
            "event_history_ref",
        },
        "workflow": {
            "repository",
            "run_id",
            "run_attempt",
            "workflow_ref",
            "github_sha",
            "producer_job",
        },
    }
    for field, keys in nested.items():
        value = receipt.get(field)
        if not isinstance(value, dict):
            raise HandoffError(f"receipt.{field} must be an object")
        _require_exact_keys(value, keys, f"receipt.{field}")
    donors = receipt.get("donors")
    if not isinstance(donors, list) or not donors:
        raise HandoffError("receipt.donors must be a non-empty list")
    donor_keys = {"repo", "env", "expected_pin", "observed_head"}
    for index, donor in enumerate(donors):
        if not isinstance(donor, dict):
            raise HandoffError(f"receipt.donors[{index}] must be an object")
        _require_exact_keys(donor, donor_keys, f"receipt.donors[{index}]")
    scalar_strings: list[object] = [receipt.get("schema_version"), receipt.get("result")]
    for field in nested:
        scalar_strings.extend(receipt[field].values())  # type: ignore[index, union-attr]
    for donor in donors:
        scalar_strings.extend(donor.values())
    scalar_strings.append(receipt.get("receipt_digest"))
    if any(not isinstance(value, str) or not value for value in scalar_strings):
        raise HandoffError("source-fast handoff contains an empty or non-string field")


def verify_receipt(
    receipt: Mapping[str, Any],
    repo_root: Path = REPO_ROOT,
    env: Mapping[str, str] = os.environ,
) -> VerificationResult:
    try:
        _validate_shape(receipt)
        if receipt["schema_version"] != SCHEMA_VERSION:
            raise HandoffError("source-fast handoff schema version is unsupported")
        if receipt["result"] != "verified":
            raise HandoffError("source-fast handoff result is not verified")
        if receipt["owner_family"]["result"] != "verified":  # type: ignore[index]
            raise HandoffError("source-fast owner-family result is not verified")
        digest = str(receipt["receipt_digest"])
        unsigned = dict(receipt)
        del unsigned["receipt_digest"]
        if not HEX_64.fullmatch(digest) or digest != _digest(unsigned):
            raise HandoffError("source-fast handoff receipt digest does not verify")
        expected = build_receipt(repo_root, env)
        if dict(receipt) != expected:
            raise HandoffError("source-fast handoff identity does not match this audit job")
        return VerificationResult(True, "accepted", digest)
    except (ValueError, OSError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        return VerificationResult(False, str(exc))


def verify_encoded_receipt(
    encoded: str,
    repo_root: Path = REPO_ROOT,
    env: Mapping[str, str] = os.environ,
) -> VerificationResult:
    try:
        receipt = decode_receipt(encoded)
    except HandoffError as exc:
        return VerificationResult(False, str(exc))
    return verify_receipt(receipt, repo_root, env)


def _issue(args: argparse.Namespace) -> int:
    if os.environ.get("GITHUB_JOB") != PRODUCER_JOB:
        raise HandoffError(f"receipt may only be issued by GitHub job {PRODUCER_JOB!r}")
    receipt = build_receipt()
    encoded = encode_receipt(receipt)
    output_path = Path(args.github_output)
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(f"receipt={encoded}\n")
        handle.write(f"receipt-digest={receipt['receipt_digest']}\n")
    print(
        "[source-fast-handoff] issued "
        f"schema={SCHEMA_VERSION} digest={receipt['receipt_digest']}"
    )
    return 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    issue = subparsers.add_parser("issue", help="issue one verified handoff receipt")
    issue.add_argument("--github-output", required=True)
    issue.set_defaults(func=_issue)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        return int(args.func(args))
    except (ValueError, OSError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(f"[source-fast-handoff] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
