#!/usr/bin/env python3
"""Generate an OS Abyss coverage report for repo-local KAG indexes."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import resource
import subprocess
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator, Sequence

from jsonschema import Draft202012Validator

try:
    from scripts.coverage_run import current_coverage_run, record_coverage_event
    from scripts.generate_repo_local_kag_index import (
        EXCLUDED_PARTS,
        INDEX_SCHEMA_VERSION,
        OwnerSourceSnapshot,
        REPOSITORY_INDEX_FILENAMES,
        SourceSnapshotError,
        build_index,
        build_repository_indexes,
        classification_summary,
        coverage_summary,
        effective_history_ref,
        git_file_paths,
        is_portable_family_control_path,
        manifest_validation_route,
        normalized_json,
        owner_type_for,
        payload_digest,
        repo_name,
        sha256_bytes,
        source_bytes,
        tiered_migration_provenance,
        tiered_previous_portable_manifest,
    )
    from scripts.generation.context import KNOWN_REPO_ROOTS
    from scripts.repo_local.portable_family import (
        MANIFEST_RELATIVE_PATH,
        OS_AGGREGATE_TRACKED_BYTES_MAX,
        build_portable_family,
        load_portable_family,
        reconstruct_source_index,
        receipt_path_for,
    )
    from scripts.repo_local.tiered_family import (
        DISTRIBUTION_SCHEMA_VERSION,
        OS_GIT_HOT_TARGET_BYTES,
        TieredFamilyUnavailable,
        build_tiered_family,
        check_tiered_git_surface,
        load_tiered_manifests,
        load_tiered_rows,
    )
    from scripts.provider_registry import (
        connector_repos,
        provider_by_repo,
        provider_roots,
        provider_repo_order,
    )
except ImportError:  # pragma: no cover - direct script execution
    from coverage_run import current_coverage_run, record_coverage_event  # type: ignore
    from generate_repo_local_kag_index import (  # type: ignore
        EXCLUDED_PARTS,
        INDEX_SCHEMA_VERSION,
        OwnerSourceSnapshot,
        REPOSITORY_INDEX_FILENAMES,
        SourceSnapshotError,
        build_index,
        build_repository_indexes,
        classification_summary,
        coverage_summary,
        effective_history_ref,
        git_file_paths,
        is_portable_family_control_path,
        manifest_validation_route,
        normalized_json,
        owner_type_for,
        payload_digest,
        repo_name,
        sha256_bytes,
        source_bytes,
        tiered_migration_provenance,
        tiered_previous_portable_manifest,
    )
    from generation.context import KNOWN_REPO_ROOTS  # type: ignore
    from repo_local.portable_family import (  # type: ignore
        MANIFEST_RELATIVE_PATH,
        OS_AGGREGATE_TRACKED_BYTES_MAX,
        build_portable_family,
        load_portable_family,
        reconstruct_source_index,
        receipt_path_for,
    )
    from repo_local.tiered_family import (  # type: ignore
        DISTRIBUTION_SCHEMA_VERSION,
        OS_GIT_HOT_TARGET_BYTES,
        TieredFamilyUnavailable,
        build_tiered_family,
        check_tiered_git_surface,
        load_tiered_manifests,
        load_tiered_rows,
    )
    from provider_registry import (  # type: ignore
        connector_repos,
        provider_by_repo,
        provider_roots,
        provider_repo_order,
    )


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OS_ROOT = Path("/srv/AbyssOS")
DEFAULT_OUTPUT = REPO_ROOT / "generated" / "repo_local_kag_coverage.json"
DEFAULT_MIN_OUTPUT = REPO_ROOT / "generated" / "repo_local_kag_coverage.min.json"
COVERAGE_PACKET_SCHEMA_VERSION = "aoa-kag-coverage-build-packet-v1"
COVERAGE_IDENTITY_SCHEMA_VERSION = "aoa-kag-coverage-input-identity-v1"
COVERAGE_CANONICALIZATION_EPOCH = "portable-record-normalization-v3"
COVERAGE_IDENTITY_FIELDS = {
    "schema_version",
    "run_scope_id",
    "lane",
    "display_os_root",
    "canonicalization_epoch",
    "index_schema_epoch",
    "provider_registry_digest",
    "coverage_schema_digest",
    "family_manifest_schema_digest",
    "repository_index_schema_digest",
    "runtime_inputs_digest",
    "owner_snapshots",
}
COVERAGE_OWNER_SNAPSHOT_FIELDS = {
    "owner",
    "root",
    "expected_ref",
    "head_commit",
    "index_tree",
    "worktree_digest",
    "manifest_digest",
    "family_content_digest",
    "source_snapshot",
    "event_content_digest",
}
OWNER_STATUS = ("passed", "migration-needed", "missing", "owner-specific")
INDEX_SCHEMA_PATH = REPO_ROOT / "schemas" / "repo-local-kag-index.schema.json"
FAMILY_MANIFEST_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "repo-local-kag-family-manifest.schema.json"
)
REPOSITORY_INDEX_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "repo-local-kag-repository-index.schema.json"
)
COVERAGE_SCHEMA_PATH = REPO_ROOT / "schemas" / "repo-local-kag-coverage.schema.json"
LOCAL_KAG_SUBTREE_SCHEMA_PATH = REPO_ROOT / "schemas" / "local-kag-subtree.schema.json"
SOURCE_SURFACE_INDEX_REL = Path("kag/indexes/source_surface_index.json")
REPOSITORY_INDEX_RELS = {
    Path("kag") / "indexes" / filename
    for filename in REPOSITORY_INDEX_FILENAMES.values()
}
COMMON_GENERATED_INDEX_RELS = {SOURCE_SURFACE_INDEX_REL, *REPOSITORY_INDEX_RELS}
REPOSITORY_INDEX_FAMILY_REFS = {
    "source": SOURCE_SURFACE_INDEX_REL.as_posix(),
    **{
        index_kind: (Path("kag") / "indexes" / filename).as_posix()
        for index_kind, filename in REPOSITORY_INDEX_FILENAMES.items()
    },
}
DOMAIN_INDEX_CATALOG_REF = "kag/indexes/domain_index_catalog.json"
META_INDEX_NAMES = {
    SOURCE_SURFACE_INDEX_REL.name,
    *(path.name for path in REPOSITORY_INDEX_RELS),
    "domain_index_catalog.json",
}
PROVIDER_REPO_ORDER = provider_repo_order()
CONNECTOR_REPOS = connector_repos()
COVERAGE_RUNTIME_INPUT_PATHS = (
    Path("config/validation_lanes.json"),
    Path("manifests/provider_registry.json"),
    Path("schemas/local-kag-subtree.schema.json"),
    Path("schemas/repo-local-kag-coverage.schema.json"),
    Path("schemas/repo-local-kag-family-manifest.schema.json"),
    Path("schemas/repo-local-kag-index.schema.json"),
    Path("schemas/repo-local-kag-repository-index.schema.json"),
    Path("scripts/coverage_run.py"),
    Path("scripts/generate_repo_local_kag_coverage.py"),
    Path("scripts/generate_repo_local_kag_index.py"),
    Path("scripts/generation/context.py"),
    Path("scripts/provider_registry.py"),
    Path("scripts/validators/common.py"),
    Path("scripts/validators/local_kag_subtree.py"),
    Path("scripts/validators/repo_local_kag_index.py"),
)
OWNER_SPECIFIC_INDEX_NAMES = {
    "session_memory_source_inventory.json",
    "source_inventory.json",
}
OWNER_SPECIFIC_OWNER_TYPES = {
    "bundle_provider",
    "connector",
}
PROVIDER_RECORD_DIRS = ("nodes", "edges", "indexes", "projections", "receipts")
COMMON_PROFILE_COUNT_KEYS = (
    "artifact_kind",
    "primary_kind",
    "surface_state",
    "document_role",
    "mechanics_role",
    "command_role",
)
LOCAL_KAG_RECORD_SCHEMA_VERSION = "aoa-local-kag-record-v1"
PROVIDER_RECORD_SCHEMA_DEFS = {
    "nodes": "nodeRecord",
    "edges": "edgeRecord",
    "indexes": "indexRecord",
    "projections": "projectionRecord",
    "receipts": "receiptRecord",
}

PortableBundle = tuple[
    dict[str, Any],
    dict[str, dict[str, Any]],
    dict[str, Any],
]


@dataclass
class _ProviderCoveragePrebuild:
    run_scope_id: str
    os_root: Path
    identity: dict[str, Any]
    owner_roots: tuple[tuple[str, Path], ...]
    owners: dict[str, dict[str, Any]] = field(default_factory=dict)
    owner_timings: dict[str, dict[str, Any]] = field(default_factory=dict)
    strategy: str = "provider-home-fused"


_ACTIVE_PROVIDER_COVERAGE_PREBUILD: _ProviderCoveragePrebuild | None = None
_TRANSIENT_PORTABLE_BUNDLE: tuple[Path, PortableBundle] | None = None


def coverage_progress(label: str) -> None:
    print(f"[repo-local-kag-coverage] {label}", file=sys.stderr, flush=True)


def local_kag_record_schema(def_name: str, *, schema_id_suffix: str) -> dict[str, Any]:
    schema = json.loads(LOCAL_KAG_SUBTREE_SCHEMA_PATH.read_text(encoding="utf-8"))
    if not isinstance(schema, dict):
        raise ValueError("local KAG subtree schema must be an object")
    wrapper = {
        "$schema": schema.get("$schema"),
        "$id": f"{schema.get('$id', 'local-kag-subtree')}.{schema_id_suffix}.json",
        "$defs": schema.get("$defs", {}),
        "$ref": f"#/$defs/{def_name}",
    }
    Draft202012Validator.check_schema(wrapper)
    return wrapper


def local_kag_index_record_schema() -> dict[str, Any]:
    return local_kag_record_schema("indexRecord", schema_id_suffix="indexRecord.coverage")


def local_kag_provider_record_schemas() -> dict[str, dict[str, Any]]:
    return {
        group_name: local_kag_record_schema(def_name, schema_id_suffix=f"{def_name}.coverage")
        for group_name, def_name in PROVIDER_RECORD_SCHEMA_DEFS.items()
    }


def git_root(path: Path) -> Path | None:
    try:
        output = subprocess.run(
            ("git", "rev-parse", "--show-toplevel"),
            cwd=path,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return Path(output).resolve()


def direct_owner_roots(os_root: Path) -> list[Path]:
    roots: list[Path] = []
    for child in os_root.iterdir() if os_root.is_dir() else ():
        if child.name.startswith(".") or not child.is_dir():
            continue
        if child.name in {"connectors", "bundles", "Services"}:
            continue
        if child.name.startswith("aoa-") or child.name in {
            "Agents-of-Abyss",
            "Tree-of-Sophia",
            "8Dionysus",
            "Dionysus",
            "ATM10-Agent",
        }:
            roots.append(child)
    for parent_name in ("connectors", "bundles"):
        parent = os_root / parent_name
        if parent.is_dir():
            roots.extend(child for child in parent.iterdir() if child.is_dir() and not child.name.startswith("."))
    return sorted({root.resolve() for root in roots}, key=lambda path: path.as_posix())


def source_counts(
    owner_root: Path,
    *,
    source_snapshot: OwnerSourceSnapshot | None = None,
) -> dict[str, int]:
    counts = {
        "documents": 0,
        "mechanics": 0,
        "commands": 0,
        "validators": 0,
        "tests": 0,
        "scripts": 0,
        "schemas": 0,
        "generated": 0,
    }
    paths = (
        sorted(source_snapshot.entries)
        if source_snapshot is not None
        else git_file_paths(owner_root)
    )
    for rel in paths:
        if (EXCLUDED_PARTS | {".deps", "dist"}).intersection(rel.parts):
            continue
        if rel.suffix == ".md":
            counts["documents"] += 1
        if "mechanics" in rel.parts:
            counts["mechanics"] += 1
        if "scripts" in rel.parts and rel.suffix in {".py", ".sh"}:
            counts["scripts"] += 1
            counts["commands"] += 1
        if rel.name.startswith("validate_") or "validators" in rel.parts:
            counts["validators"] += 1
        if "tests" in rel.parts and rel.suffix == ".py":
            counts["tests"] += 1
            counts["commands"] += 1
        if "schemas" in rel.parts or rel.name.endswith(".schema.json"):
            counts["schemas"] += 1
        if "generated" in rel.parts:
            counts["generated"] += 1
    return counts


def canonical_owner_root(os_root: Path, repo: str) -> Path:
    if repo == "aoa-kag":
        return os_root / repo
    canonical_roots = provider_roots(os_root=os_root)
    if repo in canonical_roots:
        return canonical_roots[repo]
    if repo in CONNECTOR_REPOS:
        return os_root / "connectors" / repo
    if repo == "aoa-session-memory":
        return os_root / "bundles" / repo
    return os_root / repo


def configured_owner_roots() -> list[tuple[str, Path]]:
    return [(repo, KNOWN_REPO_ROOTS[repo].resolve()) for repo in PROVIDER_REPO_ORDER]


def source_index_matches_owner(
    owner_root: Path,
    payload: dict[str, Any],
    *,
    source_snapshot: OwnerSourceSnapshot | None = None,
) -> bool:
    source_snapshot = source_snapshot or OwnerSourceSnapshot.capture(owner_root)
    repo = repo_name(owner_root, source_snapshot=source_snapshot)
    repo_payload = payload.get("repo")
    if not isinstance(repo_payload, dict) or repo_payload.get("name") != repo:
        return False
    records = payload.get("records")
    summary = payload.get("coverage_summary")
    identity = payload.get("index_identity")
    if not isinstance(records, list) or not isinstance(summary, dict) or not isinstance(identity, dict):
        return False
    if identity.get("content_digest") != payload_digest(payload):
        return False
    if summary.get("record_count") != len(records):
        return False
    indexed_paths: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            return False
        identity = record.get("identity")
        if not isinstance(identity, dict):
            return False
        if identity.get("repo") != repo:
            return False
        rel_path = identity.get("path")
        if not isinstance(rel_path, str) or not rel_path:
            return False
        if rel_path in indexed_paths:
            return False
        indexed_paths.add(rel_path)
    try:
        if summary != coverage_summary(records):
            return False
    except (KeyError, TypeError):
        return False
    expected_paths = {
        rel.as_posix()
        for rel in source_snapshot.entries
        if rel not in COMMON_GENERATED_INDEX_RELS
        and not is_portable_family_control_path(rel)
    }
    if indexed_paths != expected_paths:
        return False
    for record in records:
        identity = record["identity"]
        rel_path = identity["path"]
        if rel_path.startswith("generated/repo_local_kag_coverage"):
            continue
        rel = Path(rel_path)
        try:
            content = source_bytes(
                owner_root,
                rel,
                owner_root / rel,
                source_snapshot=source_snapshot,
            )
        except (
            FileNotFoundError,
            IsADirectoryError,
            subprocess.CalledProcessError,
            SourceSnapshotError,
        ):
            return False
        digest = sha256_bytes(content)
        if identity.get("content_hash") != digest:
            return False
        signs = record.get("signs")
        if isinstance(signs, dict) and signs.get("digest") != digest:
            return False
    return True


def _count_map(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, int] = {}
    for key, count in value.items():
        if isinstance(key, str) and isinstance(count, int) and count >= 0:
            result[key] = count
    return dict(sorted(result.items()))


def _source_index_payload(owner_root: Path) -> dict[str, Any] | None:
    source_index = owner_root / SOURCE_SURFACE_INDEX_REL
    try:
        payload = json.loads(source_index.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError, IsADirectoryError):
        payload = None
    if isinstance(payload, dict) and payload.get("schema_version") == INDEX_SCHEMA_VERSION:
        return payload
    portable = _portable_bundle(owner_root)
    if portable is not None:
        return portable[0]
    tiered = _tiered_bundle(owner_root)
    if tiered is not None:
        return tiered[0]
    return None


def portable_family_profile(
    owner_root: Path,
    *,
    owner_name: str,
    status: str,
) -> tuple[str, dict[str, Any]]:
    manifest_path = owner_root / MANIFEST_RELATIVE_PATH
    try:
        raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
        raw_manifest = None
    if (
        isinstance(raw_manifest, dict)
        and raw_manifest.get("schema_version") == DISTRIBUTION_SCHEMA_VERSION
    ):
        artifact_root_value = os.environ.get("KAG_ARTIFACT_ROOT")
        artifact_root = (
            Path(artifact_root_value).expanduser().resolve()
            if artifact_root_value
            else None
        )
        try:
            distribution, corpus, _, _, _ = load_tiered_manifests(
                owner_root,
                artifact_root=artifact_root,
            )
        except (ValueError, FileNotFoundError, json.JSONDecodeError):
            placement = raw_manifest.get("placement")
            placement_state = (
                placement.get("state")
                if isinstance(placement, dict)
                and placement.get("state") in {"shadow", "externalized"}
                else "not-applicable"
            )
            return (
                "v4-tiered-content-addressed",
                {
                    "manifest_ref": MANIFEST_RELATIVE_PATH.as_posix(),
                    "content_digest": "",
                    "digest_state": "not-applicable",
                    "tracked_bytes": 0,
                    "tracked_bytes_max": 0,
                    "shards": 0,
                    "budget_state": "not-applicable",
                    "receipt_ref": "",
                    "corpus_digest": "",
                    "distribution_digest": "",
                    "git_hot_bytes": 0,
                    "corpus_total_bytes": 0,
                    "artifact_cold_bytes": 0,
                    "git_hot_objects": 0,
                    "artifact_cold_objects": 0,
                    "placement_state": placement_state,
                    "hot_profile_ref": "kag/indexes/hot_profile.json",
                    "artifact_locator_ref": "kag/indexes/artifact_locators.json",
                    "os_git_hot_target_bytes": OS_GIT_HOT_TARGET_BYTES,
                    "aggregate_ceiling_receiptable_by_owner": False,
                    "measurement_state": "not-applicable",
                    "measurement_ref": "",
                },
            )
        summary = distribution["summary"]
        budgets = distribution["budgets"]
        corpus_digest = corpus["corpus_identity"]["content_digest"]
        distribution_digest = distribution["distribution_identity"][
            "content_digest"
        ]
        git_hot_bytes = summary["git_hot_bytes"]
        tracked_bytes_max = budgets["owner_git_hot_bytes_max"]
        receipted = git_hot_bytes > tracked_bytes_max
        self_manifest = (
            owner_name == "aoa-kag"
            and owner_root.resolve() == REPO_ROOT.resolve()
        )
        public_identity = "" if self_manifest else corpus_digest.removeprefix("sha256:")
        measured_git_hot_bytes = 0 if self_manifest else git_hot_bytes
        measured_corpus_total_bytes = (
            0 if self_manifest else summary["corpus_total_bytes"]
        )
        measured_artifact_cold_bytes = (
            0 if self_manifest else summary["artifact_cold_bytes"]
        )
        measured_git_hot_objects = (
            0 if self_manifest else summary["git_hot_objects"]
        )
        measured_artifact_cold_objects = (
            0 if self_manifest else summary["artifact_cold_objects"]
        )
        measured_shards = 0 if self_manifest else corpus["summary"]["objects"]
        return (
            "v4-tiered-content-addressed",
            {
                "manifest_ref": MANIFEST_RELATIVE_PATH.as_posix(),
                "content_digest": public_identity,
                "digest_state": "self-manifest" if self_manifest else "published",
                "tracked_bytes": measured_git_hot_bytes,
                "tracked_bytes_max": tracked_bytes_max,
                "shards": measured_shards,
                "budget_state": (
                    "self-excluded"
                    if self_manifest
                    else ("receipted" if receipted else "passed")
                ),
                "receipt_ref": (
                    (
                        "kag/receipts/index_family_budget/"
                        f"{public_identity}.json"
                    )
                    if receipted and not self_manifest
                    else ""
                ),
                "corpus_digest": "" if self_manifest else corpus_digest,
                "distribution_digest": (
                    "" if self_manifest else distribution_digest
                ),
                "git_hot_bytes": measured_git_hot_bytes,
                "corpus_total_bytes": measured_corpus_total_bytes,
                "artifact_cold_bytes": measured_artifact_cold_bytes,
                "git_hot_objects": measured_git_hot_objects,
                "artifact_cold_objects": measured_artifact_cold_objects,
                "placement_state": distribution["placement"]["state"],
                "hot_profile_ref": "kag/indexes/hot_profile.json",
                "artifact_locator_ref": "kag/indexes/artifact_locators.json",
                "os_git_hot_target_bytes": budgets["os_git_hot_target_bytes"],
                "aggregate_ceiling_receiptable_by_owner": budgets[
                    "aggregate_ceiling_receiptable_by_owner"
                ],
                "measurement_state": (
                    "self-excluded" if self_manifest else "measured"
                ),
                "measurement_ref": (
                    "owner-family-release.json#/measurements"
                    if self_manifest
                    else ""
                ),
            },
        )
    portable = _portable_bundle(owner_root)
    if portable is not None:
        manifest = portable[2]
        tracked_bytes = manifest["summary"]["tracked_bytes"]
        tracked_bytes_max = manifest["budgets"]["tracked_bytes_max"]
        receipted = tracked_bytes > tracked_bytes_max
        self_manifest = (
            owner_name == "aoa-kag"
            and owner_root.resolve() == REPO_ROOT.resolve()
        )
        return (
            "v3-portable-shards",
            {
                "manifest_ref": MANIFEST_RELATIVE_PATH.as_posix(),
                "content_digest": (
                    ""
                    if self_manifest
                    else manifest["family_identity"]["content_digest"]
                ),
                "digest_state": (
                    "self-manifest"
                    if self_manifest
                    else "published"
                ),
                "tracked_bytes": 0 if self_manifest else tracked_bytes,
                "tracked_bytes_max": tracked_bytes_max,
                "shards": 0 if self_manifest else manifest["summary"]["shards"],
                "budget_state": (
                    "self-excluded"
                    if self_manifest
                    else ("receipted" if receipted else "passed")
                ),
                "receipt_ref": (
                    receipt_path_for(manifest).as_posix()
                    if receipted and not self_manifest
                    else ""
                ),
                "corpus_digest": "",
                "distribution_digest": "",
                "git_hot_bytes": 0 if self_manifest else tracked_bytes,
                "corpus_total_bytes": 0 if self_manifest else tracked_bytes,
                "artifact_cold_bytes": 0,
                "git_hot_objects": (
                    0 if self_manifest else manifest["summary"]["shards"]
                ),
                "artifact_cold_objects": 0,
                "placement_state": "git-full",
                "hot_profile_ref": "",
                "artifact_locator_ref": "",
                "os_git_hot_target_bytes": OS_GIT_HOT_TARGET_BYTES,
                "aggregate_ceiling_receiptable_by_owner": False,
                "measurement_state": (
                    "self-excluded" if self_manifest else "measured"
                ),
                "measurement_ref": (
                    "owner-family-release.json#/measurements"
                    if self_manifest
                    else ""
                ),
            },
        )
    if status == "passed":
        return (
            "v2-monoliths",
            {
                "manifest_ref": "",
                "content_digest": "",
                "digest_state": "not-applicable",
                "tracked_bytes": 0,
                "tracked_bytes_max": 0,
                "shards": 0,
                "budget_state": "not-applicable",
                "receipt_ref": "",
                "corpus_digest": "",
                "distribution_digest": "",
                "git_hot_bytes": 0,
                "corpus_total_bytes": 0,
                "artifact_cold_bytes": 0,
                "git_hot_objects": 0,
                "artifact_cold_objects": 0,
                "placement_state": "not-applicable",
                "hot_profile_ref": "",
                "artifact_locator_ref": "",
                "os_git_hot_target_bytes": OS_GIT_HOT_TARGET_BYTES,
                "aggregate_ceiling_receiptable_by_owner": False,
                "measurement_state": "not-applicable",
                "measurement_ref": "",
            },
        )
    return (
        "none",
        {
            "manifest_ref": "",
            "content_digest": "",
            "digest_state": "not-applicable",
            "tracked_bytes": 0,
            "tracked_bytes_max": 0,
            "shards": 0,
            "budget_state": "not-applicable",
            "receipt_ref": "",
            "corpus_digest": "",
            "distribution_digest": "",
            "git_hot_bytes": 0,
            "corpus_total_bytes": 0,
            "artifact_cold_bytes": 0,
            "git_hot_objects": 0,
            "artifact_cold_objects": 0,
            "placement_state": "not-applicable",
            "hot_profile_ref": "",
            "artifact_locator_ref": "",
            "os_git_hot_target_bytes": OS_GIT_HOT_TARGET_BYTES,
            "aggregate_ceiling_receiptable_by_owner": False,
            "measurement_state": "not-applicable",
            "measurement_ref": "",
        },
    )


def repository_index_family_refs(
    relative_files: Sequence[str],
    *,
    status: str,
    storage: str,
) -> dict[str, str]:
    present = set(relative_files)
    if status == "passed" and storage in {
        "v3-portable-shards",
        "v4-tiered-content-addressed",
    }:
        return dict(REPOSITORY_INDEX_FAMILY_REFS)
    return {
        index_kind: path
        for index_kind, path in REPOSITORY_INDEX_FAMILY_REFS.items()
        if path in present
    }


@lru_cache(maxsize=None)
def _portable_bundle_from_disk(
    owner_root: Path,
) -> tuple[
    dict[str, Any],
    dict[str, dict[str, Any]],
    dict[str, Any],
] | None:
    manifest = owner_root / MANIFEST_RELATIVE_PATH
    if not manifest.is_file():
        return None
    try:
        artifact_root_value = os.environ.get("KAG_ARTIFACT_ROOT")
        return load_portable_family(
            owner_root,
            artifact_root=(
                Path(artifact_root_value).expanduser().resolve()
                if artifact_root_value
                else None
            ),
            # The self-owner must replay against the executing producer.  A
            # downstream owner may be validly pinned to an older aoa-kag
            # action; its receipt remains checked for candidate/source/budget
            # identity and internal producer consistency by the loader.
            require_current_producer_identity=(
                owner_root.resolve() == REPO_ROOT.resolve()
            ),
            # v1 receipts are retained historical data.  Coverage may observe
            # one for a foreign owner until that owner regenerates its
            # identity-bound receipt, but current budget admission never opts
            # into this compatibility path.
            allow_legacy_external_receipt=(
                owner_root.resolve() != REPO_ROOT.resolve()
            ),
        )
    except (ValueError, FileNotFoundError, json.JSONDecodeError):
        return None


def _portable_bundle(
    owner_root: Path,
) -> tuple[
    dict[str, Any],
    dict[str, dict[str, Any]],
    dict[str, Any],
] | None:
    transient = _TRANSIENT_PORTABLE_BUNDLE
    resolved_root = owner_root.resolve()
    if transient is not None and transient[0] == resolved_root:
        return transient[1]
    return _portable_bundle_from_disk(resolved_root)


# Keep the public cache-invalidation hook used by owner preparation and the
# tiered coverage tests while retaining the transient same-run override above.
_portable_bundle.cache_clear = _portable_bundle_from_disk.cache_clear  # type: ignore[attr-defined]


def _portable_bundle_family_content_digest(
    portable_bundle: PortableBundle,
) -> str | None:
    """Return the compatibility family digest for either manifest era."""

    manifest = portable_bundle[2]
    if manifest.get("schema_version") == DISTRIBUTION_SCHEMA_VERSION:
        distribution_identity = manifest.get("distribution_identity")
        digest = (
            distribution_identity.get("corpus_digest")
            if isinstance(distribution_identity, dict)
            else None
        )
        return digest.removeprefix("sha256:") if isinstance(digest, str) else None
    family_identity = manifest.get("family_identity")
    digest = (
        family_identity.get("content_digest")
        if isinstance(family_identity, dict)
        else None
    )
    return digest if isinstance(digest, str) else None


@contextmanager
def _transient_portable_bundle(
    owner_root: Path,
    portable_bundle: PortableBundle | None,
) -> Iterator[None]:
    global _TRANSIENT_PORTABLE_BUNDLE
    if portable_bundle is None:
        yield
        return
    if _TRANSIENT_PORTABLE_BUNDLE is not None:
        raise RuntimeError("coverage portable-family reuse cannot be nested")
    _TRANSIENT_PORTABLE_BUNDLE = (owner_root.resolve(), portable_bundle)
    try:
        yield
    finally:
        _TRANSIENT_PORTABLE_BUNDLE = None


@lru_cache(maxsize=None)
def _externalized_tiered_bundle(
    owner_root: Path,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
] | None:
    if os.environ.get("KAG_ARTIFACT_ROOT"):
        return None
    manifest_path = owner_root / MANIFEST_RELATIVE_PATH
    try:
        raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        placement = raw_manifest.get("placement")
        if (
            raw_manifest.get("schema_version") != DISTRIBUTION_SCHEMA_VERSION
            or not isinstance(placement, dict)
            or placement.get("state") != "externalized"
        ):
            return None
    except (
        FileNotFoundError,
        IsADirectoryError,
        TypeError,
        json.JSONDecodeError,
        UnicodeDecodeError,
    ):
        return None
    return _tiered_bundle(owner_root)


@lru_cache(maxsize=None)
def _tiered_bundle(
    owner_root: Path,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
] | None:
    """Load a v4 family for coverage from shadow Git or local CAS."""
    manifest_path = owner_root / MANIFEST_RELATIVE_PATH
    try:
        raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        placement = raw_manifest.get("placement")
        if (
            raw_manifest.get("schema_version") != DISTRIBUTION_SCHEMA_VERSION
            or not isinstance(placement, dict)
        ):
            return None
        artifact_root_value = os.environ.get("KAG_ARTIFACT_ROOT")
        artifact_root = (
            Path(artifact_root_value).expanduser().resolve()
            if artifact_root_value
            else None
        )
        distribution, corpus, hot_profile, locators, _ = load_tiered_manifests(
            owner_root,
            artifact_root=artifact_root,
        )
        externalized = placement.get("state") == "externalized"
        rows, delivery = load_tiered_rows(
            owner_root,
            artifact_root=artifact_root,
            allow_shadow_git=not externalized,
            allow_hot_only=externalized,
        )
        expected_state = (
            "hot_only"
            if externalized and distribution["summary"]["artifact_cold_objects"]
            else "complete"
        )
        if delivery.get("state") != expected_state:
            return None
        source_index = reconstruct_source_index(corpus, rows)
        return source_index, distribution, corpus, hot_profile, locators
    except (
        FileNotFoundError,
        IsADirectoryError,
        KeyError,
        TypeError,
        ValueError,
        TieredFamilyUnavailable,
        json.JSONDecodeError,
        UnicodeDecodeError,
    ):
        return None



def repository_event_history_ref(owner_root: Path) -> str | None:
    portable = _portable_bundle(owner_root)
    if portable is not None:
        entries = portable[1]["event"].get("entries")
    else:
        event_index = (
            owner_root
            / "kag"
            / "indexes"
            / REPOSITORY_INDEX_FILENAMES["event"]
        )
        try:
            payload = json.loads(event_index.read_text(encoding="utf-8"))
            entries = payload.get("entries")
        except (
            FileNotFoundError,
            json.JSONDecodeError,
            UnicodeDecodeError,
            IsADirectoryError,
        ):
            return None
    if not isinstance(entries, list):
        return None
    published_refs = {
        str(evidence["ref"])
        for entry in entries
        if isinstance(entry, dict) and entry.get("event_kind") == "git_commit"
        for evidence in entry.get("evidence_refs", [])
        if isinstance(evidence, dict)
        and evidence.get("kind") == "git_commit"
        and isinstance(evidence.get("ref"), str)
    }
    if not published_refs:
        return None
    try:
        ancestry = subprocess.run(
            ("git", "rev-list", "--topo-order", "HEAD"),
            cwd=owner_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return next((ref for ref in ancestry if ref in published_refs), None)


def repository_index_family_matches_owner(
    owner_root: Path,
    source_index: dict[str, Any],
    *,
    source_snapshot: OwnerSourceSnapshot | None = None,
) -> bool:
    history_ref = repository_event_history_ref(owner_root)
    expected = build_repository_indexes(
        source_index,
        source_index_path=SOURCE_SURFACE_INDEX_REL,
        repo_root=owner_root,
        history_ref=history_ref,
        event_history_ref=history_ref,
        source_snapshot=source_snapshot,
    )
    portable = _portable_bundle(owner_root)
    if portable is not None:
        actual = portable[1]
    else:
        tiered = _tiered_bundle(owner_root)
        if tiered is not None:
            _, distribution, corpus, hot_profile, locators = tiered
            try:
                provenance_base_ref = effective_history_ref(owner_root)
                if provenance_base_ref is not None:
                    previous_manifest = tiered_previous_portable_manifest(
                        owner_root,
                        base_ref=provenance_base_ref,
                        corpus_manifest=corpus,
                        fallback=None,
                    )
                    expected_manifest, expected_shards = (
                        build_portable_family(
                            source_index,
                            expected,
                            previous_manifest=previous_manifest,
                        )
                    )
                    expected_tiered = build_tiered_family(
                        expected_manifest,
                        expected_shards,
                        hot_kinds=hot_profile["selection"][
                            "include_record_kinds"
                        ],
                        max_pack_bytes=distribution["transport"][
                            "max_pack_bytes"
                        ],
                        shadow_mode=(
                            distribution.get("placement", {}).get("state")
                            != "externalized"
                        ),
                        mirrors=locators["locators"],
                        migration=tiered_migration_provenance(
                            owner_root,
                            expected_manifest,
                            base_ref=provenance_base_ref,
                            fallback_corpus=corpus,
                        ),
                    )
            except (KeyError, TypeError, ValueError):
                return False
            if (
                provenance_base_ref is not None
                and not check_tiered_git_surface(
                    owner_root,
                    expected_tiered,
                    externalized=(
                        distribution.get("placement", {}).get("state")
                        == "externalized"
                    ),
                )
            ):
                return False
            actual = expected
        else:
            actual = {}
            for index_kind, filename in REPOSITORY_INDEX_FILENAMES.items():
                path = owner_root / "kag" / "indexes" / filename
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                except (
                    FileNotFoundError,
                    json.JSONDecodeError,
                    UnicodeDecodeError,
                    IsADirectoryError,
                ):
                    return False
                actual[index_kind] = payload
    for index_kind in REPOSITORY_INDEX_FILENAMES:
        if actual[index_kind] != expected[index_kind]:
            return False
    try:
        try:
            from scripts.validators.common import ValidationError
            from scripts.validators.repo_local_kag_index import (
                portable_family_validated_in_current_run,
                validate_repo_local_kag_repository_index_family,
            )
        except ImportError:  # pragma: no cover - direct script execution
            from validators.common import ValidationError  # type: ignore
            from validators.repo_local_kag_index import (  # type: ignore
                portable_family_validated_in_current_run,
                validate_repo_local_kag_repository_index_family,
            )

        validation_reused = portable is not None and portable_family_validated_in_current_run(
            owner_root,
            portable[2],
        )
        if source_snapshot is not None:
            if validation_reused:
                source_snapshot.metrics.family_validation_cache_hits += 1
            else:
                source_snapshot.metrics.family_validation_cache_misses += 1
        if not validation_reused:
            validate_repo_local_kag_repository_index_family(
                actual,
                source_payload=source_index,
                label=f"{owner_root.name} coverage family",
            )
    except ValidationError:
        return False
    return True


def _profile_payload(
    owner_root: Path,
    *,
    index_status: str,
    source_snapshot: OwnerSourceSnapshot | None = None,
) -> tuple[str, dict[str, Any]]:
    payload = _source_index_payload(owner_root)
    if payload is not None and (
        index_status == "passed"
        or source_index_matches_owner(
            owner_root,
            payload,
            source_snapshot=source_snapshot,
        )
    ):
        return "source_surface_index", payload
    return "source_tree_scan", build_index(
        owner_root,
        output=SOURCE_SURFACE_INDEX_REL,
        source_snapshot=source_snapshot,
    )


def _records_have_owner_commands(records: object) -> bool:
    if not isinstance(records, list):
        return False
    for record in records:
        if not isinstance(record, dict):
            continue
        toolchain = record.get("toolchain")
        if not isinstance(toolchain, dict):
            continue
        owner_commands = toolchain.get("owner_commands")
        if isinstance(owner_commands, list) and owner_commands:
            return True
    return False


def _record_classes_present(owner_root: Path) -> bool:
    kag_root = owner_root / "kag"
    return all((kag_root / directory).is_dir() for directory in PROVIDER_RECORD_DIRS)


def common_surface_profile(
    owner_root: Path,
    *,
    index_status: str,
    source_snapshot: OwnerSourceSnapshot | None = None,
) -> dict[str, Any]:
    source, payload = _profile_payload(
        owner_root,
        index_status=index_status,
        source_snapshot=source_snapshot,
    )
    records = payload.get("records")
    if not isinstance(records, list):
        records = []
    summary = coverage_summary(records)
    classification = classification_summary(records)
    counts = {
        key: _count_map(classification.get(key))
        for key in COMMON_PROFILE_COUNT_KEYS
    }
    return {
        "source": source,
        "counts": counts,
        "quality": {
            "unknown_count": int(summary.get("unknown_count", 0)),
            "has_kag_home": (owner_root / "kag").is_dir(),
            "has_record_classes": _record_classes_present(owner_root),
            "has_source_index": source == "source_surface_index",
            "has_owner_commands": _records_have_owner_commands(records),
            "has_generated_readmodels": any(
                int(counts.get("surface_state", {}).get(state, 0)) > 0
                for state in ("generated_projection", "generated_readmodel")
            ),
            "has_validation_route": (
                int(summary.get("validator_count", 0)) > 0
                or bool(manifest_validation_route(owner_root, "local-kag"))
            ),
        },
    }


def has_owner_specific_index(owner_name: str, owner_root: Path, relative_files: list[str]) -> bool:
    owner_type = owner_type_for(owner_name, owner_root)
    if owner_type not in OWNER_SPECIFIC_OWNER_TYPES:
        return False
    schema = local_kag_index_record_schema()
    for relative_file in relative_files:
        rel = Path(relative_file)
        if rel.name not in OWNER_SPECIFIC_INDEX_NAMES:
            continue
        try:
            payload = json.loads((owner_root / rel).read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError, IsADirectoryError):
            continue
        if owner_specific_index_is_usable(owner_name, owner_root, payload, schema=schema):
            return True
    return False


def owner_specific_index_is_usable(
    owner_name: str,
    owner_root: Path,
    payload: object,
    *,
    schema: dict[str, Any],
) -> bool:
    if not isinstance(payload, dict):
        return False
    if payload.get("schema_version") != LOCAL_KAG_RECORD_SCHEMA_VERSION:
        return False
    errors = list(Draft202012Validator(schema).iter_errors(payload))
    if errors:
        return False
    if payload.get("repo") != owner_name or payload.get("source_owner") != owner_name:
        return False
    if not owner_specific_checked_ref_is_source_linked(
        payload,
        label=f"{owner_name} owner-specific local KAG index",
    ):
        return False
    owner_return_route = payload.get("owner_return_route")
    if not isinstance(owner_return_route, dict) or owner_return_route.get("repo") != owner_name:
        return False
    source_refs = payload.get("source_refs")
    if not isinstance(source_refs, list):
        return False
    for source_ref in source_refs:
        if not isinstance(source_ref, dict) or source_ref.get("repo") != owner_name:
            return False
        source_path = source_ref.get("path")
        if not isinstance(source_path, str) or not (owner_root / source_path).is_file():
            return False
    if not owner_specific_provider_records_are_usable(owner_name, owner_root):
        return False
    return True


def owner_specific_checked_ref_is_source_linked(payload: object, *, label: str) -> bool:
    try:
        try:
            from scripts.validators.common import ValidationError
            from scripts.validators.local_kag_subtree import _validate_checked_ref_is_source_linked
        except ImportError:  # pragma: no cover - direct script execution
            from validators.common import ValidationError  # type: ignore
            from validators.local_kag_subtree import _validate_checked_ref_is_source_linked  # type: ignore

        _validate_checked_ref_is_source_linked(payload, label=label)
    except ValidationError:
        return False
    return True


def owner_specific_provider_records_are_usable(owner_name: str, owner_root: Path) -> bool:
    try:
        try:
            from scripts.validators.common import ValidationError
            from scripts.validators.local_kag_subtree import (
                _validate_checked_ref_is_source_linked,
                _validate_record_links,
                _validate_source_refs_exist,
            )
        except ImportError:  # pragma: no cover - direct script execution
            from validators.common import ValidationError  # type: ignore
            from validators.local_kag_subtree import (  # type: ignore
                _validate_checked_ref_is_source_linked,
                _validate_record_links,
                _validate_source_refs_exist,
            )

        groups: dict[str, list[dict[str, object]]] = {}
        schemas = local_kag_provider_record_schemas()
        kag_root = owner_root / "kag"
        for group_name in PROVIDER_RECORD_SCHEMA_DEFS:
            directory = kag_root / group_name
            if not directory.is_dir():
                return False
            records: list[dict[str, object]] = []
            for path in sorted(directory.glob("*.json")):
                if group_name == "indexes" and path.name in META_INDEX_NAMES:
                    continue
                payload = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(payload, dict):
                    return False
                if list(Draft202012Validator(schemas[group_name]).iter_errors(payload)):
                    return False
                if payload.get("repo") != owner_name or payload.get("source_owner") != owner_name:
                    return False
                label = f"{owner_name} owner-specific {path.relative_to(owner_root).as_posix()}"
                _validate_source_refs_exist(owner_name, owner_root, payload, label=label)
                _validate_checked_ref_is_source_linked(payload, label=label)
                records.append(payload)
            groups[group_name] = records
        _validate_record_links({"records": groups})
    except (
        FileNotFoundError,
        IsADirectoryError,
        KeyError,
        TypeError,
        json.JSONDecodeError,
        UnicodeDecodeError,
        ValidationError,
    ):
        return False
    return True


def source_index_schema_matches(payload: object, *, label: str) -> bool:
    try:
        try:
            from scripts.validators.common import ValidationError
            from scripts.validators.repo_local_kag_index import (
                repo_local_kag_validate_payload,
            )
        except ImportError:  # pragma: no cover - direct script execution
            from validators.common import ValidationError  # type: ignore
            from validators.repo_local_kag_index import (  # type: ignore
                repo_local_kag_validate_payload,
            )

        repo_local_kag_validate_payload(
            payload,
            schema_path=INDEX_SCHEMA_PATH,
            label=label,
        )
    except ValidationError:
        return False
    return True


def index_status(
    owner_root: Path,
    *,
    owner_name: str | None = None,
    source_snapshot: OwnerSourceSnapshot | None = None,
) -> tuple[str, list[str]]:
    owner_name = owner_name or owner_root.name
    indexes = owner_root / "kag" / "indexes"
    if not indexes.is_dir():
        return "missing", []
    files = sorted(path for path in indexes.glob("*.json") if path.is_file())
    if not files:
        return "missing", []
    relative_files = [path.relative_to(owner_root).as_posix() for path in files]
    portable = _portable_bundle(owner_root)
    if portable is not None:
        payload = portable[0]
        if (
            payload.get("schema_version") == INDEX_SCHEMA_VERSION
            and source_index_schema_matches(
                payload,
                label=f"{owner_name} coverage source index",
            )
            and source_index_matches_owner(
                owner_root,
                payload,
                source_snapshot=source_snapshot,
            )
        ):
            return (
                "passed"
                if repository_index_family_matches_owner(
                    owner_root,
                    payload,
                    source_snapshot=source_snapshot,
                )
                else "migration-needed",
                relative_files,
            )
        return "migration-needed", relative_files
    tiered = _tiered_bundle(owner_root)
    if tiered is not None:
        payload = tiered[0]
        if (
            payload.get("schema_version") == INDEX_SCHEMA_VERSION
            and source_index_schema_matches(
                payload,
                label=f"{owner_name} coverage source index",
            )
            and source_index_matches_owner(
                owner_root,
                payload,
                source_snapshot=source_snapshot,
            )
        ):
            return (
                "passed"
                if repository_index_family_matches_owner(
                    owner_root,
                    payload,
                    source_snapshot=source_snapshot,
                )
                else "migration-needed",
                relative_files,
            )
        return "migration-needed", relative_files
    source_index = indexes / "source_surface_index.json"
    if source_index.is_file():
        try:
            payload = json.loads(source_index.read_text(encoding="utf-8"))
            if (
                isinstance(payload, dict)
                and payload.get("schema_version") == INDEX_SCHEMA_VERSION
                and source_index_schema_matches(
                    payload,
                    label=f"{owner_name} coverage source index",
                )
                and source_index_matches_owner(
                    owner_root,
                    payload,
                    source_snapshot=source_snapshot,
                )
            ):
                return (
                    "passed"
                    if repository_index_family_matches_owner(
                        owner_root,
                        payload,
                        source_snapshot=source_snapshot,
                    )
                    else "migration-needed",
                    relative_files,
                )
        except (json.JSONDecodeError, UnicodeDecodeError):
            return "migration-needed", relative_files
        return "migration-needed", relative_files
    if has_owner_specific_index(owner_name, owner_root, relative_files):
        return "owner-specific", relative_files
    return "migration-needed", relative_files


def _build_owner_coverage(
    name: str,
    owner_root: Path,
    *,
    display_root: Path,
    portable_bundle: PortableBundle | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    owner_started = time.perf_counter()
    usage_before = resource.getrusage(resource.RUSAGE_SELF)
    with _transient_portable_bundle(owner_root, portable_bundle):
        source_snapshot = OwnerSourceSnapshot.capture(owner_root)
        status, files = index_status(
            owner_root,
            owner_name=name,
            source_snapshot=source_snapshot,
        )
        family_storage, portable_family = portable_family_profile(
            owner_root,
            owner_name=name,
            status=status,
        )
        display_kag_home = (
            display_root / "kag" if (owner_root / "kag").is_dir() else Path("")
        )
        owner = {
            "repo": name,
            "owner_type": owner_type_for(name, owner_root),
            "root": display_root.as_posix(),
            "kag_home": (
                display_kag_home.as_posix()
                if display_kag_home.as_posix() != "."
                else ""
            ),
            "index_status": status,
            "index_files": files,
            "family_storage": family_storage,
            "portable_family": portable_family,
            "repository_index_family": repository_index_family_refs(
                files,
                status=status,
                storage=family_storage,
            ),
            "domain_index_catalog_ref": (
                DOMAIN_INDEX_CATALOG_REF if DOMAIN_INDEX_CATALOG_REF in files else ""
            ),
            "coverage": source_counts(
                owner_root,
                source_snapshot=source_snapshot,
            ),
            "common_surface_profile": common_surface_profile(
                owner_root,
                index_status=status,
                source_snapshot=source_snapshot,
            ),
        }
    usage_after = resource.getrusage(resource.RUSAGE_SELF)
    timing = {
        "owner": name,
        "duration_ms": max(
            0,
            round((time.perf_counter() - owner_started) * 1000),
        ),
        "cpu_user_ms": max(
            0,
            round((usage_after.ru_utime - usage_before.ru_utime) * 1000),
        ),
        "cpu_system_ms": max(
            0,
            round((usage_after.ru_stime - usage_before.ru_stime) * 1000),
        ),
        "process_peak_rss_kib": max(0, int(usage_after.ru_maxrss)),
        "source_snapshot": source_snapshot.telemetry(),
    }
    return owner, timing


def _assemble_coverage(
    os_root: Path,
    owners: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    summary = {status: sum(1 for owner in owners if owner["index_status"] == status) for status in OWNER_STATUS}
    if not any(
        isinstance(owner.get("portable_family"), dict)
        and "measurement_state" in owner["portable_family"]
        for owner in owners
    ):
        portable_owners = [
            owner
            for owner in owners
            if owner["family_storage"] == "v3-portable-shards"
        ]
        portable_tracked_bytes = sum(
            owner["portable_family"]["tracked_bytes"]
            for owner in portable_owners
        )
        aggregate_budget_state = (
            "exceeded"
            if portable_tracked_bytes > OS_AGGREGATE_TRACKED_BYTES_MAX
            else (
                "passed"
                if len(portable_owners) == len(owners)
                else "partial"
            )
        )
        return {
            "schema_version": "aoa-repo-local-kag-coverage-v1",
            "source_contract": "schemas/repo-local-kag-index.schema.json",
            "root": os_root.as_posix(),
            "coverage_summary": {
                "owner_count": len(owners),
                "passed": summary["passed"],
                "migration_needed": summary["migration-needed"],
                "missing": summary["missing"],
                "owner_specific": summary["owner-specific"],
                "portable_v3": len(portable_owners),
                "portable_tracked_bytes": portable_tracked_bytes,
                "os_aggregate_tracked_bytes_max": OS_AGGREGATE_TRACKED_BYTES_MAX,
                "aggregate_budget_state": aggregate_budget_state,
            },
            "owners": owners,
        }
    portable_owners = [
        owner
        for owner in owners
        if owner["family_storage"] == "v3-portable-shards"
    ]
    tiered_owners = [
        owner
        for owner in owners
        if owner["family_storage"] == "v4-tiered-content-addressed"
    ]
    family_owners = [*portable_owners, *tiered_owners]
    measured_family_owners = [
        owner
        for owner in family_owners
        if owner["portable_family"]["measurement_state"] == "measured"
    ]
    self_excluded_owners = [
        owner
        for owner in family_owners
        if owner["portable_family"]["measurement_state"] == "self-excluded"
    ]
    portable_tracked_bytes = sum(
        owner["portable_family"]["tracked_bytes"]
        for owner in portable_owners
        if owner["portable_family"]["measurement_state"] == "measured"
    )
    git_hot_bytes = sum(
        owner["portable_family"]["git_hot_bytes"]
        for owner in measured_family_owners
    )
    corpus_total_bytes = sum(
        owner["portable_family"]["corpus_total_bytes"]
        for owner in measured_family_owners
    )
    artifact_cold_bytes = sum(
        owner["portable_family"]["artifact_cold_bytes"]
        for owner in measured_family_owners
        if owner["family_storage"] == "v4-tiered-content-addressed"
    )
    aggregate_budget_state = (
        "exceeded"
        if git_hot_bytes > OS_AGGREGATE_TRACKED_BYTES_MAX
        else (
            "passed"
            if len(measured_family_owners) == len(owners)
            else "partial"
        )
    )
    target_budget_state = (
        "exceeded"
        if git_hot_bytes > OS_GIT_HOT_TARGET_BYTES
        else (
            "passed"
            if (
                len(tiered_owners) == len(owners)
                and len(measured_family_owners) == len(owners)
            )
            else "partial"
        )
    )
    return {
        "schema_version": "aoa-repo-local-kag-coverage-v1",
        "source_contract": "schemas/repo-local-kag-index.schema.json",
        "root": os_root.as_posix(),
        "coverage_summary": {
            "owner_count": len(owners),
            "passed": summary["passed"],
            "migration_needed": summary["migration-needed"],
            "missing": summary["missing"],
            "owner_specific": summary["owner-specific"],
            "measured_owner_count": len(measured_family_owners),
            "self_excluded_owner_count": len(self_excluded_owners),
            "portable_v3": len(portable_owners),
            "tiered_v4": len(tiered_owners),
            "portable_tracked_bytes": portable_tracked_bytes,
            "git_hot_bytes": git_hot_bytes,
            "corpus_total_bytes": corpus_total_bytes,
            "artifact_cold_bytes": artifact_cold_bytes,
            "os_aggregate_tracked_bytes_max": OS_AGGREGATE_TRACKED_BYTES_MAX,
            "os_git_hot_target_bytes": OS_GIT_HOT_TARGET_BYTES,
            "aggregate_budget_state": aggregate_budget_state,
            "target_budget_state": target_budget_state,
        },
        "owners": owners,
    }


def build_coverage(
    os_root: Path,
    owner_roots: Sequence[tuple[str, Path]] | None = None,
    *,
    progress: bool = False,
    owner_timings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    owners: list[dict[str, Any]] = []
    roots = list(owner_roots) if owner_roots is not None else [
        (owner_root.name, owner_root) for owner_root in direct_owner_roots(os_root)
    ]
    if progress:
        coverage_progress(f"owners {len(roots)}")
    for index, (name, owner_root) in enumerate(roots, start=1):
        if progress:
            coverage_progress(f"owner {index}/{len(roots)} {name}")
        owner, timing = _build_owner_coverage(
            name,
            owner_root,
            display_root=(
                canonical_owner_root(os_root, name)
                if owner_roots is not None
                else owner_root
            ),
        )
        owners.append(owner)
        if owner_timings is not None:
            owner_timings.append(timing)
    return _assemble_coverage(os_root, owners)


def _sha256_digest(content: bytes) -> str:
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def _json_digest(payload: object) -> str:
    return _sha256_digest(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )


def _file_digest(path: Path) -> str:
    if path.is_symlink():
        return _sha256_digest(path.readlink().as_posix().encode("utf-8"))
    if not path.is_file():
        raise RuntimeError(f"coverage identity input is unavailable: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _git_output(
    owner: str,
    owner_root: Path,
    command: Sequence[str],
    *,
    text: bool = False,
) -> bytes | str:
    try:
        result = subprocess.run(
            command,
            cwd=owner_root,
            check=True,
            capture_output=True,
            text=text,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise RuntimeError(
            f"coverage identity cannot inspect {owner} with {' '.join(command)}"
        ) from exc
    return result.stdout


def _git_head(owner: str, owner_root: Path) -> str:
    output = _git_output(
        owner,
        owner_root,
        ("git", "rev-parse", "--verify", "HEAD"),
        text=True,
    )
    assert isinstance(output, str)
    value = output.strip()
    if len(value) not in {40, 64} or any(char not in "0123456789abcdef" for char in value):
        raise RuntimeError(f"coverage identity received an invalid HEAD for {owner}")
    return value


def _git_index_tree(owner: str, owner_root: Path) -> str:
    output = _git_output(
        owner,
        owner_root,
        ("git", "write-tree"),
        text=True,
    )
    assert isinstance(output, str)
    value = output.strip()
    if len(value) not in {40, 64} or any(char not in "0123456789abcdef" for char in value):
        raise RuntimeError(f"coverage identity received an invalid index tree for {owner}")
    return value


def _dirty_worktree_paths(owner: str, owner_root: Path) -> tuple[bytes, ...]:
    output = _git_output(
        owner,
        owner_root,
        (
            "git",
            "ls-files",
            "-m",
            "-d",
            "-o",
            "--exclude-standard",
            "-z",
        ),
    )
    assert isinstance(output, bytes)
    return tuple(sorted(set(part for part in output.split(b"\0") if part)))


def _git_worktree_digest(owner: str, owner_root: Path) -> str:
    status = _git_output(
        owner,
        owner_root,
        (
            "git",
            "status",
            "--porcelain=v2",
            "-z",
            "--untracked-files=all",
        ),
    )
    assert isinstance(status, bytes)
    digest = hashlib.sha256()
    digest.update(b"git-status-v2\0")
    digest.update(status)
    digest.update(b"\0")
    for raw_path in _dirty_worktree_paths(owner, owner_root):
        relative = Path(os.fsdecode(raw_path))
        candidate = owner_root / relative
        digest.update(raw_path)
        digest.update(b"\0")
        try:
            mode = candidate.lstat().st_mode
        except FileNotFoundError:
            digest.update(b"missing\0")
            continue
        digest.update(f"{mode:o}".encode("ascii"))
        digest.update(b"\0")
        if candidate.is_symlink():
            digest.update(b"symlink\0")
            digest.update(candidate.readlink().as_posix().encode("utf-8"))
        elif candidate.is_file():
            digest.update(b"file\0")
            with candidate.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
        elif candidate.is_dir():
            digest.update(b"directory\0")
            try:
                nested_head = subprocess.run(
                    ("git", "rev-parse", "--verify", "HEAD"),
                    cwd=candidate,
                    check=True,
                    capture_output=True,
                ).stdout.strip()
                nested_status = subprocess.run(
                    (
                        "git",
                        "status",
                        "--porcelain=v2",
                        "-z",
                        "--untracked-files=all",
                    ),
                    cwd=candidate,
                    check=True,
                    capture_output=True,
                ).stdout
            except (subprocess.CalledProcessError, FileNotFoundError):
                nested_head = b"not-a-git-directory"
                nested_status = b""
            digest.update(nested_head)
            digest.update(b"\0")
            digest.update(nested_status)
        else:
            digest.update(b"other\0")
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def _portable_manifest_identity(owner: str, owner_root: Path) -> dict[str, str]:
    manifest_path = owner_root / MANIFEST_RELATIVE_PATH
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise RuntimeError(
            f"coverage packet requires a portable family manifest for {owner}: "
            f"{manifest_path}"
        )
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, IsADirectoryError) as exc:
        raise RuntimeError(
            f"coverage packet cannot read the portable family manifest for {owner}"
        ) from exc
    repo_identity = payload.get("repo") if isinstance(payload, dict) else None
    if not isinstance(repo_identity, dict) or repo_identity.get("name") != owner:
        raise RuntimeError(
            f"coverage packet portable family manifest owner mismatch for {owner}"
        )
    if payload.get("schema_version") == DISTRIBUTION_SCHEMA_VERSION:
        corpus_manifest_path = owner_root / "kag" / "indexes" / "corpus.manifest.json"
        try:
            corpus_payload = json.loads(
                corpus_manifest_path.read_text(encoding="utf-8")
            )
        except (
            FileNotFoundError,
            IsADirectoryError,
            json.JSONDecodeError,
            UnicodeDecodeError,
        ) as exc:
            raise RuntimeError(
                f"coverage packet cannot read the v4 corpus manifest for {owner}"
            ) from exc
        corpus_repo_identity = (
            corpus_payload.get("repo")
            if isinstance(corpus_payload, dict)
            else None
        )
        if (
            not isinstance(corpus_repo_identity, dict)
            or corpus_repo_identity.get("name") != owner
        ):
            raise RuntimeError(
                f"coverage packet portable corpus manifest owner mismatch for {owner}"
            )
        family_identity = (
            corpus_payload.get("corpus_identity")
            if isinstance(corpus_payload, dict)
            else None
        )
        compatibility = (
            corpus_payload.get("compatibility")
            if isinstance(corpus_payload, dict)
            else None
        )
        family_digest_prefix = "sha256:"
    else:
        family_identity = payload.get("family_identity")
        compatibility = payload.get("compatibility")
        family_digest_prefix = ""
    files = compatibility.get("files") if isinstance(compatibility, dict) else None
    if not isinstance(family_identity, dict) or not isinstance(files, list):
        raise RuntimeError(
            f"coverage packet portable family manifest shape is invalid for {owner}"
        )
    event_entry = next(
        (
            entry
            for entry in files
            if isinstance(entry, dict) and entry.get("kind") == "event"
        ),
        None,
    )
    values = {
        "manifest_digest": _file_digest(manifest_path),
        "family_content_digest": str(
            family_identity.get("content_digest", "")
        ).removeprefix(family_digest_prefix),
        "source_snapshot": str(family_identity.get("source_snapshot", "")),
        "event_content_digest": (
            str(event_entry.get("content_digest", ""))
            if isinstance(event_entry, dict)
            else ""
        ),
    }
    for field in ("family_content_digest", "event_content_digest"):
        value = values[field]
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise RuntimeError(
                f"coverage packet portable family {field} is invalid for {owner}"
            )
    source_snapshot = values["source_snapshot"]
    if not (
        source_snapshot.startswith("sha256:")
        and len(source_snapshot) == len("sha256:") + 64
        and all(char in "0123456789abcdef" for char in source_snapshot[7:])
    ):
        raise RuntimeError(
            f"coverage packet portable family source_snapshot is invalid for {owner}"
        )
    return values


def _coverage_runtime_input_paths() -> tuple[Path, ...]:
    repo_local_modules = tuple(
        sorted(
            path.relative_to(REPO_ROOT)
            for path in (REPO_ROOT / "scripts" / "repo_local").glob("*.py")
            if path.is_file()
        )
    )
    return tuple(sorted(set((*COVERAGE_RUNTIME_INPUT_PATHS, *repo_local_modules))))


def _coverage_runtime_inputs_digest() -> str:
    digest = hashlib.sha256()
    for relative in _coverage_runtime_input_paths():
        path = REPO_ROOT / relative
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(_file_digest(path).encode("ascii"))
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def _provider_snapshot(
    owner: str,
    owner_root: Path,
    *,
    expected_ref: str,
) -> dict[str, str]:
    if not owner_root.is_dir():
        raise RuntimeError(
            f"coverage packet provider root is unavailable for {owner}: {owner_root}"
        )
    head_commit = _git_head(owner, owner_root)
    if expected_ref and head_commit != expected_ref:
        raise RuntimeError(
            f"coverage packet provider pin mismatch for {owner}: "
            f"expected {expected_ref}, got {head_commit}"
        )
    return {
        "owner": owner,
        "root": owner_root.as_posix(),
        "expected_ref": expected_ref,
        "head_commit": head_commit,
        "index_tree": _git_index_tree(owner, owner_root),
        "worktree_digest": _git_worktree_digest(owner, owner_root),
        **_portable_manifest_identity(owner, owner_root),
    }


def coverage_packet_identity(
    os_root: Path = DEFAULT_OS_ROOT,
) -> dict[str, Any]:
    run = current_coverage_run(required=True)
    assert run is not None
    current_order = provider_repo_order()
    if current_order != PROVIDER_REPO_ORDER:
        raise RuntimeError(
            "provider registry changed after coverage modules were imported; "
            "restart the validation run"
        )
    configured = configured_owner_roots()
    if tuple(owner for owner, _ in configured) != current_order:
        raise RuntimeError("configured coverage owner order drifted from the provider registry")
    provider_entries = provider_by_repo()
    return {
        "schema_version": COVERAGE_IDENTITY_SCHEMA_VERSION,
        "run_scope_id": run.run_scope_id,
        "lane": run.lane,
        "display_os_root": os_root.resolve().as_posix(),
        "canonicalization_epoch": COVERAGE_CANONICALIZATION_EPOCH,
        "index_schema_epoch": INDEX_SCHEMA_VERSION,
        "provider_registry_digest": _file_digest(
            REPO_ROOT / "manifests" / "provider_registry.json"
        ),
        "coverage_schema_digest": _file_digest(COVERAGE_SCHEMA_PATH),
        "family_manifest_schema_digest": _file_digest(FAMILY_MANIFEST_SCHEMA_PATH),
        "repository_index_schema_digest": _file_digest(REPOSITORY_INDEX_SCHEMA_PATH),
        "runtime_inputs_digest": _coverage_runtime_inputs_digest(),
        "owner_snapshots": [
            _provider_snapshot(
                owner,
                owner_root,
                expected_ref=str(provider_entries.get(owner, {}).get("pinned_ref", "")),
            )
            for owner, owner_root in configured
        ],
    }


def _validate_coverage_payload_schema(payload: dict[str, Any]) -> None:
    try:
        schema = json.loads(COVERAGE_SCHEMA_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, IsADirectoryError) as exc:
        raise RuntimeError("coverage packet cannot read the coverage schema") from exc
    errors = sorted(
        Draft202012Validator(schema).iter_errors(payload),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        location = "$" + "".join(
            f"[{part}]" if isinstance(part, int) else f".{part}"
            for part in error.absolute_path
        )
        raise RuntimeError(
            f"coverage packet payload does not match the coverage schema at "
            f"{location}: {error.message}"
        )


def _is_hex(value: object, lengths: set[int]) -> bool:
    return (
        isinstance(value, str)
        and len(value) in lengths
        and all(char in "0123456789abcdef" for char in value)
    )


def _is_sha256_digest(value: object) -> bool:
    return (
        isinstance(value, str)
        and value.startswith("sha256:")
        and _is_hex(value[7:], {64})
    )


def _validate_coverage_identity(identity: dict[str, Any]) -> None:
    if set(identity) != COVERAGE_IDENTITY_FIELDS:
        raise RuntimeError("coverage packet identity shape is invalid")
    if identity.get("schema_version") != COVERAGE_IDENTITY_SCHEMA_VERSION:
        raise RuntimeError("coverage packet identity schema is incompatible")
    run_scope_id = identity.get("run_scope_id")
    if not _is_hex(run_scope_id, {32}):
        raise RuntimeError("coverage packet run scope identity is invalid")
    for field in (
        "lane",
        "canonicalization_epoch",
        "index_schema_epoch",
    ):
        if not isinstance(identity.get(field), str) or not identity[field]:
            raise RuntimeError(f"coverage packet identity {field} is invalid")
    display_os_root = identity.get("display_os_root")
    if not isinstance(display_os_root, str) or not Path(display_os_root).is_absolute():
        raise RuntimeError("coverage packet identity display_os_root is invalid")
    for field in (
        "provider_registry_digest",
        "coverage_schema_digest",
        "family_manifest_schema_digest",
        "repository_index_schema_digest",
        "runtime_inputs_digest",
    ):
        if not _is_sha256_digest(identity.get(field)):
            raise RuntimeError(f"coverage packet identity {field} is invalid")

    snapshots = identity.get("owner_snapshots")
    if not isinstance(snapshots, list) or not snapshots:
        raise RuntimeError("coverage packet owner snapshots are incomplete")
    seen_owners: set[str] = set()
    for position, snapshot in enumerate(snapshots):
        if not isinstance(snapshot, dict) or set(snapshot) != COVERAGE_OWNER_SNAPSHOT_FIELDS:
            raise RuntimeError(
                f"coverage packet owner snapshot {position} shape is invalid"
            )
        owner = snapshot.get("owner")
        root = snapshot.get("root")
        expected_ref = snapshot.get("expected_ref")
        if not isinstance(owner, str) or not owner or owner in seen_owners:
            raise RuntimeError(
                f"coverage packet owner snapshot {position} owner is invalid"
            )
        seen_owners.add(owner)
        if not isinstance(root, str) or not Path(root).is_absolute():
            raise RuntimeError(
                f"coverage packet owner snapshot {position} root is invalid"
            )
        if expected_ref != "" and not _is_hex(expected_ref, {40, 64}):
            raise RuntimeError(
                f"coverage packet owner snapshot {position} expected ref is invalid"
            )
        if expected_ref and snapshot.get("head_commit") != expected_ref:
            raise RuntimeError(
                f"coverage packet owner snapshot {position} does not match its expected ref"
            )
        for field in ("head_commit", "index_tree"):
            if not _is_hex(snapshot.get(field), {40, 64}):
                raise RuntimeError(
                    f"coverage packet owner snapshot {position} {field} is invalid"
                )
        for field in ("worktree_digest", "manifest_digest", "source_snapshot"):
            if not _is_sha256_digest(snapshot.get(field)):
                raise RuntimeError(
                    f"coverage packet owner snapshot {position} {field} is invalid"
                )
        for field in ("family_content_digest", "event_content_digest"):
            if not _is_hex(snapshot.get(field), {64}):
                raise RuntimeError(
                    f"coverage packet owner snapshot {position} {field} is invalid"
                )


def _validate_coverage_packet_completeness(
    identity: dict[str, Any],
    payload: dict[str, Any],
) -> None:
    snapshots = identity["owner_snapshots"]
    owners = payload.get("owners")
    summary = payload.get("coverage_summary")
    if not isinstance(owners, list) or not isinstance(summary, dict):
        raise RuntimeError("coverage packet payload completeness is invalid")
    expected_owners = [snapshot["owner"] for snapshot in snapshots]
    actual_owners = [
        owner.get("repo") if isinstance(owner, dict) else None for owner in owners
    ]
    if actual_owners != expected_owners:
        raise RuntimeError(
            "coverage packet owner membership or order does not match the input identity"
        )
    if summary.get("owner_count") != len(expected_owners):
        raise RuntimeError("coverage packet owner count does not match the input identity")
    display_os_root = Path(identity["display_os_root"])
    if payload.get("root") != display_os_root.as_posix():
        raise RuntimeError("coverage packet root does not match the input identity")
    status_total = sum(
        int(summary.get(status, -1))
        for status in ("passed", "migration_needed", "missing", "owner_specific")
    )
    if status_total != len(expected_owners):
        raise RuntimeError("coverage packet owner status counts are incomplete")
    for position, (snapshot, owner_payload) in enumerate(zip(snapshots, owners)):
        expected_display_root = canonical_owner_root(
            display_os_root,
            snapshot["owner"],
        ).as_posix()
        if owner_payload.get("root") != expected_display_root:
            raise RuntimeError(
                f"coverage packet owner display root {position} does not match "
                "the input identity"
            )


def _coverage_identity_receipt(identity: dict[str, Any]) -> dict[str, Any]:
    provider_revisions = [
        {
            field: snapshot[field]
            for field in (
                "owner",
                "expected_ref",
                "head_commit",
            )
        }
        for snapshot in identity["owner_snapshots"]
    ]
    aoa_kag_revision = next(
        (
            revision["head_commit"]
            for revision in provider_revisions
            if revision["owner"] == "aoa-kag"
        ),
        "",
    )
    return {
        "schema_version": identity["schema_version"],
        "display_os_root": identity["display_os_root"],
        "canonicalization_epoch": identity["canonicalization_epoch"],
        "index_schema_epoch": identity["index_schema_epoch"],
        "provider_registry_digest": identity["provider_registry_digest"],
        "coverage_schema_digest": identity["coverage_schema_digest"],
        "family_manifest_schema_digest": identity["family_manifest_schema_digest"],
        "repository_index_schema_digest": identity[
            "repository_index_schema_digest"
        ],
        "runtime_inputs_digest": identity["runtime_inputs_digest"],
        "owner_count": len(identity["owner_snapshots"]),
        "owner_order": [
            snapshot["owner"] for snapshot in identity["owner_snapshots"]
        ],
        "owner_identity_digest": _json_digest(identity["owner_snapshots"]),
        "provider_revision_digest": _json_digest(provider_revisions),
        "pinned_provider_count": sum(
            1 for revision in provider_revisions if revision["expected_ref"]
        ),
        "matching_provider_revision_count": sum(
            1
            for revision in provider_revisions
            if not revision["expected_ref"]
            or revision["expected_ref"] == revision["head_commit"]
        ),
        "aoa_kag_commit": aoa_kag_revision,
    }


def write_coverage_packet(
    path: Path,
    *,
    identity: dict[str, Any],
    payload: dict[str, Any],
) -> tuple[str, str]:
    if path.is_symlink():
        raise RuntimeError(f"coverage packet path must not be a symlink: {path}")
    _validate_coverage_identity(identity)
    _validate_coverage_payload_schema(payload)
    _validate_coverage_packet_completeness(identity, payload)
    identity_digest = _json_digest(identity)
    payload_digest = _json_digest(payload)
    packet = {
        "schema_version": COVERAGE_PACKET_SCHEMA_VERSION,
        "identity": identity,
        "identity_digest": identity_digest,
        "payload_digest": payload_digest,
        "coverage": payload,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    if temporary.is_symlink():
        raise RuntimeError(f"coverage packet temporary path must not be a symlink: {temporary}")
    temporary.write_text(normalized_json(packet), encoding="utf-8")
    temporary.replace(path)
    return identity_digest, payload_digest


def load_coverage_packet(
    path: Path,
) -> tuple[dict[str, Any], dict[str, Any], str, str]:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError(f"coverage packet is not a regular file: {path}")
    try:
        packet = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, IsADirectoryError) as exc:
        raise RuntimeError(f"coverage packet is unreadable: {path}") from exc
    if not isinstance(packet, dict):
        raise RuntimeError(f"coverage packet must be an object: {path}")
    expected_fields = {
        "schema_version",
        "identity",
        "identity_digest",
        "payload_digest",
        "coverage",
    }
    if set(packet) != expected_fields:
        raise RuntimeError(f"coverage packet shape is invalid: {path}")
    if packet.get("schema_version") != COVERAGE_PACKET_SCHEMA_VERSION:
        raise RuntimeError(f"coverage packet schema is incompatible: {path}")
    identity = packet.get("identity")
    payload = packet.get("coverage")
    if not isinstance(identity, dict):
        raise RuntimeError(f"coverage packet identity must be an object: {path}")
    if not isinstance(payload, dict):
        raise RuntimeError(f"coverage packet payload must be an object: {path}")
    _validate_coverage_identity(identity)
    identity_digest = _json_digest(identity)
    payload_digest = _json_digest(payload)
    if packet.get("identity_digest") != identity_digest:
        raise RuntimeError(f"coverage packet identity digest mismatch: {path}")
    if packet.get("payload_digest") != payload_digest:
        raise RuntimeError(f"coverage packet payload digest mismatch: {path}")
    _validate_coverage_payload_schema(payload)
    _validate_coverage_packet_completeness(identity, payload)
    return copy.deepcopy(identity), copy.deepcopy(payload), identity_digest, payload_digest


@contextmanager
def provider_coverage_prebuild_scope(
    os_root: Path = DEFAULT_OS_ROOT,
) -> Iterator[None]:
    global _ACTIVE_PROVIDER_COVERAGE_PREBUILD
    run = current_coverage_run()
    if run is None:
        yield
        return
    if _ACTIVE_PROVIDER_COVERAGE_PREBUILD is not None:
        raise RuntimeError("provider coverage prebuild scope cannot be nested")
    owner_roots = tuple(
        (owner, owner_root.resolve())
        for owner, owner_root in configured_owner_roots()
    )
    identity = coverage_packet_identity(os_root)
    if identity.get("run_scope_id") != run.run_scope_id:
        raise RuntimeError("provider coverage prebuild identity left the active run scope")
    _ACTIVE_PROVIDER_COVERAGE_PREBUILD = _ProviderCoveragePrebuild(
        run_scope_id=run.run_scope_id,
        os_root=os_root.resolve(),
        identity=identity,
        owner_roots=owner_roots,
    )
    try:
        yield
    finally:
        _ACTIVE_PROVIDER_COVERAGE_PREBUILD = None


def prebuild_provider_coverage_owner(
    owner: str,
    owner_root: Path,
    portable_bundle: PortableBundle,
) -> None:
    prebuild = _ACTIVE_PROVIDER_COVERAGE_PREBUILD
    if prebuild is None:
        return
    run = current_coverage_run(required=True)
    assert run is not None
    if run.run_scope_id != prebuild.run_scope_id:
        raise RuntimeError("provider coverage prebuild crossed run scopes")
    expected_roots = dict(prebuild.owner_roots)
    resolved_root = owner_root.resolve()
    if owner not in expected_roots or expected_roots[owner] != resolved_root:
        raise RuntimeError(
            f"provider coverage prebuild received an unexpected owner root: {owner}"
        )
    if owner in prebuild.owners:
        raise RuntimeError(
            f"provider coverage prebuild received duplicate owner: {owner}"
        )
    family_digest = _portable_bundle_family_content_digest(portable_bundle)
    snapshot = next(
        (
            item
            for item in prebuild.identity["owner_snapshots"]
            if item.get("owner") == owner
        ),
        None,
    )
    if (
        not isinstance(family_digest, str)
        or not isinstance(snapshot, dict)
        or snapshot.get("family_content_digest") != family_digest
    ):
        raise RuntimeError(
            f"provider coverage prebuild family identity mismatch for {owner}"
        )
    owner_payload, owner_timing = _build_owner_coverage(
        owner,
        resolved_root,
        display_root=canonical_owner_root(prebuild.os_root, owner),
        portable_bundle=portable_bundle,
    )
    prebuild.owners[owner] = owner_payload
    prebuild.owner_timings[owner] = owner_timing


def prebuild_provider_coverage_owner_result(
    owner: str,
    owner_root: Path,
    *,
    family_content_digest: str,
    owner_payload: dict[str, Any],
    owner_timing: dict[str, Any],
) -> None:
    """Admit one same-run process result into the active canonical fan-in."""

    prebuild = _ACTIVE_PROVIDER_COVERAGE_PREBUILD
    if prebuild is None:
        return
    run = current_coverage_run(required=True)
    assert run is not None
    if run.run_scope_id != prebuild.run_scope_id:
        raise RuntimeError("provider coverage prebuild crossed run scopes")
    expected_roots = dict(prebuild.owner_roots)
    resolved_root = owner_root.resolve()
    if owner not in expected_roots or expected_roots[owner] != resolved_root:
        raise RuntimeError(
            f"provider coverage prebuild received an unexpected owner root: {owner}"
        )
    if owner in prebuild.owners:
        raise RuntimeError(
            f"provider coverage prebuild received duplicate owner: {owner}"
        )
    if prebuild.owners and prebuild.strategy != "provider-home-fused-process":
        raise RuntimeError("provider coverage prebuild mixed execution strategies")
    prebuild.strategy = "provider-home-fused-process"
    snapshot = next(
        (
            item
            for item in prebuild.identity["owner_snapshots"]
            if item.get("owner") == owner
        ),
        None,
    )
    portable_family = owner_payload.get("portable_family")
    self_manifest_row = (
        owner == "aoa-kag"
        and isinstance(portable_family, dict)
        and portable_family.get("digest_state") == "self-manifest"
        and portable_family.get("content_digest") == ""
    )
    if (
        not isinstance(snapshot, dict)
        or snapshot.get("family_content_digest") != family_content_digest
        or not isinstance(portable_family, dict)
        or (
            portable_family.get("content_digest") != family_content_digest
            and not self_manifest_row
        )
    ):
        raise RuntimeError(
            f"provider coverage prebuild family identity mismatch for {owner}"
        )
    expected_display_root = canonical_owner_root(prebuild.os_root, owner).as_posix()
    if (
        owner_payload.get("repo") != owner
        or owner_payload.get("root") != expected_display_root
        or owner_timing.get("owner") != owner
    ):
        raise RuntimeError(
            f"provider coverage prebuild process result identity mismatch for {owner}"
        )
    prebuild.owners[owner] = copy.deepcopy(owner_payload)
    prebuild.owner_timings[owner] = copy.deepcopy(owner_timing)


def _active_provider_coverage_prebuild(
    os_root: Path,
) -> _ProviderCoveragePrebuild | None:
    prebuild = _ACTIVE_PROVIDER_COVERAGE_PREBUILD
    if prebuild is None:
        return None
    run = current_coverage_run(required=True)
    assert run is not None
    if run.run_scope_id != prebuild.run_scope_id:
        raise RuntimeError("provider coverage prebuild crossed run scopes")
    if os_root.resolve() != prebuild.os_root:
        raise RuntimeError("provider coverage prebuild display root changed")
    return prebuild


def _assemble_prebuilt_provider_coverage(
    prebuild: _ProviderCoveragePrebuild,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    expected_owners = [owner for owner, _owner_root in prebuild.owner_roots]
    actual_owners = list(prebuild.owners)
    if len(actual_owners) != len(expected_owners) or set(actual_owners) != set(
        expected_owners
    ):
        missing = [owner for owner in expected_owners if owner not in prebuild.owners]
        unexpected = [owner for owner in actual_owners if owner not in expected_owners]
        raise RuntimeError(
            "provider coverage prebuild owner membership is incomplete"
            f"; missing={missing}; unexpected={unexpected}"
        )
    owners = [prebuild.owners[owner] for owner in expected_owners]
    owner_timings = [prebuild.owner_timings[owner] for owner in expected_owners]
    return _assemble_coverage(prebuild.os_root, owners), owner_timings


def build_provider_coverage(
    os_root: Path = DEFAULT_OS_ROOT,
    *,
    progress: bool = False,
) -> dict[str, Any]:
    run = current_coverage_run()
    if run is None:
        return build_coverage(
            os_root,
            owner_roots=configured_owner_roots(),
            progress=progress,
        )

    packet_path = run.packet_path
    try:
        prebuild = _active_provider_coverage_prebuild(os_root)
        use_prebuild = prebuild is not None and not packet_path.exists()
        identity = (
            copy.deepcopy(prebuild.identity)
            if use_prebuild and prebuild is not None
            else coverage_packet_identity(os_root)
        )
    except Exception as exc:
        record_coverage_event(
            {
                "event": "reject",
                "reason": "input-identity-unprovable",
                "detail": str(exc),
            }
        )
        raise
    identity_digest = _json_digest(identity)
    if packet_path.is_symlink():
        record_coverage_event(
            {
                "event": "reject",
                "reason": "packet-symlink",
                "identity_digest": identity_digest,
            }
        )
        raise RuntimeError(f"coverage packet path must not be a symlink: {packet_path}")

    if packet_path.exists():
        try:
            (
                packet_identity,
                packet_payload,
                packet_identity_digest,
                packet_payload_digest,
            ) = load_coverage_packet(packet_path)
        except RuntimeError as exc:
            record_coverage_event(
                {
                    "event": "reject",
                    "reason": "packet-integrity",
                    "identity_digest": identity_digest,
                    "detail": str(exc),
                }
            )
            raise
        if packet_identity == identity:
            record_coverage_event(
                {
                    "event": "hit",
                    "identity_digest": packet_identity_digest,
                    "payload_digest": packet_payload_digest,
                    "owner_count": len(packet_payload.get("owners", [])),
                }
            )
            if progress:
                coverage_progress(f"reused verified packet {packet_path}")
            return packet_payload
        record_coverage_event(
            {
                "event": "miss",
                "reason": "input-identity-changed",
                "identity_digest": identity_digest,
                "previous_identity_digest": packet_identity_digest,
            }
        )
    else:
        record_coverage_event(
            {
                "event": "miss",
                "reason": "packet-absent",
                "identity_digest": identity_digest,
            }
        )

    owner_timings: list[dict[str, Any]] = (
        list(prebuild.owner_timings.values())
        if use_prebuild and prebuild is not None
        else []
    )
    build_strategy = (
        prebuild.strategy
        if use_prebuild and prebuild is not None
        else "cold"
    )
    started = time.perf_counter()
    try:
        if use_prebuild and prebuild is not None:
            payload, owner_timings = _assemble_prebuilt_provider_coverage(prebuild)
        else:
            payload = build_coverage(
                os_root,
                owner_roots=configured_owner_roots(),
                progress=progress,
                owner_timings=owner_timings,
            )
    except Exception as exc:
        duration_ms = max(0, round((time.perf_counter() - started) * 1000))
        if use_prebuild:
            duration_ms += sum(
                int(timing.get("duration_ms", 0))
                for timing in owner_timings
                if isinstance(timing.get("duration_ms", 0), int)
            )
        record_coverage_event(
            {
                "event": "build-failed",
                "identity_digest": identity_digest,
                "duration_ms": duration_ms,
                "detail": str(exc),
                "owner_timings": owner_timings,
                "strategy": build_strategy,
            }
        )
        raise

    try:
        final_identity = coverage_packet_identity(os_root)
    except Exception as exc:
        duration_ms = max(0, round((time.perf_counter() - started) * 1000))
        if use_prebuild:
            duration_ms += sum(
                int(timing.get("duration_ms", 0))
                for timing in owner_timings
                if isinstance(timing.get("duration_ms", 0), int)
            )
        record_coverage_event(
            {
                "event": "reject",
                "reason": "final-input-identity-unprovable",
                "identity_digest": identity_digest,
                "duration_ms": duration_ms,
                "detail": str(exc),
                "owner_timings": owner_timings,
                "strategy": build_strategy,
            }
        )
        raise
    if final_identity != identity:
        final_identity_digest = _json_digest(final_identity)
        duration_ms = max(0, round((time.perf_counter() - started) * 1000))
        if use_prebuild:
            duration_ms += sum(
                int(timing.get("duration_ms", 0))
                for timing in owner_timings
                if isinstance(timing.get("duration_ms", 0), int)
            )
        record_coverage_event(
            {
                "event": "reject",
                "reason": "input-changed-during-build",
                "identity_digest": identity_digest,
                "final_identity_digest": final_identity_digest,
                "duration_ms": duration_ms,
                "owner_timings": owner_timings,
                "strategy": build_strategy,
            }
        )
        raise RuntimeError(
            "coverage inputs changed during the owner audit; restart from one "
            "immutable input epoch"
        )

    identity_digest, payload_digest = write_coverage_packet(
        packet_path,
        identity=identity,
        payload=payload,
    )
    duration_ms = max(0, round((time.perf_counter() - started) * 1000))
    if use_prebuild:
        duration_ms += sum(
            int(timing.get("duration_ms", 0))
            for timing in owner_timings
            if isinstance(timing.get("duration_ms", 0), int)
        )
    record_coverage_event(
        {
            "event": "build",
            "identity_digest": identity_digest,
            "payload_digest": payload_digest,
            "duration_ms": duration_ms,
            "owner_count": len(payload.get("owners", [])),
            "owner_timings": owner_timings,
            "input_identity": _coverage_identity_receipt(identity),
            "strategy": build_strategy,
            "prebuilt_owner_count": len(owner_timings) if use_prebuild else 0,
        }
    )
    if progress:
        coverage_progress(f"wrote verified packet {packet_path}")
    return payload


def write_outputs(output: Path, min_output: Path, payload: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(normalized_json(payload), encoding="utf-8")
    min_output.parent.mkdir(parents=True, exist_ok=True)
    min_output.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def check_outputs(output: Path, min_output: Path, payload: dict[str, Any]) -> bool:
    expected = normalized_json(payload)
    expected_min = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ok = True
    if not output.exists() or output.read_text(encoding="utf-8") != expected:
        print(f"[repo-local-kag-coverage] drift in {output}", file=sys.stderr)
        ok = False
    if not min_output.exists() or min_output.read_text(encoding="utf-8") != expected_min:
        print(f"[repo-local-kag-coverage] drift in {min_output}", file=sys.stderr)
        ok = False
    return ok


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate repo-local KAG coverage for OS Abyss.")
    parser.add_argument("--os-root")
    parser.add_argument("--output", default=DEFAULT_OUTPUT.as_posix())
    parser.add_argument("--min-output", default=DEFAULT_MIN_OUTPUT.as_posix())
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    payload = (
        build_coverage(Path(args.os_root).resolve(), progress=True)
        if args.os_root
        else build_provider_coverage(progress=True)
    )
    output = Path(args.output)
    min_output = Path(args.min_output)
    if args.check:
        return 0 if check_outputs(output, min_output, payload) else 1
    write_outputs(output, min_output, payload)
    print(f"[repo-local-kag-coverage] wrote {output} and {min_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
