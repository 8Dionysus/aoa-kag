from __future__ import annotations

import copy
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .portable_family import (
    DEFAULT_DELTA_BYTES_MAX,
    GLOBAL_TRACKED_BYTES_MAX,
    MANIFEST_RELATIVE_PATH,
    OS_AGGREGATE_TRACKED_BYTES_MAX,
    SCHEMA_VERSION as PORTABLE_V3_SCHEMA_VERSION,
    SHARD_ROOT_RELATIVE_PATH,
    PortableFamilyError,
    canonical_json_bytes,
    manifest_digest as portable_v3_manifest_digest,
    reconstruct_compatibility_family,
    render_manifest,
    sha256_bytes,
)


CORPUS_SCHEMA_VERSION = "aoa-repo-local-kag-corpus-manifest-v1"
DISTRIBUTION_SCHEMA_VERSION = "aoa-repo-local-kag-distribution-manifest-v1"
HOT_PROFILE_SCHEMA_VERSION = "aoa-repo-local-kag-hot-profile-v1"
LOCATOR_SCHEMA_VERSION = "aoa-kag-artifact-locator-v1"
PACK_INDEX_SCHEMA_VERSION = "aoa-kag-pack-index-v1"
OWNER_RELEASE_SCHEMA_VERSION = "aoa-kag-owner-family-release-v1"
OWNER_RELEASE_ARTIFACT_CLASS = "kag_owner_family_release"
OWNER_RELEASE_ABI_EPOCH = OWNER_RELEASE_SCHEMA_VERSION
BUNDLE_SCHEMA_VERSION = "aoa-kag-portable-family-bundle-v1"

CORPUS_SCHEMA_REF = "aoa-kag:schemas/repo-local-kag-corpus-manifest.schema.json"
DISTRIBUTION_SCHEMA_REF = (
    "aoa-kag:schemas/repo-local-kag-distribution-manifest.schema.json"
)
HOT_PROFILE_SCHEMA_REF = "aoa-kag:schemas/repo-local-kag-hot-profile.schema.json"
LOCATOR_SCHEMA_REF = "aoa-kag:schemas/kag-artifact-locator.schema.json"
PACK_INDEX_SCHEMA_REF = "aoa-kag:schemas/kag-pack-index.schema.json"
OWNER_RELEASE_SCHEMA_REF = "aoa-kag:schemas/kag-owner-family-release.schema.json"

CORPUS_MANIFEST_RELATIVE_PATH = Path("kag/indexes/corpus.manifest.json")
HOT_PROFILE_RELATIVE_PATH = Path("kag/indexes/hot_profile.json")
LOCATOR_MANIFEST_RELATIVE_PATH = Path("kag/indexes/artifact_locators.json")
PACK_INDEX_ARTIFACT_PATH = Path("pack-index.json")
OWNER_RELEASE_ARTIFACT_PATH = Path("owner-family-release.json")
BUNDLE_MANIFEST_PATH = Path("bundle.manifest.json")

ZERO_DIGEST_URI = f"sha256:{'0' * 64}"
OWNER_RELEASE_LIFECYCLE_STATES = (
    "candidate",
    "built-local",
    "manually-verified",
    "release-ready",
    "published",
    "superseded",
    "revoked",
)
SOURCE_BOUND_LIFECYCLE_STATES = frozenset(
    {
        "manually-verified",
        "release-ready",
        "published",
        "superseded",
        "revoked",
    }
)
EXACT_GIT_COMMIT_REF = re.compile(r"^commit:[0-9a-f]{40}(?:[0-9a-f]{24})?$")
DEFAULT_HOT_KINDS = ("source", "source_chunk")
DEFAULT_PACK_BYTES_MAX = 8 * 1024 * 1024
OS_GIT_HOT_TARGET_BYTES = 234_881_024
DECISION_REF = (
    "aoa-kag:docs/decisions/"
    "AOA-KAG-D-0019-tiered-content-addressed-kag-distribution.md"
)

COMPLETE_STATES = {"complete", "git_hot_complete"}
DEGRADATION_STATES = {
    "complete",
    "git_hot_complete",
    "hot_only",
    "artifact_required",
    "artifact_unavailable",
    "rebuild_available",
    "rebuild_required",
    "stale",
    "digest_mismatch",
    "revoked",
    "access_denied",
}


class TieredFamilyError(PortableFamilyError):
    pass


class TieredFamilyUnavailable(TieredFamilyError):
    def __init__(
        self,
        state: str,
        missing: Sequence[str],
        *,
        corpus_digest: str = "",
        distribution_digest: str = "",
    ) -> None:
        if state not in DEGRADATION_STATES:
            raise ValueError(f"unknown tiered family state: {state}")
        self.state = state
        self.missing = tuple(missing)
        self.corpus_digest = corpus_digest
        self.distribution_digest = distribution_digest
        super().__init__(
            f"tiered family is {state}; missing objects: "
            + ", ".join(self.missing[:8])
        )


@dataclass(frozen=True)
class TieredFamilyBuild:
    corpus_manifest: dict[str, Any]
    hot_profile: dict[str, Any]
    locator_manifest: dict[str, Any]
    pack_index: dict[str, Any]
    distribution_manifest: dict[str, Any]
    owner_release: dict[str, Any]
    object_bytes: Mapping[str, bytes]
    hot_shards: Mapping[Path, bytes]
    cold_shards: Mapping[Path, bytes]
    pack_bytes: Mapping[str, bytes]


def _sha256_uri(content: bytes) -> str:
    return f"sha256:{sha256_bytes(content)}"


def _digest_hex(digest: str) -> str:
    if not isinstance(digest, str) or not digest.startswith("sha256:"):
        raise TieredFamilyError("content digest must use sha256:<hex>")
    value = digest.removeprefix("sha256:")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise TieredFamilyError("content digest must contain 64 lowercase hex digits")
    return value


def canonical_source_ref(source_ref: str) -> str:
    """Return one transport-neutral exact source-ref spelling.

    Committed KAG manifests intentionally use ``git-index-source-tree`` to
    avoid embedding the hash of the commit that contains the manifest itself.
    Immutable artifact releases are outside that recursive boundary and bind
    the exact owner commit as ``commit:<hex>`` during lifecycle preparation.
    """
    value = str(source_ref or "").strip().lower()
    if re.fullmatch(r"[0-9a-f]{40}(?:[0-9a-f]{24})?", value):
        return f"commit:{value}"
    return value


def _is_exact_git_commit_ref(source_ref: object) -> bool:
    return isinstance(source_ref, str) and EXACT_GIT_COMMIT_REF.fullmatch(
        source_ref
    ) is not None


def _is_digest_uri(value: object) -> bool:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        return False
    digest = value.removeprefix("sha256:")
    return len(digest) == 64 and all(
        character in "0123456789abcdef" for character in digest
    )


def _identity_digest(
    payload: Mapping[str, Any],
    identity_field: str,
    *,
    excluded_fields: Sequence[str] = (),
) -> str:
    candidate = copy.deepcopy(dict(payload))
    identity = candidate.get(identity_field)
    if not isinstance(identity, dict):
        raise TieredFamilyError(f"manifest needs {identity_field}")
    identity["content_digest"] = ZERO_DIGEST_URI
    for field in excluded_fields:
        candidate.pop(field, None)
    return _sha256_uri(canonical_json_bytes(candidate))


def _corpus_digest(payload: Mapping[str, Any]) -> str:
    identity = payload.get("corpus_identity")
    if not isinstance(identity, Mapping):
        raise TieredFamilyError("corpus manifest needs corpus_identity")
    material = {
        "owner": payload.get("repo"),
        "source_snapshot": identity.get("source_snapshot"),
        "epochs": payload.get("epochs"),
        "partitioning": payload.get("partitioning"),
        "normalization": payload.get("normalization"),
        "source_index_header": payload.get("source_index_header"),
        "compatibility": payload.get("compatibility"),
        "objects": payload.get("objects"),
    }
    return _sha256_uri(canonical_json_bytes(material))


def _repo_name(manifest: Mapping[str, Any]) -> str:
    repo = manifest.get("repo")
    name = repo.get("name") if isinstance(repo, Mapping) else None
    if not isinstance(name, str) or not name:
        raise TieredFamilyError("family manifest needs repo.name")
    return name


def _object_key(digest: str) -> str:
    value = _digest_hex(digest)
    return f"objects/sha256/{value[:2]}/{value}"


def _pack_key(digest: str) -> str:
    value = _digest_hex(digest)
    return f"packs/sha256/{value[:2]}/{value}.pack"


def _release_relative_root(distribution_manifest: Mapping[str, Any]) -> Path:
    owner = _repo_name(distribution_manifest)
    identity = distribution_manifest.get("distribution_identity")
    digest = identity.get("content_digest") if isinstance(identity, Mapping) else None
    return Path("releases") / owner / _digest_hex(str(digest))


def _shard_path(kind: str, hash_range: str) -> Path:
    if not kind or not hash_range or "/" in kind or "/" in hash_range:
        raise TieredFamilyError("invalid shard kind or hash range")
    return SHARD_ROOT_RELATIVE_PATH / kind / f"{hash_range}.jsonl"


def _is_hot_kind(kind: str, hot_kinds: Sequence[str]) -> bool:
    return kind in hot_kinds


def _validate_portable_v3_inputs(
    portable_manifest: Mapping[str, Any],
    shards: Mapping[Path, bytes],
) -> list[dict[str, Any]]:
    if portable_manifest.get("schema_version") != PORTABLE_V3_SCHEMA_VERSION:
        raise TieredFamilyError(
            f"tiered migration requires {PORTABLE_V3_SCHEMA_VERSION} input"
        )
    identity = portable_manifest.get("family_identity")
    if not isinstance(identity, Mapping) or identity.get(
        "content_digest"
    ) != portable_v3_manifest_digest(portable_manifest):
        raise TieredFamilyError("portable v3 manifest digest does not match")
    descriptors = portable_manifest.get("shards")
    if not isinstance(descriptors, list) or not descriptors:
        raise TieredFamilyError("portable v3 manifest needs shard descriptors")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for descriptor in descriptors:
        if not isinstance(descriptor, Mapping):
            raise TieredFamilyError("portable shard descriptor must be an object")
        path_value = descriptor.get("path")
        if not isinstance(path_value, str):
            raise TieredFamilyError("portable shard descriptor needs path")
        path = Path(path_value)
        content = shards.get(path)
        if content is None:
            raise TieredFamilyError(f"portable shard bytes are missing: {path_value}")
        digest = descriptor.get("digest")
        if digest != _sha256_uri(content):
            raise TieredFamilyError(f"portable shard digest does not match: {path_value}")
        if descriptor.get("bytes") != len(content):
            raise TieredFamilyError(f"portable shard byte count does not match: {path_value}")
        if digest in seen:
            raise TieredFamilyError(f"duplicate portable object digest: {digest}")
        seen.add(str(digest))
        normalized.append(
            {
                "kind": descriptor.get("kind"),
                "range": descriptor.get("range"),
                "content_digest": digest,
                "bytes": descriptor.get("bytes"),
                "records": descriptor.get("records"),
            }
        )
    if any(
        not isinstance(item["kind"], str)
        or not isinstance(item["range"], str)
        or not isinstance(item["bytes"], int)
        or not isinstance(item["records"], int)
        for item in normalized
    ):
        raise TieredFamilyError("portable shard descriptor fields are malformed")
    return sorted(
        normalized,
        key=lambda item: (item["kind"], len(item["range"]), item["range"]),
    )


def build_corpus_manifest(
    portable_manifest: Mapping[str, Any],
    shards: Mapping[Path, bytes],
    *,
    migration: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    objects = _validate_portable_v3_inputs(portable_manifest, shards)
    source_identity = portable_manifest.get("family_identity")
    if not isinstance(source_identity, Mapping):
        raise TieredFamilyError("portable family identity is malformed")
    manifest: dict[str, Any] = {
        "schema_version": CORPUS_SCHEMA_VERSION,
        "repo": copy.deepcopy(portable_manifest["repo"]),
        "corpus_identity": {
            "local_id": "family:repo-local:logical-record-corpus",
            "artifact_kind": "repo_local_kag_corpus",
            "content_digest": ZERO_DIGEST_URI,
            "schema_ref": CORPUS_SCHEMA_REF,
            "source_snapshot": source_identity.get("source_snapshot"),
        },
        "epochs": {
            "logical_schema": PORTABLE_V3_SCHEMA_VERSION,
            "canonicalization": "portable-record-normalization-v3",
            "record_key": "portable-record-key-v1",
            "shard_partition": "sha256-record-key-adaptive-prefix-v1",
        },
        "builder": {
            "route": "aoa-kag:scripts/repo_local/tiered_family.py",
            "contract_version": "tiered-family-v1",
        },
        "partitioning": copy.deepcopy(portable_manifest.get("partitioning")),
        "normalization": copy.deepcopy(portable_manifest.get("normalization")),
        "source_index_header": copy.deepcopy(
            portable_manifest.get("source_index_header")
        ),
        "compatibility": copy.deepcopy(portable_manifest.get("compatibility")),
        "summary": {
            "canonical_records": sum(item["records"] for item in objects),
            "objects": len(objects),
            "corpus_total_bytes": sum(item["bytes"] for item in objects),
        },
        "objects": objects,
        "migration": (
            copy.deepcopy(dict(migration))
            if migration is not None
            else {
                "from_schema": PORTABLE_V3_SCHEMA_VERSION,
                "from_family_digest": source_identity.get("content_digest"),
                "decision_ref": DECISION_REF,
            }
        ),
    }
    manifest["corpus_identity"]["content_digest"] = _corpus_digest(manifest)
    validate_corpus_manifest(manifest)
    return manifest


def validate_corpus_manifest(manifest: Mapping[str, Any]) -> None:
    if manifest.get("schema_version") != CORPUS_SCHEMA_VERSION:
        raise TieredFamilyError(f"corpus schema must be {CORPUS_SCHEMA_VERSION}")
    identity = manifest.get("corpus_identity")
    if not isinstance(identity, Mapping):
        raise TieredFamilyError("corpus manifest needs corpus_identity")
    if identity.get("content_digest") != _corpus_digest(manifest):
        raise TieredFamilyError("corpus identity digest does not match")
    objects = manifest.get("objects")
    summary = manifest.get("summary")
    if not isinstance(objects, list) or not isinstance(summary, Mapping):
        raise TieredFamilyError("corpus manifest needs objects and summary")
    digests = [item.get("content_digest") for item in objects if isinstance(item, Mapping)]
    if len(digests) != len(objects) or len(digests) != len(set(digests)):
        raise TieredFamilyError("corpus object digests must be unique")
    if summary.get("objects") != len(objects):
        raise TieredFamilyError("corpus object count does not match")
    if summary.get("canonical_records") != sum(
        int(item.get("records", -1)) for item in objects
    ):
        raise TieredFamilyError("corpus record count does not match")
    if summary.get("corpus_total_bytes") != sum(
        int(item.get("bytes", -1)) for item in objects
    ):
        raise TieredFamilyError("corpus byte count does not match")


def build_hot_profile(
    corpus_manifest: Mapping[str, Any],
    *,
    hot_kinds: Sequence[str] = DEFAULT_HOT_KINDS,
) -> dict[str, Any]:
    validate_corpus_manifest(corpus_manifest)
    unique_kinds = sorted(set(hot_kinds))
    if "source" not in unique_kinds:
        raise TieredFamilyError("Git-hot profile must retain source shards")
    profile: dict[str, Any] = {
        "schema_version": HOT_PROFILE_SCHEMA_VERSION,
        "repo": copy.deepcopy(corpus_manifest["repo"]),
        "profile_identity": {
            "local_id": "profile:repo-local:kag-git-hot",
            "artifact_kind": "repo_local_kag_hot_profile",
            "content_digest": ZERO_DIGEST_URI,
            "schema_ref": HOT_PROFILE_SCHEMA_REF,
            "corpus_digest": corpus_manifest["corpus_identity"]["content_digest"],
        },
        "selection": {
            "mode": "record-kind-allowlist",
            "include_record_kinds": unique_kinds,
            "purpose": ["bootstrap", "discovery", "audit", "owner_return"],
            "runtime_frequency_inputs": "forbidden",
            "automatic_merge_or_eviction": "forbidden",
        },
        "policy": {
            "owner_qualified": True,
            "deterministic": True,
            "committed_lru_lfu": "forbidden",
            "decision_ref": DECISION_REF,
        },
    }
    profile["profile_identity"]["content_digest"] = _identity_digest(
        profile, "profile_identity"
    )
    validate_hot_profile(profile)
    return profile


def validate_hot_profile(profile: Mapping[str, Any]) -> None:
    if profile.get("schema_version") != HOT_PROFILE_SCHEMA_VERSION:
        raise TieredFamilyError(f"hot profile schema must be {HOT_PROFILE_SCHEMA_VERSION}")
    identity = profile.get("profile_identity")
    selection = profile.get("selection")
    if not isinstance(identity, Mapping) or not isinstance(selection, Mapping):
        raise TieredFamilyError("hot profile identity or selection is missing")
    if identity.get("content_digest") != _identity_digest(profile, "profile_identity"):
        raise TieredFamilyError("hot profile digest does not match")
    kinds = selection.get("include_record_kinds")
    if not isinstance(kinds, list) or "source" not in kinds:
        raise TieredFamilyError("hot profile must include source")
    if selection.get("runtime_frequency_inputs") != "forbidden":
        raise TieredFamilyError("runtime frequency cannot select committed hot shards")


def build_locator_manifest(
    corpus_manifest: Mapping[str, Any],
    *,
    mirrors: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    validate_corpus_manifest(corpus_manifest)
    locator_entries = list(mirrors or ()) or [
        {
            "locator_id": "owner-public-cas",
            "transport": "cas",
            "priority": 100,
            "object_key_template": "objects/sha256/{prefix}/{digest}",
            "pack_key_template": "packs/sha256/{prefix}/{digest}.pack",
            "trust_domain": "public-kag",
            "mutable_location": True,
        }
    ]
    manifest: dict[str, Any] = {
        "schema_version": LOCATOR_SCHEMA_VERSION,
        "repo": copy.deepcopy(corpus_manifest["repo"]),
        "locator_identity": {
            "local_id": "locator:repo-local:kag-artifacts",
            "artifact_kind": "kag_artifact_locator_set",
            "content_digest": ZERO_DIGEST_URI,
            "schema_ref": LOCATOR_SCHEMA_REF,
            "corpus_digest": corpus_manifest["corpus_identity"]["content_digest"],
        },
        "locators": [copy.deepcopy(dict(item)) for item in locator_entries],
        "authority": {
            "corpus_identity_authority": False,
            "replaceable": True,
            "decision_ref": DECISION_REF,
        },
    }
    manifest["locator_identity"]["content_digest"] = _identity_digest(
        manifest, "locator_identity"
    )
    validate_locator_manifest(manifest)
    return manifest


def validate_locator_manifest(manifest: Mapping[str, Any]) -> None:
    if manifest.get("schema_version") != LOCATOR_SCHEMA_VERSION:
        raise TieredFamilyError(f"locator schema must be {LOCATOR_SCHEMA_VERSION}")
    identity = manifest.get("locator_identity")
    locators = manifest.get("locators")
    if not isinstance(identity, Mapping) or not isinstance(locators, list):
        raise TieredFamilyError("locator manifest needs identity and locators")
    if identity.get("content_digest") != _identity_digest(
        manifest, "locator_identity"
    ):
        raise TieredFamilyError("locator manifest digest does not match")
    for locator in locators:
        if not isinstance(locator, Mapping):
            raise TieredFamilyError("artifact locator must be an object")
        for field in ("object_key_template", "pack_key_template"):
            value = locator.get(field)
            if not isinstance(value, str) or "{digest}" not in value:
                raise TieredFamilyError(f"artifact locator needs {field}")
            if value.startswith("/") or ".." in Path(value).parts:
                raise TieredFamilyError("artifact locator templates must be portable")


def _object_bytes_by_digest(
    corpus_manifest: Mapping[str, Any],
    shards: Mapping[Path, bytes],
) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for descriptor in corpus_manifest["objects"]:
        path = _shard_path(descriptor["kind"], descriptor["range"])
        content = shards.get(path)
        if content is None:
            raise TieredFamilyError(f"missing shard content for {path}")
        digest = descriptor["content_digest"]
        if _sha256_uri(content) != digest:
            raise TieredFamilyError(f"shard content digest changed for {path}")
        result[digest] = content
    return result


def build_pack_index(
    corpus_manifest: Mapping[str, Any],
    object_bytes: Mapping[str, bytes],
    *,
    hot_kinds: Sequence[str] = DEFAULT_HOT_KINDS,
    max_pack_bytes: int = DEFAULT_PACK_BYTES_MAX,
) -> tuple[dict[str, Any], dict[str, bytes]]:
    validate_corpus_manifest(corpus_manifest)
    if max_pack_bytes <= 0:
        raise TieredFamilyError("max pack bytes must be positive")
    cold = [
        descriptor
        for descriptor in corpus_manifest["objects"]
        if not _is_hot_kind(descriptor["kind"], hot_kinds)
    ]
    packs: list[dict[str, Any]] = []
    entries: list[dict[str, Any]] = []
    pack_bytes: dict[str, bytes] = {}
    pending: list[tuple[dict[str, Any], int, bytes]] = []
    current = bytearray()

    def flush() -> None:
        nonlocal current, pending
        if not pending:
            return
        content = bytes(current)
        digest = _sha256_uri(content)
        key = _pack_key(digest)
        pack_bytes[digest] = content
        packs.append(
            {
                "pack_digest": digest,
                "object_key": key,
                "bytes": len(content),
                "objects": len(pending),
            }
        )
        for descriptor, offset, object_content in pending:
            entries.append(
                {
                    "object_digest": descriptor["content_digest"],
                    "kind": descriptor["kind"],
                    "range": descriptor["range"],
                    "pack_digest": digest,
                    "offset": offset,
                    "length": len(object_content),
                }
            )
        current = bytearray()
        pending = []

    for descriptor in cold:
        digest = descriptor["content_digest"]
        content = object_bytes.get(digest)
        if content is None:
            raise TieredFamilyError(f"cold object bytes are missing: {digest}")
        if len(content) > max_pack_bytes:
            raise TieredFamilyError(f"object exceeds maximum pack size: {digest}")
        if pending and len(current) + len(content) > max_pack_bytes:
            flush()
        offset = len(current)
        current.extend(content)
        pending.append((descriptor, offset, content))
    flush()

    index: dict[str, Any] = {
        "schema_version": PACK_INDEX_SCHEMA_VERSION,
        "repo": copy.deepcopy(corpus_manifest["repo"]),
        "pack_index_identity": {
            "local_id": "pack-index:repo-local:kag-family",
            "artifact_kind": "kag_pack_index",
            "content_digest": ZERO_DIGEST_URI,
            "schema_ref": PACK_INDEX_SCHEMA_REF,
            "corpus_digest": corpus_manifest["corpus_identity"]["content_digest"],
        },
        "packing": {
            "format": "concatenated-byte-ranges-v1",
            "ordering": "corpus-object-order",
            "max_pack_bytes": max_pack_bytes,
            "canonical_identity": False,
        },
        "summary": {
            "packs": len(packs),
            "objects": len(entries),
            "bytes": sum(item["bytes"] for item in packs),
        },
        "packs": packs,
        "entries": entries,
    }
    index["pack_index_identity"]["content_digest"] = _identity_digest(
        index, "pack_index_identity"
    )
    validate_pack_index(index, pack_bytes)
    return index, pack_bytes


def extract_pack_object(
    pack_content: bytes,
    entry: Mapping[str, Any],
) -> bytes:
    offset = entry.get("offset")
    length = entry.get("length")
    if not isinstance(offset, int) or not isinstance(length, int):
        raise TieredFamilyError("pack entry needs integer offset and length")
    if offset < 0 or length < 0 or offset + length > len(pack_content):
        raise TieredFamilyError("pack entry byte range is out of bounds")
    content = pack_content[offset : offset + length]
    if _sha256_uri(content) != entry.get("object_digest"):
        raise TieredFamilyError("pack extraction object digest does not match")
    return content


def validate_pack_index(
    index: Mapping[str, Any],
    pack_bytes: Mapping[str, bytes] | None = None,
) -> None:
    if index.get("schema_version") != PACK_INDEX_SCHEMA_VERSION:
        raise TieredFamilyError(f"pack index schema must be {PACK_INDEX_SCHEMA_VERSION}")
    identity = index.get("pack_index_identity")
    packs = index.get("packs")
    entries = index.get("entries")
    summary = index.get("summary")
    if not all(isinstance(value, (Mapping, list)) for value in (identity, packs, entries, summary)):
        raise TieredFamilyError("pack index shape is incomplete")
    if identity.get("content_digest") != _identity_digest(index, "pack_index_identity"):
        raise TieredFamilyError("pack index digest does not match")
    for descriptor in packs:
        if not isinstance(descriptor, Mapping):
            raise TieredFamilyError("pack descriptor must be an object")
        pack_digest = descriptor.get("pack_digest")
        if not _is_digest_uri(pack_digest):
            raise TieredFamilyError("pack descriptor digest is invalid")
        if descriptor.get("object_key") != _pack_key(str(pack_digest)):
            raise TieredFamilyError(
                "pack object key must be the canonical portable path for its digest"
            )
    pack_by_digest = {
        item.get("pack_digest"): item
        for item in packs
        if isinstance(item, Mapping)
    }
    if len(pack_by_digest) != len(packs):
        raise TieredFamilyError("pack digests must be unique")
    if summary.get("packs") != len(packs) or summary.get("objects") != len(entries):
        raise TieredFamilyError("pack index summary does not match")
    if summary.get("bytes") != sum(int(item.get("bytes", -1)) for item in packs):
        raise TieredFamilyError("pack index byte total does not match")
    object_digests: set[str] = set()
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise TieredFamilyError("pack entry must be an object")
        digest = entry.get("object_digest")
        if not isinstance(digest, str) or digest in object_digests:
            raise TieredFamilyError("pack object digests must be unique")
        object_digests.add(digest)
        pack_digest = entry.get("pack_digest")
        if pack_digest not in pack_by_digest:
            raise TieredFamilyError("pack entry references an unknown pack")
        if pack_bytes is not None:
            content = pack_bytes.get(str(pack_digest))
            if content is None or _sha256_uri(content) != pack_digest:
                raise TieredFamilyError("pack bytes are missing or corrupt")
            extract_pack_object(content, entry)


def _owner_hot_baseline(git_hot_bytes: int) -> int:
    mebibyte = 1024 * 1024
    rounded = ((git_hot_bytes * 110 + 99) // 100 + mebibyte - 1) // mebibyte
    return min(GLOBAL_TRACKED_BYTES_MAX, max(4 * mebibyte, rounded * mebibyte))


def _set_digest_and_git_hot_bytes(
    manifest: dict[str, Any],
    *,
    other_manifest_bytes: int,
    hot_shard_bytes: int,
) -> None:
    manifest["distribution_identity"]["content_digest"] = ZERO_DIGEST_URI
    for _ in range(16):
        manifest["distribution_identity"]["content_digest"] = _identity_digest(
            manifest, "distribution_identity"
        )
        total = other_manifest_bytes + hot_shard_bytes + len(render_manifest(manifest))
        if manifest["summary"]["git_hot_bytes"] == total:
            return
        manifest["summary"]["git_hot_bytes"] = total
    raise TieredFamilyError("distribution Git-hot byte count did not converge")


def build_distribution_manifest(
    corpus_manifest: Mapping[str, Any],
    hot_profile: Mapping[str, Any],
    locator_manifest: Mapping[str, Any],
    pack_index: Mapping[str, Any],
    *,
    shadow_mode: bool,
) -> dict[str, Any]:
    validate_corpus_manifest(corpus_manifest)
    validate_hot_profile(hot_profile)
    validate_locator_manifest(locator_manifest)
    validate_pack_index(pack_index)
    if hot_profile["profile_identity"]["corpus_digest"] != corpus_manifest["corpus_identity"]["content_digest"]:
        raise TieredFamilyError("hot profile targets the wrong corpus")
    hot_kinds = hot_profile["selection"]["include_record_kinds"]
    hot_objects = [
        item for item in corpus_manifest["objects"] if _is_hot_kind(item["kind"], hot_kinds)
    ]
    cold_objects = [
        item for item in corpus_manifest["objects"] if not _is_hot_kind(item["kind"], hot_kinds)
    ]
    hot_set_digest = _sha256_uri(
        canonical_json_bytes([item["content_digest"] for item in hot_objects])
    )
    cold_set_digest = _sha256_uri(
        canonical_json_bytes([item["content_digest"] for item in cold_objects])
    )
    manifest: dict[str, Any] = {
        "schema_version": DISTRIBUTION_SCHEMA_VERSION,
        "repo": copy.deepcopy(corpus_manifest["repo"]),
        "distribution_identity": {
            "local_id": "family:repo-local:tiered-distribution",
            "artifact_kind": "repo_local_kag_distribution",
            "content_digest": ZERO_DIGEST_URI,
            "schema_ref": DISTRIBUTION_SCHEMA_REF,
            "corpus_digest": corpus_manifest["corpus_identity"]["content_digest"],
        },
        "corpus_manifest": {
            "path": CORPUS_MANIFEST_RELATIVE_PATH.as_posix(),
            "content_digest": corpus_manifest["corpus_identity"]["content_digest"],
        },
        "hot_profile": {
            "path": HOT_PROFILE_RELATIVE_PATH.as_posix(),
            "content_digest": hot_profile["profile_identity"]["content_digest"],
        },
        "artifact_locators": {
            "path": LOCATOR_MANIFEST_RELATIVE_PATH.as_posix(),
            "content_digest": locator_manifest["locator_identity"]["content_digest"],
        },
        "placement": {
            "state": "shadow" if shadow_mode else "externalized",
            "git_hot": {
                "record_kinds": list(hot_kinds),
                "path_template": "kag/indexes/shards/{kind}/{range}.jsonl",
                "object_set_digest": hot_set_digest,
                "objects": len(hot_objects),
            },
            "artifact_cold": {
                "record_kinds": sorted({item["kind"] for item in cold_objects}),
                "object_key_template": "objects/sha256/{prefix}/{digest}",
                "object_set_digest": cold_set_digest,
                "objects": len(cold_objects),
                "shadow_git_copy": shadow_mode,
            },
        },
        "transport": {
            "object_identity": "sha256-shard-bytes",
            "pack_index_digest": pack_index["pack_index_identity"]["content_digest"],
            "pack_format": pack_index["packing"]["format"],
            "packs": pack_index["summary"]["packs"],
            "max_pack_bytes": pack_index["packing"]["max_pack_bytes"],
            "repacking_changes_corpus_identity": False,
        },
        "trust": {
            "trust_domain": "public-kag",
            "admission": "fail-closed",
            "required_checks": [
                "digest",
                "signature",
                "owner",
                "source_ref",
                "schema_abi",
                "revocation",
                "access_policy",
            ],
        },
        "lifecycle": {
            "state": "candidate",
            "last_good_required": True,
            "rollback_by_digest": True,
        },
        "degradation": {
            "complete_states": sorted(COMPLETE_STATES),
            "states": sorted(DEGRADATION_STATES),
            "partial_may_claim_complete": False,
        },
        "budgets": {
            "owner_git_hot_bytes_max": 0,
            "owner_hard_bytes_max": GLOBAL_TRACKED_BYTES_MAX,
            "changed_generated_bytes_max": DEFAULT_DELTA_BYTES_MAX,
            "os_git_hot_bytes_max": OS_AGGREGATE_TRACKED_BYTES_MAX,
            "os_git_hot_target_bytes": OS_GIT_HOT_TARGET_BYTES,
            "aggregate_ceiling_receiptable_by_owner": False,
        },
        "summary": {
            "corpus_total_bytes": corpus_manifest["summary"]["corpus_total_bytes"],
            "git_hot_shard_bytes": sum(item["bytes"] for item in hot_objects),
            "artifact_cold_bytes": sum(item["bytes"] for item in cold_objects),
            "git_hot_objects": len(hot_objects),
            "artifact_cold_objects": len(cold_objects),
            "git_hot_bytes": 0,
            "shadow_git_bytes": (
                sum(item["bytes"] for item in cold_objects) if shadow_mode else 0
            ),
        },
        "provenance": {
            "builder": "aoa-kag:scripts/repo_local/tiered_family.py",
            "decision_ref": DECISION_REF,
            "authored_truth_owner": _repo_name(corpus_manifest),
        },
    }
    other_manifest_bytes = sum(
        len(render_manifest(payload))
        for payload in (corpus_manifest, hot_profile, locator_manifest)
    )
    _set_digest_and_git_hot_bytes(
        manifest,
        other_manifest_bytes=other_manifest_bytes,
        hot_shard_bytes=manifest["summary"]["git_hot_shard_bytes"],
    )
    manifest["budgets"]["owner_git_hot_bytes_max"] = _owner_hot_baseline(
        manifest["summary"]["git_hot_bytes"]
    )
    _set_digest_and_git_hot_bytes(
        manifest,
        other_manifest_bytes=other_manifest_bytes,
        hot_shard_bytes=manifest["summary"]["git_hot_shard_bytes"],
    )
    validate_distribution_manifest(
        manifest,
        corpus_manifest=corpus_manifest,
        hot_profile=hot_profile,
        locator_manifest=locator_manifest,
        pack_index=pack_index,
    )
    return manifest


def validate_distribution_manifest(
    manifest: Mapping[str, Any],
    *,
    corpus_manifest: Mapping[str, Any] | None = None,
    hot_profile: Mapping[str, Any] | None = None,
    locator_manifest: Mapping[str, Any] | None = None,
    pack_index: Mapping[str, Any] | None = None,
) -> None:
    if manifest.get("schema_version") != DISTRIBUTION_SCHEMA_VERSION:
        raise TieredFamilyError(
            f"distribution schema must be {DISTRIBUTION_SCHEMA_VERSION}"
        )
    identity = manifest.get("distribution_identity")
    summary = manifest.get("summary")
    budgets = manifest.get("budgets")
    if not isinstance(identity, Mapping) or not isinstance(summary, Mapping) or not isinstance(budgets, Mapping):
        raise TieredFamilyError("distribution identity, summary, or budgets are missing")
    if identity.get("content_digest") != _identity_digest(
        manifest, "distribution_identity"
    ):
        raise TieredFamilyError("distribution identity digest does not match")
    if budgets.get("owner_hard_bytes_max") != GLOBAL_TRACKED_BYTES_MAX:
        raise TieredFamilyError("per-owner hard ceiling drifted")
    if budgets.get("os_git_hot_bytes_max") != OS_AGGREGATE_TRACKED_BYTES_MAX:
        raise TieredFamilyError("OS Git-hot hard ceiling drifted")
    if budgets.get("os_git_hot_target_bytes") != OS_GIT_HOT_TARGET_BYTES:
        raise TieredFamilyError("OS Git-hot target drifted")
    if budgets.get("aggregate_ceiling_receiptable_by_owner") is not False:
        raise TieredFamilyError("owner receipt cannot override the OS ceiling")
    git_hot_bytes = summary.get("git_hot_bytes")
    if not isinstance(git_hot_bytes, int) or git_hot_bytes < 0:
        raise TieredFamilyError("distribution Git-hot byte count is invalid")
    if git_hot_bytes > budgets.get("owner_hard_bytes_max", -1):
        raise TieredFamilyError("owner Git-hot surface exceeds the hard ceiling")
    if corpus_manifest is not None:
        validate_corpus_manifest(corpus_manifest)
        if identity.get("corpus_digest") != corpus_manifest["corpus_identity"]["content_digest"]:
            raise TieredFamilyError("distribution targets the wrong corpus")
    if hot_profile is not None:
        validate_hot_profile(hot_profile)
        if manifest.get("hot_profile", {}).get("content_digest") != hot_profile["profile_identity"]["content_digest"]:
            raise TieredFamilyError("distribution hot profile digest does not match")
    if corpus_manifest is not None and hot_profile is not None:
        corpus_digest = corpus_manifest["corpus_identity"]["content_digest"]
        if hot_profile["profile_identity"].get("corpus_digest") != corpus_digest:
            raise TieredFamilyError("distribution hot profile targets the wrong corpus")
        hot_kinds = hot_profile["selection"]["include_record_kinds"]
        hot_objects = [
            item
            for item in corpus_manifest["objects"]
            if _is_hot_kind(item["kind"], hot_kinds)
        ]
        cold_objects = [
            item
            for item in corpus_manifest["objects"]
            if not _is_hot_kind(item["kind"], hot_kinds)
        ]
        placement = manifest.get("placement")
        if not isinstance(placement, Mapping) or placement.get("state") not in {
            "shadow",
            "externalized",
        }:
            raise TieredFamilyError("distribution placement state is invalid")
        git_hot_placement = placement.get("git_hot")
        cold_placement = placement.get("artifact_cold")
        if not isinstance(git_hot_placement, Mapping) or not isinstance(
            cold_placement, Mapping
        ):
            raise TieredFamilyError("distribution placement sets are missing")
        expected_hot_digest = _sha256_uri(
            canonical_json_bytes(
                [item["content_digest"] for item in hot_objects]
            )
        )
        expected_cold_digest = _sha256_uri(
            canonical_json_bytes(
                [item["content_digest"] for item in cold_objects]
            )
        )
        expected_placement = {
            "git_hot record kinds": (
                git_hot_placement.get("record_kinds"),
                list(hot_kinds),
            ),
            "git_hot object count": (
                git_hot_placement.get("objects"),
                len(hot_objects),
            ),
            "git_hot object set": (
                git_hot_placement.get("object_set_digest"),
                expected_hot_digest,
            ),
            "artifact_cold record kinds": (
                cold_placement.get("record_kinds"),
                sorted({item["kind"] for item in cold_objects}),
            ),
            "artifact_cold object count": (
                cold_placement.get("objects"),
                len(cold_objects),
            ),
            "artifact_cold object set": (
                cold_placement.get("object_set_digest"),
                expected_cold_digest,
            ),
            "artifact_cold shadow state": (
                cold_placement.get("shadow_git_copy"),
                placement["state"] == "shadow",
            ),
        }
        for label, (actual, expected) in expected_placement.items():
            if actual != expected:
                raise TieredFamilyError(
                    f"distribution {label} does not match corpus placement"
                )
        hot_shard_bytes = sum(int(item["bytes"]) for item in hot_objects)
        cold_shard_bytes = sum(int(item["bytes"]) for item in cold_objects)
        expected_summary = {
            "corpus_total_bytes": hot_shard_bytes + cold_shard_bytes,
            "git_hot_shard_bytes": hot_shard_bytes,
            "artifact_cold_bytes": cold_shard_bytes,
            "git_hot_objects": len(hot_objects),
            "artifact_cold_objects": len(cold_objects),
            "shadow_git_bytes": (
                cold_shard_bytes if placement["state"] == "shadow" else 0
            ),
        }
        for field, expected in expected_summary.items():
            if summary.get(field) != expected:
                raise TieredFamilyError(
                    f"distribution summary {field} does not match corpus placement"
                )
    if locator_manifest is not None:
        validate_locator_manifest(locator_manifest)
        if manifest.get("artifact_locators", {}).get("content_digest") != locator_manifest["locator_identity"]["content_digest"]:
            raise TieredFamilyError("distribution locator digest does not match")
        if corpus_manifest is not None and hot_profile is not None:
            expected_git_hot_bytes = (
                len(render_manifest(corpus_manifest))
                + len(render_manifest(hot_profile))
                + len(render_manifest(locator_manifest))
                + int(summary["git_hot_shard_bytes"])
                + len(render_manifest(manifest))
            )
            if git_hot_bytes != expected_git_hot_bytes:
                raise TieredFamilyError(
                    "distribution summary git_hot_bytes does not match Git-hot surface"
                )
    if pack_index is not None:
        validate_pack_index(pack_index)
        if manifest.get("transport", {}).get("pack_index_digest") != pack_index["pack_index_identity"]["content_digest"]:
            raise TieredFamilyError("distribution pack index digest does not match")


def build_owner_release(
    corpus_manifest: Mapping[str, Any],
    distribution_manifest: Mapping[str, Any],
    hot_profile: Mapping[str, Any],
    locator_manifest: Mapping[str, Any],
    pack_index: Mapping[str, Any],
) -> dict[str, Any]:
    validate_distribution_manifest(
        distribution_manifest,
        corpus_manifest=corpus_manifest,
        hot_profile=hot_profile,
        locator_manifest=locator_manifest,
        pack_index=pack_index,
    )
    pack_entry_by_object = {
        item["object_digest"]: item
        for item in pack_index["entries"]
    }
    hot_kinds = hot_profile["selection"]["include_record_kinds"]
    objects = []
    for descriptor in corpus_manifest["objects"]:
        digest = descriptor["content_digest"]
        placement = "git_hot" if _is_hot_kind(descriptor["kind"], hot_kinds) else "artifact_cold"
        item = {
            **copy.deepcopy(descriptor),
            "placement": placement,
            "object_key": _object_key(digest),
        }
        pack_entry = pack_entry_by_object.get(digest)
        if pack_entry is not None:
            item["pack"] = {
                key: pack_entry[key]
                for key in ("pack_digest", "offset", "length")
            }
        objects.append(item)
    release: dict[str, Any] = {
        "schema_version": OWNER_RELEASE_SCHEMA_VERSION,
        "repo": copy.deepcopy(corpus_manifest["repo"]),
        "release_identity": {
            "local_id": "release:repo-local:kag-family",
            "artifact_kind": "kag_owner_family_release",
            "artifact_class": OWNER_RELEASE_ARTIFACT_CLASS,
            "abi_epoch": OWNER_RELEASE_ABI_EPOCH,
            "content_digest": ZERO_DIGEST_URI,
            "schema_ref": OWNER_RELEASE_SCHEMA_REF,
            "corpus_digest": corpus_manifest["corpus_identity"]["content_digest"],
            "distribution_digest": distribution_manifest["distribution_identity"]["content_digest"],
        },
        "manifests": {
            "corpus_digest": corpus_manifest["corpus_identity"]["content_digest"],
            "distribution_digest": distribution_manifest["distribution_identity"]["content_digest"],
            "hot_profile_digest": hot_profile["profile_identity"]["content_digest"],
            "locator_digest": locator_manifest["locator_identity"]["content_digest"],
            "pack_index_digest": pack_index["pack_index_identity"]["content_digest"],
        },
        "source": {
            "snapshot": corpus_manifest["corpus_identity"]["source_snapshot"],
            "owner": _repo_name(corpus_manifest),
            "ref": str(corpus_manifest["repo"].get("git_ref") or ""),
        },
        "epochs": copy.deepcopy(corpus_manifest["epochs"]),
        "objects": objects,
        "packs": copy.deepcopy(pack_index["packs"]),
        "compatibility": copy.deepcopy(corpus_manifest["compatibility"]),
        "measurements": {
            "git_hot_bytes": distribution_manifest["summary"][
                "git_hot_bytes"
            ],
            "corpus_total_bytes": distribution_manifest["summary"][
                "corpus_total_bytes"
            ],
            "artifact_unique_bytes": distribution_manifest["summary"][
                "artifact_cold_bytes"
            ],
        },
        "provenance": {
            "builder": "aoa-kag:scripts/repo_local/tiered_family.py",
            "decision_ref": DECISION_REF,
            "verification_receipt": "",
        },
        "lifecycle": {
            "state": "built-local",
            "supersedes": "",
            "rollback_to": "",
            "revoked": False,
        },
        "signature": {
            "algorithm": "none",
            "subject_digest": ZERO_DIGEST_URI,
            "signature_ref": "",
            "verification_state": "unsigned-candidate",
        },
    }
    release["release_identity"]["content_digest"] = _identity_digest(
        release,
        "release_identity",
        excluded_fields=("signature",),
    )
    release["signature"]["subject_digest"] = release["release_identity"]["content_digest"]
    validate_owner_release(release)
    return release


def owner_release_digest(release: Mapping[str, Any]) -> str:
    return _identity_digest(
        release,
        "release_identity",
        excluded_fields=("signature",),
    )


def prepare_owner_release_lifecycle(
    release: Mapping[str, Any],
    *,
    state: str,
    source_ref: str = "",
    verification_receipt: str = "",
    supersedes: str = "",
    rollback_to: str = "",
) -> dict[str, Any]:
    if state not in OWNER_RELEASE_LIFECYCLE_STATES:
        raise TieredFamilyError(f"invalid owner release lifecycle: {state}")
    validate_owner_release(release)
    prepared = copy.deepcopy(dict(release))
    source = prepared.get("source")
    repo = prepared.get("repo")
    provenance = prepared.get("provenance")
    if not all(isinstance(value, dict) for value in (source, repo, provenance)):
        raise TieredFamilyError(
            "owner release source, repo, or provenance is missing"
        )
    selected_source_ref = canonical_source_ref(
        source_ref or str(source.get("ref") or repo.get("git_ref") or "")
    )
    if state in SOURCE_BOUND_LIFECYCLE_STATES and not _is_exact_git_commit_ref(
        selected_source_ref
    ):
        raise TieredFamilyError(
            f"owner release lifecycle {state} requires an exact commit:<hex> source ref"
        )
    source["ref"] = selected_source_ref
    repo["git_ref"] = selected_source_ref
    selected_verification_receipt = str(
        verification_receipt or provenance.get("verification_receipt") or ""
    ).strip()
    if state in SOURCE_BOUND_LIFECYCLE_STATES and not selected_verification_receipt:
        raise TieredFamilyError(
            f"owner release lifecycle {state} requires a verification receipt"
        )
    provenance["verification_receipt"] = selected_verification_receipt
    for label, value in (
        ("supersedes", supersedes),
        ("rollback_to", rollback_to),
    ):
        if value and not _is_digest_uri(value):
            raise TieredFamilyError(
                f"owner release {label} must be empty or a sha256 digest URI"
            )
    prepared["lifecycle"] = {
        "state": state,
        "supersedes": supersedes,
        "rollback_to": rollback_to,
        "revoked": state == "revoked",
    }
    identity = prepared.get("release_identity")
    if not isinstance(identity, dict):
        raise TieredFamilyError("owner release identity is missing")
    identity["content_digest"] = ZERO_DIGEST_URI
    digest = owner_release_digest(prepared)
    identity["content_digest"] = digest
    prepared["signature"] = {
        "algorithm": "none",
        "subject_digest": digest,
        "signature_ref": "",
        "verification_state": "unsigned-candidate",
    }
    validate_owner_release(prepared)
    return prepared


def attach_owner_release_signature(
    release: Mapping[str, Any],
    *,
    algorithm: str,
    signature_ref: str,
    verification_state: str,
) -> dict[str, Any]:
    signed = copy.deepcopy(dict(release))
    identity = signed.get("release_identity")
    if not isinstance(identity, Mapping):
        raise TieredFamilyError("owner release identity is missing")
    signed["signature"] = {
        "algorithm": algorithm,
        "subject_digest": identity["content_digest"],
        "signature_ref": signature_ref,
        "verification_state": verification_state,
    }
    validate_owner_release(signed)
    return signed


def validate_owner_release(release: Mapping[str, Any]) -> None:
    if release.get("schema_version") != OWNER_RELEASE_SCHEMA_VERSION:
        raise TieredFamilyError(f"owner release schema must be {OWNER_RELEASE_SCHEMA_VERSION}")
    identity = release.get("release_identity")
    signature = release.get("signature")
    repo = release.get("repo")
    source = release.get("source")
    provenance = release.get("provenance")
    lifecycle = release.get("lifecycle")
    if not all(
        isinstance(value, Mapping)
        for value in (
            identity,
            signature,
            repo,
            source,
            provenance,
            lifecycle,
        )
    ):
        raise TieredFamilyError(
            "owner release identity, source, lifecycle, provenance, or signature is missing"
        )
    if identity.get("artifact_kind") != OWNER_RELEASE_ARTIFACT_CLASS:
        raise TieredFamilyError("owner release artifact kind does not match")
    if identity.get("artifact_class") != OWNER_RELEASE_ARTIFACT_CLASS:
        raise TieredFamilyError("owner release artifact class does not match")
    if identity.get("abi_epoch") != OWNER_RELEASE_ABI_EPOCH:
        raise TieredFamilyError("owner release ABI epoch does not match")
    owner = repo.get("name")
    if not isinstance(owner, str) or not owner or source.get("owner") != owner:
        raise TieredFamilyError("owner release source owner does not match repo")
    source_ref = source.get("ref")
    if not isinstance(source_ref, str) or not source_ref:
        raise TieredFamilyError("owner release source ref is missing")
    if repo.get("git_ref") != source_ref:
        raise TieredFamilyError("owner release repo and source refs do not match")
    if not _is_digest_uri(source.get("snapshot")):
        raise TieredFamilyError("owner release source snapshot is not a sha256 digest")
    state = lifecycle.get("state")
    if state not in OWNER_RELEASE_LIFECYCLE_STATES:
        raise TieredFamilyError("owner release lifecycle state is invalid")
    if lifecycle.get("revoked") is not (state == "revoked"):
        raise TieredFamilyError("owner release revoked flag does not match lifecycle")
    if state in SOURCE_BOUND_LIFECYCLE_STATES:
        if not _is_exact_git_commit_ref(source_ref):
            raise TieredFamilyError(
                f"owner release lifecycle {state} requires an exact commit:<hex> source ref"
            )
        if not str(provenance.get("verification_receipt") or "").strip():
            raise TieredFamilyError(
                f"owner release lifecycle {state} requires a verification receipt"
            )
    for label in ("supersedes", "rollback_to"):
        value = lifecycle.get(label)
        if not isinstance(value, str) or (value and not _is_digest_uri(value)):
            raise TieredFamilyError(
                f"owner release {label} must be empty or a sha256 digest URI"
            )
    expected = owner_release_digest(release)
    if identity.get("content_digest") != expected:
        raise TieredFamilyError("owner release digest does not match")
    if signature.get("subject_digest") != expected:
        raise TieredFamilyError("owner release signature targets the wrong digest")


def build_tiered_family(
    portable_manifest: Mapping[str, Any],
    shards: Mapping[Path, bytes],
    *,
    hot_kinds: Sequence[str] = DEFAULT_HOT_KINDS,
    max_pack_bytes: int = DEFAULT_PACK_BYTES_MAX,
    shadow_mode: bool = True,
    mirrors: Sequence[Mapping[str, Any]] | None = None,
    migration: Mapping[str, Any] | None = None,
) -> TieredFamilyBuild:
    corpus = build_corpus_manifest(
        portable_manifest,
        shards,
        migration=migration,
    )
    hot_profile = build_hot_profile(corpus, hot_kinds=hot_kinds)
    locators = build_locator_manifest(corpus, mirrors=mirrors)
    object_bytes = _object_bytes_by_digest(corpus, shards)
    pack_index, pack_bytes = build_pack_index(
        corpus,
        object_bytes,
        hot_kinds=hot_kinds,
        max_pack_bytes=max_pack_bytes,
    )
    distribution = build_distribution_manifest(
        corpus,
        hot_profile,
        locators,
        pack_index,
        shadow_mode=shadow_mode,
    )
    release = build_owner_release(
        corpus,
        distribution,
        hot_profile,
        locators,
        pack_index,
    )
    hot_shards: dict[Path, bytes] = {}
    cold_shards: dict[Path, bytes] = {}
    hot_kind_set = set(hot_profile["selection"]["include_record_kinds"])
    for descriptor in corpus["objects"]:
        path = _shard_path(descriptor["kind"], descriptor["range"])
        target = hot_shards if descriptor["kind"] in hot_kind_set else cold_shards
        target[path] = object_bytes[descriptor["content_digest"]]
    return TieredFamilyBuild(
        corpus_manifest=corpus,
        hot_profile=hot_profile,
        locator_manifest=locators,
        pack_index=pack_index,
        distribution_manifest=distribution,
        owner_release=release,
        object_bytes=object_bytes,
        hot_shards=hot_shards,
        cold_shards=cold_shards,
        pack_bytes=pack_bytes,
    )


def _write_if_changed(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.is_file() or path.read_bytes() != content:
        path.write_bytes(content)


def write_tiered_git_surface(
    repo_root: Path,
    build: TieredFamilyBuild,
    *,
    externalize: bool,
) -> None:
    root = repo_root.resolve()
    expected_shards = dict(build.hot_shards)
    if not externalize:
        expected_shards.update(build.cold_shards)
    for path, content in expected_shards.items():
        _write_if_changed(root / path, content)
    existing = {
        path.relative_to(root)
        for path in (root / SHARD_ROOT_RELATIVE_PATH).glob("*/*.jsonl")
        if path.is_file()
    }
    for path in sorted(existing - set(expected_shards)):
        (root / path).unlink()
    _write_if_changed(
        root / CORPUS_MANIFEST_RELATIVE_PATH,
        render_manifest(build.corpus_manifest),
    )
    _write_if_changed(
        root / HOT_PROFILE_RELATIVE_PATH,
        render_manifest(build.hot_profile),
    )
    _write_if_changed(
        root / LOCATOR_MANIFEST_RELATIVE_PATH,
        render_manifest(build.locator_manifest),
    )
    _write_if_changed(
        root / MANIFEST_RELATIVE_PATH,
        render_manifest(build.distribution_manifest),
    )


def check_tiered_git_surface(
    repo_root: Path,
    build: TieredFamilyBuild,
    *,
    externalized: bool,
) -> bool:
    root = repo_root.resolve()
    expected_shards = dict(build.hot_shards)
    if not externalized:
        expected_shards.update(build.cold_shards)
    expected_manifests = {
        CORPUS_MANIFEST_RELATIVE_PATH: build.corpus_manifest,
        HOT_PROFILE_RELATIVE_PATH: build.hot_profile,
        LOCATOR_MANIFEST_RELATIVE_PATH: build.locator_manifest,
        MANIFEST_RELATIVE_PATH: build.distribution_manifest,
    }
    for path, payload in expected_manifests.items():
        destination = root / path
        if not destination.is_file() or destination.read_bytes() != render_manifest(payload):
            return False
    for path, content in expected_shards.items():
        destination = root / path
        if not destination.is_file() or destination.read_bytes() != content:
            return False
    actual_shards = {
        path.relative_to(root)
        for path in (root / SHARD_ROOT_RELATIVE_PATH).glob("*/*.jsonl")
        if path.is_file()
    }
    return actual_shards == set(expected_shards)


def tiered_budget_projection(
    build: TieredFamilyBuild,
    *,
    externalized: bool,
) -> dict[str, Any]:
    """Adapt the v4 Git surface to the durable generated-delta budget ABI."""
    expected_shards = dict(build.hot_shards)
    if not externalized:
        expected_shards.update(build.cold_shards)
    control_paths = (
        CORPUS_MANIFEST_RELATIVE_PATH,
        HOT_PROFILE_RELATIVE_PATH,
        LOCATOR_MANIFEST_RELATIVE_PATH,
    )
    distribution = build.distribution_manifest
    corpus_digest = build.corpus_manifest["corpus_identity"][
        "content_digest"
    ].removeprefix("sha256:")
    return {
        "schema_version": DISTRIBUTION_SCHEMA_VERSION,
        "repo": copy.deepcopy(distribution["repo"]),
        "family_identity": {
            "content_digest": corpus_digest,
        },
        "budgets": {
            "tracked_bytes_max": distribution["budgets"][
                "owner_git_hot_bytes_max"
            ],
            "changed_generated_bytes_max": distribution["budgets"][
                "changed_generated_bytes_max"
            ],
        },
        "summary": {
            "tracked_bytes": distribution["summary"]["git_hot_bytes"],
        },
        "shards": [
            {"path": path.as_posix()}
            for path in sorted({*control_paths, *expected_shards})
        ],
    }


def write_tiered_artifact(
    artifact_root: Path,
    build: TieredFamilyBuild,
) -> dict[str, int]:
    root = artifact_root.resolve()
    added_objects = 0
    reused_objects = 0
    for digest, content in build.object_bytes.items():
        destination = root / _object_key(digest)
        if destination.is_file():
            if destination.read_bytes() != content:
                raise TieredFamilyError(f"CAS object collision: {digest}")
            reused_objects += 1
        else:
            _write_if_changed(destination, content)
            added_objects += 1
    for digest, content in build.pack_bytes.items():
        destination = root / _pack_key(digest)
        if destination.is_file() and destination.read_bytes() != content:
            raise TieredFamilyError(f"CAS pack collision: {digest}")
        _write_if_changed(destination, content)
    release_root = root / _release_relative_root(build.distribution_manifest)
    _write_if_changed(release_root / CORPUS_MANIFEST_RELATIVE_PATH.name, render_manifest(build.corpus_manifest))
    _write_if_changed(release_root / MANIFEST_RELATIVE_PATH.name, render_manifest(build.distribution_manifest))
    _write_if_changed(release_root / HOT_PROFILE_RELATIVE_PATH.name, render_manifest(build.hot_profile))
    _write_if_changed(release_root / LOCATOR_MANIFEST_RELATIVE_PATH.name, render_manifest(build.locator_manifest))
    _write_if_changed(release_root / PACK_INDEX_ARTIFACT_PATH, render_manifest(build.pack_index))
    _write_if_changed(release_root / OWNER_RELEASE_ARTIFACT_PATH, render_manifest(build.owner_release))
    return {
        "objects_added": added_objects,
        "objects_reused": reused_objects,
        "packs": len(build.pack_bytes),
    }


def check_tiered_artifact(
    artifact_root: Path,
    build: TieredFamilyBuild,
) -> bool:
    root = artifact_root.resolve()
    for digest, content in build.object_bytes.items():
        destination = root / _object_key(digest)
        if not destination.is_file() or destination.read_bytes() != content:
            return False
    for digest, content in build.pack_bytes.items():
        destination = root / _pack_key(digest)
        if not destination.is_file() or destination.read_bytes() != content:
            return False
    release_root = root / _release_relative_root(build.distribution_manifest)
    expected = {
        CORPUS_MANIFEST_RELATIVE_PATH.name: build.corpus_manifest,
        MANIFEST_RELATIVE_PATH.name: build.distribution_manifest,
        HOT_PROFILE_RELATIVE_PATH.name: build.hot_profile,
        LOCATOR_MANIFEST_RELATIVE_PATH.name: build.locator_manifest,
        PACK_INDEX_ARTIFACT_PATH.as_posix(): build.pack_index,
        OWNER_RELEASE_ARTIFACT_PATH.as_posix(): build.owner_release,
    }
    return all(
        (release_root / path).is_file()
        and (release_root / path).read_bytes() == render_manifest(payload)
        for path, payload in expected.items()
    )


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise TieredFamilyError(f"cannot read {label}: {path}") from exc
    if not isinstance(payload, dict):
        raise TieredFamilyError(f"{label} must be an object")
    return payload


def load_tiered_manifests(
    repo_root: Path,
    *,
    artifact_root: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any] | None]:
    root = repo_root.resolve()
    distribution = _read_json(root / MANIFEST_RELATIVE_PATH, "distribution manifest")
    corpus = _read_json(root / CORPUS_MANIFEST_RELATIVE_PATH, "corpus manifest")
    hot_profile = _read_json(root / HOT_PROFILE_RELATIVE_PATH, "hot profile")
    locators = _read_json(root / LOCATOR_MANIFEST_RELATIVE_PATH, "artifact locators")
    pack_index = None
    if artifact_root is not None:
        release_root = (
            artifact_root.resolve()
            / _release_relative_root(distribution)
        )
        pack_index = _read_json(
            release_root / PACK_INDEX_ARTIFACT_PATH,
            "pack index",
        )
    validate_distribution_manifest(
        distribution,
        corpus_manifest=corpus,
        hot_profile=hot_profile,
        locator_manifest=locators,
        pack_index=pack_index,
    )
    return distribution, corpus, hot_profile, locators, pack_index


def _validate_object_content(
    descriptor: Mapping[str, Any],
    content: bytes,
) -> list[dict[str, Any]]:
    if _sha256_uri(content) != descriptor.get("content_digest"):
        raise TieredFamilyError("tiered shard digest does not match")
    if len(content) != descriptor.get("bytes"):
        raise TieredFamilyError("tiered shard byte count does not match")
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TieredFamilyError(
                f"tiered shard line {line_number} is not valid JSON"
            ) from exc
        if not isinstance(row, dict) or row.get("_kind") != descriptor.get("kind"):
            raise TieredFamilyError("tiered shard record kind does not match")
        rows.append(row)
    if len(rows) != descriptor.get("records"):
        raise TieredFamilyError("tiered shard record count does not match")
    return rows


def load_tiered_rows(
    repo_root: Path,
    *,
    artifact_root: Path | None = None,
    allow_shadow_git: bool = True,
    allow_hot_only: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    distribution, corpus, hot_profile, _, _ = load_tiered_manifests(
        repo_root,
        artifact_root=artifact_root,
    )
    root = repo_root.resolve()
    artifact = artifact_root.resolve() if artifact_root is not None else None
    hot_kinds = hot_profile["selection"]["include_record_kinds"]
    rows: list[dict[str, Any]] = []
    routes: dict[str, int] = {"git_hot": 0, "local_cas": 0, "shadow_git": 0}
    missing: list[str] = []
    for descriptor in corpus["objects"]:
        path = root / _shard_path(descriptor["kind"], descriptor["range"])
        content: bytes | None = None
        if _is_hot_kind(descriptor["kind"], hot_kinds):
            if path.is_file():
                content = path.read_bytes()
                routes["git_hot"] += 1
        else:
            if artifact is not None:
                candidate = artifact / _object_key(descriptor["content_digest"])
                if candidate.is_file():
                    content = candidate.read_bytes()
                    routes["local_cas"] += 1
            if content is None and allow_shadow_git and path.is_file():
                content = path.read_bytes()
                routes["shadow_git"] += 1
        if content is None:
            missing.append(descriptor["content_digest"])
            continue
        rows.extend(_validate_object_content(descriptor, content))
    if missing and not allow_hot_only:
        state = "artifact_required" if artifact is None else "artifact_unavailable"
        raise TieredFamilyUnavailable(
            state,
            missing,
            corpus_digest=corpus["corpus_identity"]["content_digest"],
            distribution_digest=distribution["distribution_identity"][
                "content_digest"
            ],
        )
    state = "hot_only" if missing else "complete"
    result_state = {
        "state": state,
        "complete": not missing,
        "missing_objects": missing,
        "routes": routes,
        "corpus_digest": corpus["corpus_identity"]["content_digest"],
        "distribution_digest": distribution["distribution_identity"]["content_digest"],
    }
    return rows, result_state


def load_tiered_family(
    repo_root: Path,
    *,
    artifact_root: Path | None = None,
    allow_shadow_git: bool = True,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, Any], dict[str, Any]]:
    distribution, corpus, _, _, _ = load_tiered_manifests(
        repo_root,
        artifact_root=artifact_root,
    )
    rows, state = load_tiered_rows(
        repo_root,
        artifact_root=artifact_root,
        allow_shadow_git=allow_shadow_git,
    )
    source, family = reconstruct_compatibility_family(corpus, rows)
    return source, family, distribution, state


def validate_tiered_family(
    repo_root: Path,
    *,
    artifact_root: Path | None = None,
    allow_shadow_git: bool = True,
) -> dict[str, Any]:
    source, family, distribution, state = load_tiered_family(
        repo_root,
        artifact_root=artifact_root,
        allow_shadow_git=allow_shadow_git,
    )
    return {
        "repo": distribution["repo"]["name"],
        "corpus_digest": distribution["distribution_identity"]["corpus_digest"],
        "distribution_digest": distribution["distribution_identity"]["content_digest"],
        "state": state,
        "source_records": len(source["records"]),
        "compatibility_views": {
            kind: len(payload["entries"])
            for kind, payload in family.items()
        },
    }


def validate_tiered_artifact_release(
    repo_root: Path,
    artifact_root: Path,
) -> dict[str, Any]:
    distribution, corpus, hot_profile, locators, pack_index = load_tiered_manifests(
        repo_root,
        artifact_root=artifact_root,
    )
    if pack_index is None:
        raise TieredFamilyError("tiered artifact release needs a pack index")
    root = artifact_root.resolve()
    release_root = root / _release_relative_root(distribution)
    release = _read_json(
        release_root / OWNER_RELEASE_ARTIFACT_PATH,
        "owner release",
    )
    _validate_release_manifest_set(
        release,
        distribution=distribution,
        corpus=corpus,
        hot_profile=hot_profile,
        locators=locators,
        pack_index=pack_index,
    )
    for descriptor in corpus["objects"]:
        object_path = root / _object_key(descriptor["content_digest"])
        try:
            content = object_path.read_bytes()
        except FileNotFoundError as exc:
            raise TieredFamilyError(
                f"artifact release is missing CAS object "
                f"{descriptor['content_digest']}"
            ) from exc
        _validate_object_content(descriptor, content)
    pack_bytes: dict[str, bytes] = {}
    for descriptor in pack_index["packs"]:
        path = root / descriptor["object_key"]
        content = path.read_bytes()
        if _sha256_uri(content) != descriptor["pack_digest"]:
            raise TieredFamilyError("artifact pack digest does not match")
        pack_bytes[descriptor["pack_digest"]] = content
    validate_pack_index(pack_index, pack_bytes)
    _, _, _, state = load_tiered_family(
        repo_root,
        artifact_root=root,
        allow_shadow_git=False,
    )
    return {
        "owner": _repo_name(distribution),
        "release_digest": release["release_identity"]["content_digest"],
        "corpus_digest": corpus["corpus_identity"]["content_digest"],
        "distribution_digest": distribution["distribution_identity"]["content_digest"],
        "objects": len(corpus["objects"]),
        "packs": len(pack_index["packs"]),
        "state": state["state"],
        "signature_state": release["signature"]["verification_state"],
    }


def _validate_release_manifest_set(
    release: Mapping[str, Any],
    *,
    distribution: Mapping[str, Any],
    corpus: Mapping[str, Any],
    hot_profile: Mapping[str, Any],
    locators: Mapping[str, Any],
    pack_index: Mapping[str, Any],
) -> None:
    validate_owner_release(release)
    owner = _repo_name(corpus)
    release_repo = release.get("repo")
    release_source = release.get("source")
    if not isinstance(release_repo, Mapping) or not isinstance(
        release_source, Mapping
    ):
        raise TieredFamilyError("owner release source owner is missing")
    if release_repo.get("name") != owner or release_source.get("owner") != owner:
        raise TieredFamilyError("owner release owner does not match corpus")
    corpus_identity = corpus.get("corpus_identity")
    if not isinstance(corpus_identity, Mapping):
        raise TieredFamilyError("corpus identity is missing")
    if release_source.get("snapshot") != corpus_identity.get("source_snapshot"):
        raise TieredFamilyError(
            "owner release source snapshot does not match corpus"
        )
    identity = release.get("release_identity")
    if not isinstance(identity, Mapping):
        raise TieredFamilyError("owner release identity is missing")
    if identity.get("corpus_digest") != corpus["corpus_identity"]["content_digest"]:
        raise TieredFamilyError("owner release corpus identity does not match")
    if identity.get("distribution_digest") != distribution[
        "distribution_identity"
    ]["content_digest"]:
        raise TieredFamilyError("owner release distribution identity does not match")
    expected_manifest_digests = {
        "corpus_digest": corpus["corpus_identity"]["content_digest"],
        "distribution_digest": distribution["distribution_identity"][
            "content_digest"
        ],
        "hot_profile_digest": hot_profile["profile_identity"]["content_digest"],
        "locator_digest": locators["locator_identity"]["content_digest"],
        "pack_index_digest": pack_index["pack_index_identity"]["content_digest"],
    }
    manifests = release.get("manifests")
    if not isinstance(manifests, Mapping):
        raise TieredFamilyError("owner release manifest digest set is missing")
    for field, value in expected_manifest_digests.items():
        if manifests.get(field) != value:
            raise TieredFamilyError(f"owner release {field} does not match")


def export_portable_bundle(
    repo_root: Path,
    artifact_root: Path,
    destination: Path,
    *,
    lifecycle_state: str | None = None,
    source_ref: str = "",
    verification_receipt: str = "",
    supersedes: str = "",
    rollback_to: str = "",
) -> dict[str, Any]:
    source_root = artifact_root.resolve()
    target = destination.resolve()
    if target.exists() and any(target.iterdir()):
        raise TieredFamilyError("bundle destination must be absent or empty")
    distribution, corpus, hot_profile, locators, pack_index = load_tiered_manifests(
        repo_root,
        artifact_root=source_root,
    )
    if pack_index is None:
        raise TieredFamilyError("artifact pack index is required for export")
    release_root = source_root / _release_relative_root(distribution)
    release = _read_json(
        release_root / OWNER_RELEASE_ARTIFACT_PATH,
        "owner release",
    )
    if lifecycle_state is not None:
        release = prepare_owner_release_lifecycle(
            release,
            state=lifecycle_state,
            source_ref=source_ref,
            verification_receipt=verification_receipt,
            supersedes=supersedes,
            rollback_to=rollback_to,
        )
    elif any((source_ref, verification_receipt, supersedes, rollback_to)):
        raise TieredFamilyError(
            "release lifecycle coordinates require lifecycle_state"
        )
    _validate_release_manifest_set(
        release,
        distribution=distribution,
        corpus=corpus,
        hot_profile=hot_profile,
        locators=locators,
        pack_index=pack_index,
    )
    target.mkdir(parents=True, exist_ok=True)
    for path, payload in (
        (CORPUS_MANIFEST_RELATIVE_PATH, corpus),
        (MANIFEST_RELATIVE_PATH, distribution),
        (HOT_PROFILE_RELATIVE_PATH, hot_profile),
        (LOCATOR_MANIFEST_RELATIVE_PATH, locators),
        (PACK_INDEX_ARTIFACT_PATH, pack_index),
        (OWNER_RELEASE_ARTIFACT_PATH, release),
    ):
        _write_if_changed(target / path, render_manifest(payload))
    copied_objects = 0
    for descriptor in corpus["objects"]:
        key = Path(_object_key(descriptor["content_digest"]))
        content = (source_root / key).read_bytes()
        _validate_object_content(descriptor, content)
        _write_if_changed(target / key, content)
        copied_objects += 1
    for descriptor in pack_index["packs"]:
        key = Path(descriptor["object_key"])
        content = (source_root / key).read_bytes()
        if _sha256_uri(content) != descriptor["pack_digest"]:
            raise TieredFamilyError("bundle export pack digest does not match")
        _write_if_changed(target / key, content)
    bundle: dict[str, Any] = {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "bundle_identity": {
            "content_digest": ZERO_DIGEST_URI,
            "corpus_digest": corpus["corpus_identity"]["content_digest"],
            "distribution_digest": distribution["distribution_identity"]["content_digest"],
            "release_digest": release["release_identity"]["content_digest"],
        },
        "summary": {
            "objects": copied_objects,
            "packs": len(pack_index["packs"]),
            "bytes": sum(item["bytes"] for item in corpus["objects"]),
        },
        "network_required": False,
        "decision_ref": DECISION_REF,
    }
    bundle["bundle_identity"]["content_digest"] = _identity_digest(
        bundle, "bundle_identity"
    )
    _write_if_changed(target / BUNDLE_MANIFEST_PATH, render_manifest(bundle))
    return bundle


def import_portable_bundle(
    bundle_root: Path,
    artifact_root: Path,
) -> dict[str, int]:
    source = bundle_root.resolve()
    target = artifact_root.resolve()
    bundle = _read_json(source / BUNDLE_MANIFEST_PATH, "bundle manifest")
    if bundle.get("schema_version") != BUNDLE_SCHEMA_VERSION or bundle.get(
        "bundle_identity", {}
    ).get("content_digest") != _identity_digest(bundle, "bundle_identity"):
        raise TieredFamilyError("portable bundle identity does not match")
    corpus = _read_json(source / CORPUS_MANIFEST_RELATIVE_PATH, "bundle corpus")
    validate_corpus_manifest(corpus)
    distribution = _read_json(
        source / MANIFEST_RELATIVE_PATH,
        "bundle distribution",
    )
    hot_profile = _read_json(
        source / HOT_PROFILE_RELATIVE_PATH,
        "bundle hot profile",
    )
    locators = _read_json(
        source / LOCATOR_MANIFEST_RELATIVE_PATH,
        "bundle locators",
    )
    pack_index = _read_json(
        source / PACK_INDEX_ARTIFACT_PATH,
        "bundle pack index",
    )
    release = _read_json(
        source / OWNER_RELEASE_ARTIFACT_PATH,
        "bundle owner release",
    )
    validate_distribution_manifest(
        distribution,
        corpus_manifest=corpus,
        hot_profile=hot_profile,
        locator_manifest=locators,
        pack_index=pack_index,
    )
    _validate_release_manifest_set(
        release,
        distribution=distribution,
        corpus=corpus,
        hot_profile=hot_profile,
        locators=locators,
        pack_index=pack_index,
    )
    bundle_identity = bundle.get("bundle_identity")
    if not isinstance(bundle_identity, Mapping):
        raise TieredFamilyError("portable bundle identity is missing")
    expected_bundle_links = {
        "corpus_digest": corpus["corpus_identity"]["content_digest"],
        "distribution_digest": distribution["distribution_identity"][
            "content_digest"
        ],
        "release_digest": release["release_identity"]["content_digest"],
    }
    for field, expected in expected_bundle_links.items():
        if bundle_identity.get(field) != expected:
            raise TieredFamilyError(f"portable bundle {field} does not match")
    pack_bytes: dict[str, bytes] = {}
    for descriptor in pack_index["packs"]:
        key = Path(descriptor["object_key"])
        content = (source / key).read_bytes()
        if _sha256_uri(content) != descriptor["pack_digest"]:
            raise TieredFamilyError("portable bundle pack digest does not match")
        pack_bytes[descriptor["pack_digest"]] = content
    validate_pack_index(pack_index, pack_bytes)
    added = 0
    reused = 0
    for descriptor in corpus["objects"]:
        key = Path(_object_key(descriptor["content_digest"]))
        content = (source / key).read_bytes()
        _validate_object_content(descriptor, content)
        destination = target / key
        if destination.is_file():
            if destination.read_bytes() != content:
                raise TieredFamilyError("import target has a corrupt CAS object")
            reused += 1
        else:
            _write_if_changed(destination, content)
            added += 1
    release_root = target / _release_relative_root(distribution)
    for relative in (
        PACK_INDEX_ARTIFACT_PATH,
        OWNER_RELEASE_ARTIFACT_PATH,
    ):
        _write_if_changed(
            release_root / relative,
            (source / relative).read_bytes(),
        )
    for relative in (
        CORPUS_MANIFEST_RELATIVE_PATH.name,
        MANIFEST_RELATIVE_PATH.name,
        HOT_PROFILE_RELATIVE_PATH.name,
        LOCATOR_MANIFEST_RELATIVE_PATH.name,
    ):
        source_path = {
            CORPUS_MANIFEST_RELATIVE_PATH.name: source / CORPUS_MANIFEST_RELATIVE_PATH,
            MANIFEST_RELATIVE_PATH.name: source / MANIFEST_RELATIVE_PATH,
            HOT_PROFILE_RELATIVE_PATH.name: source / HOT_PROFILE_RELATIVE_PATH,
            LOCATOR_MANIFEST_RELATIVE_PATH.name: source / LOCATOR_MANIFEST_RELATIVE_PATH,
        }[relative]
        _write_if_changed(release_root / relative, source_path.read_bytes())
    for source_path in (source / "packs").glob("sha256/*/*.pack"):
        relative = source_path.relative_to(source)
        _write_if_changed(target / relative, source_path.read_bytes())
    return {"objects_added": added, "objects_reused": reused}


def copy_bundle_to_empty_destination(source: Path, destination: Path) -> None:
    if destination.exists():
        if any(destination.iterdir()):
            raise TieredFamilyError("destination must be empty")
    else:
        destination.mkdir(parents=True)
    for path in source.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
