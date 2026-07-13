from __future__ import annotations

import copy
import hashlib
from pathlib import PurePosixPath
from typing import Any, Iterable, Sequence

from .identity import qualified_id
from .structure import resolve_markdown_target


def artifact_entries(records: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for record in records:
        identity = record["identity"]
        anchors = record.get("refs", {}).get("anchor_refs", [])
        artifact_anchor_ids = [
            item["id"]
            for item in anchors
            if isinstance(item, dict) and item.get("anchor_kind") == "artifact"
        ]
        entries.append(
            {
                "id": str(identity["id"]),
                "version_id": str(identity["version_id"]),
                "artifact_kind": str(record.get("artifact_kind") or "unknown"),
                "surface_state": str(record.get("surface_state") or "authored_source"),
                "anchor_id": artifact_anchor_ids[0],
                "path": str(identity["path"]),
                "lineage_path": str(identity["lineage_path"]),
                "content_hash": str(identity["content_hash"]),
                "mime": str(identity["mime"]),
                "provenance_ref": "deterministic",
                "temporal_ref": "current",
                "trust_ref": "deterministic",
            }
        )
    return entries


def anchor_entries(records: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for record in records:
        identity = record["identity"]
        refs = record.get("refs")
        anchors = refs.get("anchor_refs") if isinstance(refs, dict) else []
        outbound = refs.get("outbound_refs") if isinstance(refs, dict) else []
        outbound_by_anchor: dict[str, list[dict[str, Any]]] = {}
        for reference in outbound if isinstance(outbound, list) else []:
            if not isinstance(reference, dict):
                continue
            source_anchor_id = str(reference.get("source_anchor_id") or "")
            outbound_by_anchor.setdefault(source_anchor_id, []).append(
                {
                    "relation_kind": str(reference.get("relation_kind") or "references"),
                    "source_context": str(reference.get("source_context") or "$artifact"),
                    "target_ref": str(reference.get("target_ref") or ""),
                    "evidence_class": str(reference.get("evidence_class") or "deterministic"),
                }
            )
        for anchor in anchors if isinstance(anchors, list) else []:
            if not isinstance(anchor, dict):
                continue
            entry = copy.deepcopy(anchor)
            parser = entry.pop("parser")
            entry["parser_ref"] = f"{parser['name']}@{parser['version']}"
            entry.update(
                {
                    "source_record_id": str(identity["id"]),
                    "outbound_refs": sorted(
                        outbound_by_anchor.get(str(entry["id"]), []),
                        key=lambda item: (item["relation_kind"], item["target_ref"]),
                    ),
                    "evidence_class": "deterministic",
                    "provenance_ref": "deterministic",
                    "temporal_ref": "current",
                    "trust_ref": "deterministic",
                }
            )
            entries.append(entry)
    return sorted(
        entries,
        key=lambda item: (
            item["source_record_id"],
            item["locator"]["start_line"],
            item["id"],
        ),
    )


def _file_entity_kind(record: dict[str, Any]) -> str:
    mechanics = str(record.get("mechanics_role") or "none")
    command = str(record.get("command_role") or "none")
    artifact = str(record.get("artifact_kind") or "unknown")
    document = str(record.get("document_role") or "none")
    if command != "none":
        return "command"
    if artifact == "schema":
        return "contract"
    if document == "decision":
        return "decision"
    if document == "agents":
        return "agent_route"
    if artifact == "manifest":
        return "manifest"
    if record.get("surface_state") == "generated_readmodel":
        return "readmodel"
    if document != "none":
        return "document"
    if record.get("code_role") != "none":
        return "code"
    if artifact == "owner_metadata":
        return "owner_surface"
    if mechanics != "none":
        return "mechanics_surface"
    return "artifact"


def _entity(
    *,
    entity_id: str,
    entity_kind: str,
    label: str,
    source_record_ids: Iterable[str],
    anchor_ids: Iterable[str],
    semantic_key: str,
    source_digest: str,
) -> dict[str, Any]:
    sources = sorted(set(source_record_ids))
    anchors = sorted(set(anchor_ids))
    return {
        "id": entity_id,
        "entity_kind": entity_kind,
        "label": label,
        "semantic_key": semantic_key,
        "source_record_ids": sources,
        "anchor_ids": anchors,
        "source_digest": source_digest,
        "provenance_ref": "deterministic",
        "temporal_ref": "current",
        "trust_ref": "deterministic",
    }


def _aggregate_source_digest(
    records_by_id: dict[str, dict[str, Any]],
    source_ids: Iterable[str],
) -> str:
    material = "|".join(
        f"{source_id}:{records_by_id[source_id]['identity']['content_hash']}"
        for source_id in sorted(set(source_ids))
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def entity_entries(
    repo: str,
    records: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    mechanic_sources: dict[str, dict[str, set[str] | str]] = {}
    records_by_id = {
        str(record["identity"]["id"]): record
        for record in records
    }
    artifact_anchors_by_source: dict[str, list[str]] = {}
    directory_descendants: dict[str, set[str]] = {".": set()}
    directory_direct_sources: dict[str, set[str]] = {".": set()}
    for record in records:
        identity = record["identity"]
        source_id = str(identity["id"])
        refs = record.get("refs") if isinstance(record.get("refs"), dict) else {}
        anchors = refs.get("anchor_refs") if isinstance(refs, dict) else []
        artifact_anchor_ids = [
            item["id"]
            for item in anchors if isinstance(item, dict) and item.get("anchor_kind") == "artifact"
        ]
        artifact_anchors_by_source[source_id] = artifact_anchor_ids
        path = PurePosixPath(str(identity["path"]))
        parent = path.parent.as_posix()
        directory_direct_sources.setdefault(parent, set()).add(source_id)
        directory_descendants["."].add(source_id)
        current = path.parent
        while current.as_posix() != ".":
            current_path = current.as_posix()
            directory_descendants.setdefault(current_path, set()).add(source_id)
            directory_direct_sources.setdefault(current_path, set())
            current = current.parent
        semantic_key = str(identity["lineage_path"])
        file_entity_id = qualified_id(repo, "entity", f"surface:{identity['logical_id']}")
        file_entity_kind = _file_entity_kind(record)
        if file_entity_kind in {
            "agent_route",
            "command",
            "contract",
            "decision",
            "document",
            "manifest",
            "owner_surface",
            "readmodel",
        }:
            entries[file_entity_id] = _entity(
                entity_id=file_entity_id,
                entity_kind=file_entity_kind,
                label=str(identity["path"]),
                source_record_ids=[source_id],
                anchor_ids=artifact_anchor_ids,
                semantic_key=semantic_key,
                source_digest=str(identity["content_hash"]),
            )

        for anchor in anchors if isinstance(anchors, list) else []:
            if not isinstance(anchor, dict):
                continue
            anchor_kind = str(anchor.get("anchor_kind") or "")
            entity_kind = ""
            if anchor_kind == "python_symbol":
                symbol_kind = str(anchor.get("symbol_kind") or "symbol")
                entity_kind = f"python_{symbol_kind}"
            elif anchor_kind == "json_pointer" and anchor.get("symbol_kind") == "schema_definition":
                entity_kind = "schema_definition"
            if not entity_kind:
                continue
            semantic_key = str(anchor.get("semantic_key") or anchor["id"])
            entity_id = qualified_id(repo, "entity", f"{source_id}:{entity_kind}:{semantic_key}")
            entries[entity_id] = _entity(
                entity_id=entity_id,
                entity_kind=entity_kind,
                label=str(anchor.get("label") or semantic_key),
                source_record_ids=[source_id],
                anchor_ids=[str(anchor["id"])],
                semantic_key=semantic_key,
                source_digest=str(identity["content_hash"]),
            )

        parts = path.parts
        if len(parts) >= 2 and parts[0] == "mechanics":
            mechanic_path = "/".join(parts[:2])
            mechanic_sources.setdefault(
                mechanic_path,
                {"kind": "mechanic_package", "label": parts[1], "sources": set(), "anchors": set()},
            )
            mechanic_sources[mechanic_path]["sources"].add(source_id)  # type: ignore[union-attr]
            mechanic_sources[mechanic_path]["anchors"].update(artifact_anchor_ids)  # type: ignore[union-attr]
            if len(parts) >= 4 and parts[2] == "parts":
                part_path = "/".join(parts[:4])
                mechanic_sources.setdefault(
                    part_path,
                    {"kind": "mechanic_part", "label": parts[3], "sources": set(), "anchors": set()},
                )
                mechanic_sources[part_path]["sources"].add(source_id)  # type: ignore[union-attr]
                mechanic_sources[part_path]["anchors"].update(artifact_anchor_ids)  # type: ignore[union-attr]

    for semantic_key, item in mechanic_sources.items():
        entity_id = qualified_id(repo, "entity", semantic_key)
        sources = item["sources"]
        anchors = item["anchors"]
        entries[entity_id] = _entity(
            entity_id=entity_id,
            entity_kind=str(item["kind"]),
            label=str(item["label"]),
            source_record_ids=sources,  # type: ignore[arg-type]
            anchor_ids=anchors,  # type: ignore[arg-type]
            semantic_key=semantic_key,
            source_digest=_aggregate_source_digest(records_by_id, sources),  # type: ignore[arg-type]
        )

    for directory_path, descendants in sorted(
        directory_descendants.items(),
        key=lambda item: (len(PurePosixPath(item[0]).parts), item[0]),
    ):
        direct_sources = directory_direct_sources.get(directory_path, set())
        evidence_sources = sorted(direct_sources or descendants)[:1]
        if not evidence_sources:
            continue
        semantic_key = f"directory:{directory_path}"
        entity_id = qualified_id(repo, "entity", semantic_key)
        entries[entity_id] = _entity(
            entity_id=entity_id,
            entity_kind="repository" if directory_path == "." else "directory",
            label=repo if directory_path == "." else PurePosixPath(directory_path).name,
            source_record_ids=evidence_sources,
            anchor_ids=(
                anchor_id
                for source_id in evidence_sources
                for anchor_id in artifact_anchors_by_source[source_id]
            ),
            semantic_key=semantic_key,
            source_digest=_aggregate_source_digest(records_by_id, evidence_sources),
        )
    return sorted(entries.values(), key=lambda item: (item["entity_kind"], item["id"]))


def _assertion(
    repo: str,
    *,
    assertion_kind: str,
    subject_id: str,
    predicate: str,
    object_kind: str,
    object_value: str,
    source_record_ids: Iterable[str],
    evidence_anchor_ids: Iterable[str],
    evidence_class: str,
) -> dict[str, Any]:
    sources = sorted(set(source_record_ids))
    evidence = sorted(set(evidence_anchor_ids))
    assertion_id = qualified_id(
        repo,
        "assertion",
        f"{subject_id}:{predicate}:{object_kind}:{object_value}",
    )
    return {
        "id": assertion_id,
        "assertion_kind": assertion_kind,
        "subject_id": subject_id,
        "predicate": predicate,
        "object": {"kind": object_kind, "value": object_value},
        "source_record_ids": sources,
        "evidence_anchor_ids": evidence,
        "evidence_class": evidence_class,
        "confidence": 1.0 if evidence_class == "deterministic" else 0.75,
        "quality_state": "accepted",
        "temporal_ref": "current",
        "provenance_ref": evidence_class,
        "trust_ref": evidence_class,
    }


def assertion_entries(
    repo: str,
    records: Sequence[dict[str, Any]],
    *,
    artifacts: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    artifacts_by_id = {str(entry["id"]): entry for entry in artifacts}
    entries: dict[str, dict[str, Any]] = {}
    for record in records:
        identity = record["identity"]
        source_id = str(identity["id"])
        artifact = artifacts_by_id[source_id]
        evidence = [str(artifact["anchor_id"])]
        facts = [
            (
                "classification",
                "classified_as",
                str(record["classification"]["primary_kind"]),
                "deterministic",
            )
        ]
        for field, predicate in (
            ("document_role", "document_role"),
            ("mechanics_role", "mechanics_role"),
            ("command_role", "command_role"),
        ):
            value = str(record.get(field) or "none")
            if value != "none":
                facts.append(("role", predicate, value, "deterministic"))
        abi = record.get("abi") if isinstance(record.get("abi"), dict) else {}
        for field, predicate in (
            ("schema_version", "declares_schema_version"),
            ("contract_version", "declares_contract_version"),
        ):
            value = str(abi.get(field) or "none")
            if value != "none":
                facts.append(("contract", predicate, value, "declared"))
        for assertion_kind, predicate, value, evidence_class in facts:
            entry = _assertion(
                repo,
                assertion_kind=assertion_kind,
                subject_id=source_id,
                predicate=predicate,
                object_kind="literal",
                object_value=value,
                source_record_ids=[source_id],
                evidence_anchor_ids=evidence,
                evidence_class=evidence_class,
            )
            entries[entry["id"]] = entry
    return sorted(
        entries.values(),
        key=lambda item: (item["assertion_kind"], item["subject_id"], item["predicate"]),
    )


def _relation(
    repo: str,
    *,
    relation_kind: str,
    from_id: str,
    to_id: str,
    evidence_anchor_ids: Iterable[str],
    evidence_class: str = "deterministic",
) -> dict[str, Any]:
    evidence = sorted(set(evidence_anchor_ids))
    relation_id = qualified_id(
        repo,
        "relation",
        f"{from_id}:{relation_kind}:{to_id}:{'|'.join(evidence)}",
    )
    return {
        "id": relation_id,
        "relation_kind": relation_kind,
        "from_id": from_id,
        "to_id": to_id,
        "evidence_anchor_ids": evidence,
        "evidence_class": evidence_class,
        "confidence": 1.0 if evidence_class == "deterministic" else 0.75,
        "temporal_ref": "current",
        "provenance_ref": evidence_class,
        "trust_ref": evidence_class,
    }


def relation_entries(
    repo: str,
    records: Sequence[dict[str, Any]],
    *,
    artifacts: Sequence[dict[str, Any]],
    anchors: Sequence[dict[str, Any]],
    entities: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    relations: dict[str, dict[str, Any]] = {}
    artifact_by_source = {entry["id"]: entry for entry in artifacts}
    anchor_by_id = {entry["id"]: entry for entry in anchors}
    artifact_anchor_by_path = {
        artifact["path"]: artifact["anchor_id"] for artifact in artifacts
    }
    heading_by_path_fragment = {
        (
            artifact_by_source[entry["source_record_id"]]["path"],
            entry["locator"]["fragment"],
        ): entry["id"]
        for entry in anchors
        if entry["anchor_kind"] == "markdown_heading" and entry["locator"]["fragment"]
    }
    file_entity_by_source = {
        entry["source_record_ids"][0]: entry
        for entry in entities
        if len(entry["source_record_ids"]) == 1
        and entry["semantic_key"]
        == next(
            (
                record["identity"]["lineage_path"]
                for record in records
                if record["identity"]["id"] == entry["source_record_ids"][0]
            ),
            "",
        )
    }
    entity_by_anchor: dict[str, dict[str, Any]] = {}
    python_entities_by_name: dict[str, list[dict[str, Any]]] = {}
    for entity in entities:
        for anchor_id in entity["anchor_ids"]:
            entity_by_anchor[anchor_id] = entity
        if entity["entity_kind"].startswith("python_"):
            key = entity["semantic_key"].split(":", 2)[-1]
            qualified_name = key.rsplit(":", 1)[-1]
            python_entities_by_name.setdefault(qualified_name, []).append(entity)
            python_entities_by_name.setdefault(qualified_name.rsplit(".", 1)[-1], []).append(entity)

    for anchor in anchors:
        source_id = anchor["source_record_id"]
        artifact = artifact_by_source[source_id]
        entity = entity_by_anchor.get(anchor["id"])
        if entity and anchor["anchor_kind"] != "artifact":
            relation = _relation(
                repo,
                relation_kind="defines",
                from_id=artifact["id"],
                to_id=entity["id"],
                evidence_anchor_ids=[anchor["id"]],
            )
            relations[relation["id"]] = relation

    for source_id, entity in file_entity_by_source.items():
        artifact = artifact_by_source[source_id]
        relation = _relation(
            repo,
            relation_kind="represents",
            from_id=artifact["id"],
            to_id=entity["id"],
            evidence_anchor_ids=[artifact["anchor_id"]],
        )
        relations[relation["id"]] = relation

    mechanic_entities = {
        entity["semantic_key"]: entity
        for entity in entities
        if entity["entity_kind"] in {"mechanic_package", "mechanic_part"}
    }
    for key, part in mechanic_entities.items():
        if part["entity_kind"] != "mechanic_part":
            continue
        package_key = "/".join(key.split("/")[:2])
        package = mechanic_entities.get(package_key)
        if package:
            relation = _relation(
                repo,
                relation_kind="contains",
                from_id=package["id"],
                to_id=part["id"],
                evidence_anchor_ids=part["anchor_ids"][:1],
            )
            relations[relation["id"]] = relation

    directory_entities = {
        entity["semantic_key"].removeprefix("directory:"): entity
        for entity in entities
        if entity["entity_kind"] in {"directory", "repository"}
        and entity["semantic_key"].startswith("directory:")
    }
    for directory_path, directory in directory_entities.items():
        if directory_path != ".":
            parent_path = PurePosixPath(directory_path).parent.as_posix()
            parent = directory_entities.get(parent_path)
            if parent:
                relation = _relation(
                    repo,
                    relation_kind="contains",
                    from_id=parent["id"],
                    to_id=directory["id"],
                    evidence_anchor_ids=directory["anchor_ids"][:1],
                )
                relations[relation["id"]] = relation
    for artifact in artifacts:
        parent_path = PurePosixPath(str(artifact["path"])).parent.as_posix()
        parent = directory_entities.get(parent_path)
        if parent:
            relation = _relation(
                repo,
                relation_kind="contains",
                from_id=parent["id"],
                to_id=artifact["id"],
                evidence_anchor_ids=[artifact["anchor_id"]],
            )
            relations[relation["id"]] = relation

    records_by_source_id = {
        str(record["identity"]["id"]): record
        for record in records
    }
    for anchor in anchors:
        source_id = str(anchor["source_record_id"])
        identity = records_by_source_id[source_id]["identity"]
        source_entity = file_entity_by_source.get(source_id)
        for reference in anchor.get("outbound_refs", []):
            target_ref = str(reference.get("target_ref") or "")
            target_id = ""
            if target_ref.startswith("python:"):
                matches = python_entities_by_name.get(target_ref.removeprefix("python:"), [])
                unique = {item["id"]: item for item in matches}
                if len(unique) == 1:
                    target_id = next(iter(unique))
            else:
                resolved = resolve_markdown_target(str(identity["path"]), target_ref)
                if resolved:
                    target_path, fragment = resolved
                    target_id = (
                        heading_by_path_fragment.get((target_path, fragment), "")
                        if fragment
                        else (
                            artifact_anchor_by_path.get(target_path, "")
                            or str(directory_entities.get(target_path, {}).get("id") or "")
                        )
                    )
            evidence_anchor_id = str(anchor["id"])
            if not target_id or evidence_anchor_id not in anchor_by_id:
                continue
            source_node = entity_by_anchor.get(evidence_anchor_id) or source_entity
            relation = _relation(
                repo,
                relation_kind=str(reference.get("relation_kind") or "references"),
                from_id=source_node["id"] if source_node else artifact_by_source[source_id]["id"],
                to_id=target_id,
                evidence_anchor_ids=[evidence_anchor_id],
                evidence_class=str(reference.get("evidence_class") or "deterministic"),
            )
            relations[relation["id"]] = relation
    return sorted(relations.values(), key=lambda item: (item["relation_kind"], item["from_id"], item["to_id"]))
