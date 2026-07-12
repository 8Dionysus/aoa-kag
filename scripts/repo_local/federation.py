from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter, defaultdict, deque
from typing import Any, Mapping, Sequence
from urllib.parse import unquote, urlsplit

try:
    from scripts.validators.repo_local_kag_index import (
        validate_repo_local_kag_repository_index_family,
    )
except ImportError:  # pragma: no cover - direct script execution
    from validators.repo_local_kag_index import (  # type: ignore
        validate_repo_local_kag_repository_index_family,
    )

from .identity import qualified_id
from .query import RepoKagQuery, tokenize


ZERO_DIGEST = "0" * 64
NODE_CLASSES = ("artifact", "anchor", "entity", "event", "assertion")


def _digest(payload: dict[str, Any]) -> str:
    material = copy.deepcopy(payload)
    material["federation_identity"]["content_digest"] = ZERO_DIGEST
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class RepoKagFederation:
    def __init__(
        self,
        bundles: Mapping[str, tuple[dict[str, Any], dict[str, dict[str, Any]]]],
    ) -> None:
        if not bundles:
            raise ValueError("federation requires at least one owner bundle")
        self._bundles: dict[str, tuple[dict[str, Any], dict[str, dict[str, Any]]]] = {}
        self._queries: dict[str, RepoKagQuery] = {}
        self._node_owner: dict[str, str] = {}
        self._node_handles: dict[str, dict[str, Any]] = {}
        self._artifacts_by_repo_path: dict[tuple[str, str], dict[str, Any]] = {}
        self._headings_by_repo_path_fragment: dict[tuple[str, str, str], dict[str, Any]] = {}
        self._root_entities: dict[str, dict[str, Any]] = {}
        self._file_entities: dict[tuple[str, str], dict[str, Any]] = {}
        self._entity_by_anchor: dict[str, dict[str, Any]] = {}

        for owner, (source, family) in sorted(bundles.items()):
            repo = str(source.get("repo", {}).get("name") or "")
            if owner != repo:
                raise ValueError(f"owner key {owner!r} must match source repo {repo!r}")
            validate_repo_local_kag_repository_index_family(
                family,
                source_payload=source,
                label=f"{owner} federation family",
            )
            self._bundles[owner] = (source, family)
            self._queries[owner] = RepoKagQuery(source, family)
            self._register_owner(owner, source, family)

        self._local_relations = self._collect_local_relations()
        (
            self._cross_repo_relations,
            self._unresolved_references,
            self._external_references,
        ) = self._resolve_cross_repo_refs()
        self._relations = (*self._local_relations, *self._cross_repo_relations)
        self._adjacency: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
        for relation in self._relations:
            self._adjacency[str(relation["from_id"])].append((str(relation["to_id"]), relation))
            self._adjacency[str(relation["to_id"])].append((str(relation["from_id"]), relation))
        for neighbors in self._adjacency.values():
            neighbors.sort(key=lambda item: (item[0], item[1]["id"]))
        self._projection = self._build_projection()

    def _register_owner(
        self,
        owner: str,
        source: dict[str, Any],
        family: dict[str, dict[str, Any]],
    ) -> None:
        source_records = {
            str(record["identity"]["id"]): record
            for record in source["records"]
        }
        for node_class in NODE_CLASSES:
            for entry in family[node_class]["entries"]:
                node_id = str(entry["id"])
                previous_owner = self._node_owner.get(node_id)
                if previous_owner is not None:
                    raise ValueError(
                        f"federation node id collision: {node_id} ({previous_owner}, {owner})"
                    )
                source_ids = self._entry_source_ids(node_class, entry)
                anchor_ids = self._entry_anchor_ids(node_class, entry)
                access_scope = self._queries[owner].source_access(source_ids)
                kind = str(entry[f"{node_class}_kind"])
                self._node_owner[node_id] = owner
                self._node_handles[node_id] = {
                    "id": node_id,
                    "repo": owner,
                    "namespace": source["repo"]["namespace"],
                    "node_class": node_class,
                    "kind": kind,
                    "source_record_ids": list(source_ids),
                    "anchor_ids": list(anchor_ids),
                    "access_scope": access_scope,
                }
                if node_class == "artifact":
                    source_record = source_records[node_id]
                    current_path = str(entry["path"])
                    lineage_path = str(source_record["identity"]["lineage_path"])
                    self._artifacts_by_repo_path[(owner, current_path)] = entry
                    self._artifacts_by_repo_path.setdefault((owner, lineage_path), entry)
                elif node_class == "anchor":
                    source_record = source_records[str(entry["source_record_id"])]
                    path = str(source_record["identity"]["path"])
                    lineage_path = str(source_record["identity"]["lineage_path"])
                    fragment = str(entry["locator"]["fragment"])
                    if entry["anchor_kind"] == "markdown_heading" and fragment:
                        self._headings_by_repo_path_fragment[(owner, path, fragment)] = entry
                        self._headings_by_repo_path_fragment.setdefault(
                            (owner, lineage_path, fragment),
                            entry,
                        )
                elif node_class == "entity":
                    for anchor_id in entry["anchor_ids"]:
                        self._entity_by_anchor[str(anchor_id)] = entry
                    if entry["entity_kind"] == "repository":
                        self._root_entities[owner] = entry
                    if len(entry["source_record_ids"]) == 1:
                        source_id = str(entry["source_record_ids"][0])
                        lineage_path = str(source_records[source_id]["identity"]["lineage_path"])
                        if entry["semantic_key"] == lineage_path:
                            path = str(source_records[source_id]["identity"]["path"])
                            self._file_entities[(owner, path)] = entry

    @staticmethod
    def _entry_source_ids(node_class: str, entry: dict[str, Any]) -> tuple[str, ...]:
        if node_class == "artifact":
            return (str(entry["id"]),)
        if node_class == "anchor":
            return (str(entry["source_record_id"]),)
        return tuple(str(item) for item in entry["source_record_ids"])

    @staticmethod
    def _entry_anchor_ids(node_class: str, entry: dict[str, Any]) -> tuple[str, ...]:
        if node_class == "artifact":
            return (str(entry["anchor_id"]),)
        if node_class == "anchor":
            return (str(entry["id"]),)
        if node_class == "assertion":
            return tuple(str(item) for item in entry["evidence_anchor_ids"])
        return tuple(str(item) for item in entry["anchor_ids"])

    def _collect_local_relations(self) -> tuple[dict[str, Any], ...]:
        relations: list[dict[str, Any]] = []
        seen: set[str] = set()
        for owner, (_, family) in sorted(self._bundles.items()):
            for entry in family["relation"]["entries"]:
                relation_id = str(entry["id"])
                if relation_id in seen:
                    raise ValueError(f"federation relation id collision: {relation_id}")
                seen.add(relation_id)
                target_owner = self._node_owner[str(entry["to_id"])]
                relations.append(
                    {
                        **copy.deepcopy(entry),
                        "source_repo": owner,
                        "target_repo": target_owner,
                        "scope": "local",
                    }
                )
        return tuple(sorted(relations, key=lambda item: item["id"]))

    def _target_for_ref(self, source_repo: str, target_ref: str) -> tuple[str, str, str]:
        if target_ref.startswith("aoa:"):
            if target_ref in self._node_owner:
                return target_ref, self._node_owner[target_ref], "resolved"
            return "", "", "unresolved-qualified-id"

        parsed = urlsplit(target_ref)
        if parsed.scheme not in {"http", "https", "repo"}:
            return "", "", "out-of-scope"
        if parsed.scheme == "repo":
            target_repo = parsed.netloc
            tail = parsed.path.lstrip("/")
        elif parsed.netloc.casefold() in {"github.com", "www.github.com"}:
            parts = [unquote(part) for part in parsed.path.split("/") if part]
            if len(parts) < 2:
                return "", "", "out-of-scope"
            target_repo = parts[1]
            tail_parts = parts[2:]
            if tail_parts and tail_parts[0] not in {"blob", "tree"}:
                return "", target_repo, "github-object"
            if tail_parts:
                tail_parts = tail_parts[1:]
            tail = "/".join(tail_parts)
        else:
            return "", "", "external-web"

        if target_repo not in self._bundles:
            return "", target_repo, "external-owner"
        if target_repo == source_repo:
            return "", target_repo, "owner-local-absolute"
        if not tail:
            root = self._root_entities.get(target_repo)
            return (
                (str(root["id"]), target_repo, "resolved")
                if root is not None
                else ("", target_repo, "unresolved-root")
            )

        target_path = ""
        tail_parts = tail.split("/")
        for offset in range(len(tail_parts)):
            candidate = "/".join(tail_parts[offset:])
            if (target_repo, candidate) in self._artifacts_by_repo_path:
                target_path = candidate
                break
        if not target_path:
            return "", target_repo, "unresolved-path"
        fragment = unquote(parsed.fragment)
        if fragment:
            heading = self._headings_by_repo_path_fragment.get(
                (target_repo, target_path, fragment)
            )
            return (
                (str(heading["id"]), target_repo, "resolved")
                if heading is not None
                else ("", target_repo, "unresolved-fragment")
            )
        artifact = self._artifacts_by_repo_path[(target_repo, target_path)]
        return str(artifact["anchor_id"]), target_repo, "resolved"

    def _resolve_cross_repo_refs(
        self,
    ) -> tuple[
        tuple[dict[str, Any], ...],
        tuple[dict[str, Any], ...],
        tuple[dict[str, Any], ...],
    ]:
        relations: dict[str, dict[str, Any]] = {}
        unresolved: list[dict[str, Any]] = []
        external: list[dict[str, Any]] = []
        for owner, (source, family) in sorted(self._bundles.items()):
            source_records = {
                str(record["identity"]["id"]): record
                for record in source["records"]
            }
            for anchor in family["anchor"]["entries"]:
                source_id = str(anchor["source_record_id"])
                source_path = str(source_records[source_id]["identity"]["path"])
                source_node = self._entity_by_anchor.get(str(anchor["id"]))
                if source_node is None:
                    source_node = self._file_entities.get((owner, source_path))
                from_id = str(source_node["id"]) if source_node else source_id
                for reference in anchor.get("outbound_refs", []):
                    target_ref = str(reference["target_ref"])
                    target_id, target_owner, state = self._target_for_ref(owner, target_ref)
                    if state in {"external-web", "external-owner", "github-object"}:
                        external_ref = {
                            "source_repo": owner,
                            "source_anchor_id": str(anchor["id"]),
                            "target_ref": target_ref,
                            "reference_kind": state,
                        }
                        if target_owner:
                            external_ref["target_repo"] = target_owner
                        external.append(external_ref)
                        continue
                    if state in {"out-of-scope", "owner-local-absolute"}:
                        continue
                    if state != "resolved":
                        unresolved.append(
                            {
                                "source_repo": owner,
                                "source_anchor_id": str(anchor["id"]),
                                "target_ref": target_ref,
                                "resolution_state": state,
                            }
                        )
                        continue
                    relation_kind = str(reference["relation_kind"])
                    relation_id = qualified_id(
                        owner,
                        "relation",
                        f"federated:{from_id}:{relation_kind}:{target_id}:{anchor['id']}",
                    )
                    relation = {
                        "id": relation_id,
                        "relation_kind": relation_kind,
                        "from_id": from_id,
                        "to_id": target_id,
                        "source_repo": owner,
                        "target_repo": target_owner,
                        "scope": "federated",
                        "evidence_anchor_ids": [str(anchor["id"])],
                        "evidence_class": str(reference["evidence_class"]),
                        "confidence": 1.0,
                        "temporal_ref": "current",
                        "provenance_ref": "deterministic",
                        "trust_ref": "deterministic",
                    }
                    relations[relation_id] = relation
        return (
            tuple(sorted(relations.values(), key=lambda item: item["id"])),
            tuple(
                sorted(
                    unresolved,
                    key=lambda item: (
                        item["source_repo"],
                        item["source_anchor_id"],
                        item["target_ref"],
                    ),
                )
            ),
            tuple(
                sorted(
                    external,
                    key=lambda item: (
                        item["source_repo"],
                        item["source_anchor_id"],
                        item["target_ref"],
                    ),
                )
            ),
        )

    def _build_projection(self) -> dict[str, Any]:
        owners: list[dict[str, Any]] = []
        for owner, (source, family) in sorted(self._bundles.items()):
            owners.append(
                {
                    "repo": copy.deepcopy(source["repo"]),
                    "source_index_digest": source["index_identity"]["content_digest"],
                    "family_digests": {
                        kind: family[kind]["index_identity"]["content_digest"]
                        for kind in sorted(family)
                    },
                    "node_counts": {
                        kind: len(family[kind]["entries"])
                        for kind in NODE_CLASSES
                    },
                    "relation_count": len(family["relation"]["entries"]),
                }
            )
        relation_counts = Counter(relation["relation_kind"] for relation in self._relations)
        payload: dict[str, Any] = {
            "schema_version": "aoa-repo-local-kag-federation-v1",
            "federation_identity": {
                "local_id": "projection:os-abyss:repo-self-federation",
                "content_digest": ZERO_DIGEST,
            },
            "owners": owners,
            "summary": {
                "owner_count": len(owners),
                "node_count": len(self._node_handles),
                "relation_count": len(self._relations),
                "cross_repo_relation_count": len(self._cross_repo_relations),
                "unresolved_reference_count": len(self._unresolved_references),
                "external_reference_count": len(self._external_references),
                "relation_kind_counts": dict(sorted(relation_counts.items())),
            },
            "nodes": [copy.deepcopy(self._node_handles[key]) for key in sorted(self._node_handles)],
            "relations": [copy.deepcopy(item) for item in self._local_relations],
            "cross_repo_relations": [copy.deepcopy(item) for item in self._cross_repo_relations],
            "unresolved_references": [copy.deepcopy(item) for item in self._unresolved_references],
            "external_references": [copy.deepcopy(item) for item in self._external_references],
        }
        payload["federation_identity"]["content_digest"] = _digest(payload)
        return payload

    def projection(self) -> dict[str, Any]:
        return copy.deepcopy(self._projection)

    def _owner_hit(
        self,
        node_id: str,
        *,
        access_scopes: set[str] | None,
        relation_ids: Sequence[str] = (),
        anchor_ids: Sequence[str] = (),
        score: float | None = None,
    ) -> dict[str, Any] | None:
        owner = self._node_owner.get(node_id)
        if owner is None:
            return None
        hit = self._queries[owner].read(node_id, access_scopes=access_scopes)
        if hit is None:
            return None
        hit["repo"] = copy.deepcopy(self._bundles[owner][0]["repo"])
        if score is not None:
            hit["score"] = round(score, 8)
        hit["evidence"]["relation_ids"] = sorted(
            set(hit["evidence"]["relation_ids"]) | set(relation_ids)
        )
        hit["evidence"]["anchor_ids"] = sorted(
            set(hit["evidence"]["anchor_ids"]) | set(anchor_ids)
        )
        return hit

    def _owner_rankings(
        self,
        query: str,
        *,
        mode: str,
        limit: int,
        access_scopes: set[str] | None,
    ) -> list[list[dict[str, Any]]]:
        rankings: list[list[dict[str, Any]]] = []
        for owner in sorted(self._queries):
            result = self._queries[owner].query(
                query,
                mode=mode,
                limit=limit,
                access_scopes=access_scopes,
            )
            ranking = []
            for hit in result["hits"]:
                enriched = copy.deepcopy(hit)
                enriched["repo"] = copy.deepcopy(result["repo"])
                ranking.append(enriched)
            rankings.append(ranking)
        return rankings

    @staticmethod
    def _rrf(rankings: Sequence[Sequence[dict[str, Any]]], *, limit: int) -> list[dict[str, Any]]:
        scores: dict[str, float] = defaultdict(float)
        hits: dict[str, dict[str, Any]] = {}
        relation_evidence: dict[str, set[str]] = defaultdict(set)
        anchor_evidence: dict[str, set[str]] = defaultdict(set)
        for ranking in rankings:
            for rank, hit in enumerate(ranking, start=1):
                node_id = str(hit["id"])
                scores[node_id] += 1.0 / (60 + rank)
                hits[node_id] = copy.deepcopy(hit)
                relation_evidence[node_id].update(hit["evidence"]["relation_ids"])
                anchor_evidence[node_id].update(hit["evidence"]["anchor_ids"])
        ordered = sorted(scores, key=lambda node_id: (-scores[node_id], node_id))[:limit]
        output: list[dict[str, Any]] = []
        for node_id in ordered:
            hit = hits[node_id]
            hit["score"] = round(scores[node_id], 8)
            hit["evidence"]["relation_ids"] = sorted(relation_evidence[node_id])
            hit["evidence"]["anchor_ids"] = sorted(anchor_evidence[node_id])
            output.append(hit)
        return output

    def graph(
        self,
        query: str,
        *,
        limit: int = 20,
        max_hops: int = 2,
        access_scopes: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        seed_rankings = self._owner_rankings(
            query,
            mode="lexical",
            limit=max(limit * 4, 64),
            access_scopes=access_scopes,
        )
        seeds = self._rrf(seed_rankings, limit=max(limit * 4, 64))
        query_tokens = set(tokenize(query))
        queue = deque(
            (str(hit["id"]), 0, tuple(), tuple())
            for hit in seeds
            if hit["id"] in self._node_owner
        )
        best: dict[str, tuple[float, tuple[str, ...], tuple[str, ...]]] = {}
        while queue:
            node_id, hops, relation_path, anchor_path = queue.popleft()
            if hops >= max_hops:
                continue
            for neighbor_id, relation in self._adjacency.get(node_id, []):
                candidate = self._owner_hit(neighbor_id, access_scopes=access_scopes)
                if candidate is None:
                    continue
                candidate_tokens = set(
                    tokenize(f"{candidate['label']} {candidate['kind']} {candidate['path']}")
                )
                overlap = len(query_tokens & candidate_tokens)
                score = (
                    (1.0 / (hops + 2))
                    + overlap * 0.25
                    + (0.5 if relation["scope"] == "federated" else 0.0)
                )
                next_relations = (*relation_path, str(relation["id"]))
                next_anchors = (
                    *anchor_path,
                    *(str(item) for item in relation["evidence_anchor_ids"]),
                )
                previous = best.get(neighbor_id)
                if previous is None or score > previous[0]:
                    best[neighbor_id] = (score, next_relations, next_anchors)
                    queue.append((neighbor_id, hops + 1, next_relations, next_anchors))
        traversed: list[dict[str, Any]] = []
        for node_id, (score, relations, anchors) in sorted(
            best.items(), key=lambda item: (-item[1][0], item[0])
        )[: limit * 2]:
            hit = self._owner_hit(
                node_id,
                access_scopes=access_scopes,
                relation_ids=relations,
                anchor_ids=anchors,
                score=score,
            )
            if hit is not None:
                traversed.append(hit)
        return self._rrf([traversed, traversed, seeds], limit=limit)

    def query(
        self,
        query: str,
        *,
        mode: str = "hybrid",
        limit: int = 20,
        access_scopes: set[str] | None = None,
    ) -> dict[str, Any]:
        allowed_scopes = access_scopes if access_scopes is not None else {"public"}
        if mode == "graph":
            hits = self.graph(query, limit=limit, access_scopes=allowed_scopes)
        elif mode in {"exact", "lexical"}:
            hits = self._rrf(
                self._owner_rankings(
                    query,
                    mode=mode,
                    limit=limit,
                    access_scopes=allowed_scopes,
                ),
                limit=limit,
            )
        elif mode == "hybrid":
            exact = self._rrf(
                self._owner_rankings(
                    query,
                    mode="exact",
                    limit=limit,
                    access_scopes=allowed_scopes,
                ),
                limit=limit,
            )
            lexical = self._rrf(
                self._owner_rankings(
                    query,
                    mode="lexical",
                    limit=limit * 2,
                    access_scopes=allowed_scopes,
                ),
                limit=limit * 2,
            )
            graph = self.graph(query, limit=limit * 2, access_scopes=allowed_scopes)
            hits = self._rrf([exact, lexical, graph], limit=limit)
        else:
            raise ValueError(f"unsupported federated query mode: {mode}")
        return {
            "schema_version": "aoa-repo-local-kag-federated-query-result-v1",
            "mode": mode,
            "query": query,
            "federation_digest": self._projection["federation_identity"]["content_digest"],
            "owners": [
                copy.deepcopy(self._bundles[owner][0]["repo"])
                for owner in sorted(self._bundles)
            ],
            "hits": hits,
        }
