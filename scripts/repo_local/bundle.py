from __future__ import annotations

import copy
import hashlib
import json
import os
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any, Mapping


ZERO_DIGEST = "0" * 64
ENCODER = json.JSONEncoder(
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
)


def _json_chunks(payload: object) -> Iterator[bytes]:
    for chunk in ENCODER.iterencode(payload):
        yield chunk.encode("utf-8")
    yield b"\n"


def _document_chunks(documents: Iterable[Mapping[str, Any]]) -> Iterator[bytes]:
    for document in documents:
        yield from _json_chunks(document)


def _digest_chunks(chunks: Iterable[bytes]) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    for chunk in chunks:
        digest.update(chunk)
        size += len(chunk)
    return digest.hexdigest(), size


def _file_digest(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def _write_atomic(path: Path, chunks: Iterable[bytes]) -> tuple[str, int]:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    digest = hashlib.sha256()
    size = 0
    try:
        with temporary.open("wb") as handle:
            for chunk in chunks:
                handle.write(chunk)
                digest.update(chunk)
                size += len(chunk)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return digest.hexdigest(), size


def _file_metadata(
    *,
    path: str,
    media_type: str,
    digest: str,
    size: int,
    record_count: int,
) -> dict[str, Any]:
    return {
        "path": path,
        "media_type": media_type,
        "sha256": digest,
        "bytes": size,
        "record_count": record_count,
    }


def build_retrieval_bundle_manifest(
    plan: Mapping[str, Any],
    *,
    files: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    federation = plan["federation"]
    payload: dict[str, Any] = {
        "schema_version": "aoa-repo-local-kag-retrieval-bundle-v1",
        "bundle_identity": {
            "local_id": "bundle:os-abyss:repo-self-retrieval",
            "content_digest": ZERO_DIGEST,
        },
        "projection_identity": copy.deepcopy(plan["projection_identity"]),
        "federation_identity": copy.deepcopy(federation["federation_identity"]),
        "canonical_inputs": copy.deepcopy(plan["canonical_inputs"]),
        "projection_lanes": copy.deepcopy(plan["projection_lanes"]),
        "retrieval_profile": copy.deepcopy(plan["retrieval_profile"]),
        "embedding_profile": copy.deepcopy(plan["embedding_profile"]),
        "summary": copy.deepcopy(plan["summary"]),
        "federation_summary": copy.deepcopy(federation["summary"]),
        "files": {
            key: copy.deepcopy(dict(metadata)) for key, metadata in sorted(files.items())
        },
    }
    material = copy.deepcopy(payload)
    encoded = json.dumps(
        material,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    payload["bundle_identity"]["content_digest"] = hashlib.sha256(encoded).hexdigest()
    return payload


def _expected_file_metadata(plan: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    federation = plan["federation"]
    records = {
        "owners": federation["owners"],
        "nodes": federation["nodes"],
        "relations": federation["relations"],
        "external_references": federation["external_references"],
        "documents": plan["documents"],
    }
    metadata: dict[str, dict[str, Any]] = {}
    for key, items in records.items():
        digest, size = _digest_chunks(_document_chunks(items))
        metadata[key] = _file_metadata(
            path=f"{key}.jsonl",
            media_type="application/x-ndjson",
            digest=digest,
            size=size,
            record_count=len(items),
        )
    return metadata


def write_retrieval_bundle(
    plan: Mapping[str, Any],
    bundle_dir: Path,
) -> dict[str, Any]:
    bundle_dir = bundle_dir.resolve()
    federation = plan["federation"]
    records = {
        "owners": federation["owners"],
        "nodes": federation["nodes"],
        "relations": federation["relations"],
        "external_references": federation["external_references"],
        "documents": plan["documents"],
    }
    files: dict[str, dict[str, Any]] = {}
    for key, items in records.items():
        path = f"{key}.jsonl"
        digest, size = _write_atomic(
            bundle_dir / path,
            _document_chunks(items),
        )
        files[key] = _file_metadata(
            path=path,
            media_type="application/x-ndjson",
            digest=digest,
            size=size,
            record_count=len(items),
        )
    manifest = build_retrieval_bundle_manifest(plan, files=files)
    rendered = (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    _write_atomic(bundle_dir / "manifest.json", (rendered,))
    return manifest


def retrieval_bundle_matches(plan: Mapping[str, Any], bundle_dir: Path) -> bool:
    bundle_dir = bundle_dir.resolve()
    expected_files = _expected_file_metadata(plan)
    for metadata in expected_files.values():
        path = bundle_dir / str(metadata["path"])
        if not path.is_file():
            return False
        digest, size = _file_digest(path)
        if digest != metadata["sha256"] or size != metadata["bytes"]:
            return False
    manifest_path = bundle_dir / "manifest.json"
    if not manifest_path.is_file():
        return False
    try:
        actual_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    expected_manifest = build_retrieval_bundle_manifest(
        plan,
        files=expected_files,
    )
    expected_names = {"manifest.json"} | {
        str(metadata["path"]) for metadata in expected_files.values()
    }
    actual_names = {path.name for path in bundle_dir.iterdir() if path.is_file()}
    return actual_manifest == expected_manifest and actual_names == expected_names
