from __future__ import annotations

import copy
import math
import re
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from typing import Any, Iterable, Sequence


TOKEN = re.compile(r"\w+", re.UNICODE)


def tokenize(value: str) -> tuple[str, ...]:
    return tuple(token.casefold() for token in TOKEN.findall(value) if len(token) > 1)


def retrieval_document_role(record: dict[str, Any]) -> str:
    path = str(record["identity"]["path"])
    folded_parts = {part.casefold() for part in path.replace("\\", "/").split("/")}
    name = path.rsplit("/", 1)[-1].casefold()
    if folded_parts.intersection({"fixtures", "fixture", "testdata", "golden"}) or any(
        marker in name
        for marker in ("retrieval-eval.", "retrieval_eval.", ".fixture.", "_fixture.")
    ):
        return "evaluation_fixture"
    return str(record.get("document_role") or "none")


@dataclass(frozen=True)
class _Node:
    id: str
    node_class: str
    kind: str
    label: str
    text: str
    path: str
    source_record_ids: tuple[str, ...]
    anchor_ids: tuple[str, ...]
    access_scope: str
    provenance_ref: str
    temporal_ref: str
    trust_ref: str
    record: dict[str, Any]


class RepoKagQuery:
    def __init__(self, source_index: dict[str, Any], family: dict[str, dict[str, Any]]) -> None:
        self.source_index = source_index
        self.family = family
        self.repo = copy.deepcopy(source_index["repo"])
        self.freshness_digest = str(source_index["index_identity"]["content_digest"])
        self._source_records = {
            str(record["identity"]["id"]): record
            for record in source_index["records"]
        }
        self._nodes = self._build_nodes()
        self._tokens = {node_id: tokenize(node.text) for node_id, node in self._nodes.items()}
        self._relations = {
            str(entry["id"]): entry
            for entry in family["relation"]["entries"]
        }
        self._adjacency: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
        for relation in self._relations.values():
            self._adjacency[str(relation["from_id"])].append((str(relation["to_id"]), relation))
            self._adjacency[str(relation["to_id"])].append((str(relation["from_id"]), relation))

    def _source_access(self, source_ids: Sequence[str]) -> str:
        scopes = {
            str(self._source_records[source_id].get("access", {}).get("scope") or "public")
            for source_id in source_ids
            if source_id in self._source_records
        }
        for scope in ("private", "local", "runtime", "public"):
            if scope in scopes:
                return scope
        return "public"

    def source_access(self, source_ids: Sequence[str]) -> str:
        return self._source_access(source_ids)

    def _source_dimension(
        self,
        source_ids: Sequence[str],
        field: str,
        *,
        fallback: str,
    ) -> str:
        values: set[str] = set()
        for source_id in source_ids:
            record = self._source_records.get(source_id)
            if record is None:
                continue
            value = (
                retrieval_document_role(record)
                if field == "document_role"
                else str(record.get(field) or fallback)
            )
            values.add(value)
        if field == "document_role" and "evaluation_fixture" in values:
            return "evaluation_fixture"
        if len(values) == 1:
            return next(iter(values))
        return "mixed" if values else fallback

    def projection_handle(self, record_id: str) -> dict[str, Any] | None:
        node = self._nodes.get(record_id)
        if node is None:
            return None
        event_without_sources = node.node_class == "event" and not node.source_record_ids
        handle = {
            "record_form": "projection_handle",
            "label": node.label,
            "path": node.path,
            "search_text": node.text,
            "source_record_ids": list(node.source_record_ids),
            "anchor_ids": list(node.anchor_ids),
            "access_scope": node.access_scope,
            "document_role": self._source_dimension(
                node.source_record_ids,
                "document_role",
                fallback="repository_event" if event_without_sources else "none",
            ),
            "surface_state": self._source_dimension(
                node.source_record_ids,
                "surface_state",
                fallback="observed_history" if event_without_sources else "authored_source",
            ),
            "provenance_ref": node.provenance_ref,
            "temporal_ref": node.temporal_ref,
            "trust_ref": node.trust_ref,
        }
        primary_source = next(
            (
                self._source_records[source_id]
                for source_id in node.source_record_ids
                if source_id in self._source_records
            ),
            None,
        )
        if primary_source is not None:
            handle["abi"] = copy.deepcopy(primary_source["abi"])
            handle["signs"] = copy.deepcopy(primary_source["signs"])
            handle["owner_return_route"] = copy.deepcopy(
                primary_source["owner_return_route"]
            )
        return handle

    def _build_nodes(self) -> dict[str, _Node]:
        nodes: dict[str, _Node] = {}
        for artifact in self.family["artifact"]["entries"]:
            source_id = str(artifact["id"])
            path = str(artifact["path"])
            nodes[source_id] = _Node(
                id=source_id,
                node_class="artifact",
                kind=str(artifact["artifact_kind"]),
                label=path,
                text=f"{path} {artifact['artifact_kind']} {artifact['mime']}",
                path=path,
                source_record_ids=(source_id,),
                anchor_ids=(str(artifact["anchor_id"]),),
                access_scope=self._source_access((source_id,)),
                provenance_ref=str(artifact["provenance_ref"]),
                temporal_ref=str(artifact["temporal_ref"]),
                trust_ref=str(artifact["trust_ref"]),
                record=copy.deepcopy(artifact),
            )
        for anchor in self.family["anchor"]["entries"]:
            source_id = str(anchor["source_record_id"])
            path = str(self._source_records[source_id]["identity"]["path"])
            anchor_id = str(anchor["id"])
            nodes[anchor_id] = _Node(
                id=anchor_id,
                node_class="anchor",
                kind=str(anchor["anchor_kind"]),
                label=str(anchor["label"]),
                text=(
                    f"{anchor['label']} {anchor['semantic_key']} "
                    f"{anchor['qualified_name']} {path} {anchor['anchor_kind']}"
                ),
                path=path,
                source_record_ids=(source_id,),
                anchor_ids=(anchor_id,),
                access_scope=self._source_access((source_id,)),
                provenance_ref=str(anchor["provenance_ref"]),
                temporal_ref=str(anchor["temporal_ref"]),
                trust_ref=str(anchor["trust_ref"]),
                record=copy.deepcopy(anchor),
            )
        for entity in self.family["entity"]["entries"]:
            source_ids = tuple(str(item) for item in entity["source_record_ids"])
            entity_id = str(entity["id"])
            path = ""
            if source_ids and source_ids[0] in self._source_records:
                path = str(self._source_records[source_ids[0]]["identity"]["path"])
            nodes[entity_id] = _Node(
                id=entity_id,
                node_class="entity",
                kind=str(entity["entity_kind"]),
                label=str(entity["label"]),
                text=f"{entity['label']} {entity['semantic_key']} {entity['entity_kind']} {path}",
                path=path,
                source_record_ids=source_ids,
                anchor_ids=tuple(str(item) for item in entity["anchor_ids"]),
                access_scope=self._source_access(source_ids),
                provenance_ref=str(entity["provenance_ref"]),
                temporal_ref=str(entity["temporal_ref"]),
                trust_ref=str(entity["trust_ref"]),
                record=copy.deepcopy(entity),
            )
        for event in self.family["event"]["entries"]:
            source_ids = tuple(str(item) for item in event["source_record_ids"])
            event_id = str(event["id"])
            change_text = " ".join(
                f"{item['change_kind']} {item['old_path']} {item['path']}"
                for item in event["changes"]
            )
            nodes[event_id] = _Node(
                id=event_id,
                node_class="event",
                kind=str(event["event_kind"]),
                label=str(event["label"]),
                text=f"{event['label']} {event['event_kind']} {change_text}",
                path="",
                source_record_ids=source_ids,
                anchor_ids=tuple(str(item) for item in event["anchor_ids"]),
                access_scope=self._source_access(source_ids),
                provenance_ref=str(event["provenance_ref"]),
                temporal_ref=str(event["temporal_ref"]),
                trust_ref=str(event["trust_ref"]),
                record=copy.deepcopy(event),
            )
        for assertion in self.family["assertion"]["entries"]:
            source_ids = tuple(str(item) for item in assertion["source_record_ids"])
            assertion_id = str(assertion["id"])
            path = ""
            if source_ids and source_ids[0] in self._source_records:
                path = str(self._source_records[source_ids[0]]["identity"]["path"])
            object_value = str(assertion["object"]["value"])
            predicate = str(assertion["predicate"])
            nodes[assertion_id] = _Node(
                id=assertion_id,
                node_class="assertion",
                kind=str(assertion["assertion_kind"]),
                label=f"{predicate}: {object_value}",
                text=(
                    f"{predicate} {object_value} {assertion['subject_id']} "
                    f"{path} {assertion['evidence_class']}"
                ),
                path=path,
                source_record_ids=source_ids,
                anchor_ids=tuple(str(item) for item in assertion["evidence_anchor_ids"]),
                access_scope=self._source_access(source_ids),
                provenance_ref=str(assertion["provenance_ref"]),
                temporal_ref=str(assertion["temporal_ref"]),
                trust_ref=str(assertion["trust_ref"]),
                record=copy.deepcopy(assertion),
            )
        anchor_sources = {
            str(anchor["id"]): str(anchor["source_record_id"])
            for anchor in self.family["anchor"]["entries"]
        }
        for relation in self.family["relation"]["entries"]:
            relation_id = str(relation["id"])
            anchor_ids = tuple(str(item) for item in relation["evidence_anchor_ids"])
            source_ids = tuple(
                sorted(
                    {
                        anchor_sources[anchor_id]
                        for anchor_id in anchor_ids
                        if anchor_id in anchor_sources
                    }
                )
            )
            path = ""
            if source_ids:
                path = str(self._source_records[source_ids[0]]["identity"]["path"])
            relation_kind = str(relation["relation_kind"])
            nodes[relation_id] = _Node(
                id=relation_id,
                node_class="relation",
                kind=relation_kind,
                label=f"{relation_kind}: {relation['from_id']} -> {relation['to_id']}",
                text=(
                    f"{relation_kind} {relation['from_id']} {relation['to_id']} "
                    f"{path} {relation['evidence_class']}"
                ),
                path=path,
                source_record_ids=source_ids,
                anchor_ids=anchor_ids,
                access_scope=self._source_access(source_ids),
                provenance_ref=str(relation["provenance_ref"]),
                temporal_ref=str(relation["temporal_ref"]),
                trust_ref=str(relation["trust_ref"]),
                record=copy.deepcopy(relation),
            )
        return nodes

    def _allowed(self, node: _Node, *, access_scopes: set[str] | None) -> bool:
        return access_scopes is None or node.access_scope in access_scopes

    def _profile(self, node: _Node, profile_kind: str, profile_ref: str) -> dict[str, Any]:
        profiles = self.family[node.node_class]["profiles"]
        profile = copy.deepcopy(profiles[profile_kind][profile_ref])
        profile["ref"] = profile_ref
        if profile_kind == "provenance":
            extractor_ref = str(profile["extractor_ref"])
            profile["extractor"] = copy.deepcopy(profiles["extractors"][extractor_ref])
        return profile

    def _source_contexts(self, source_record_ids: Sequence[str]) -> list[dict[str, Any]]:
        contexts: list[dict[str, Any]] = []
        for source_id in source_record_ids:
            record = self._source_records.get(source_id)
            if record is None:
                continue
            identity = record["identity"]
            contexts.append(
                {
                    "source_record_id": source_id,
                    "path": str(identity["path"]),
                    "version_id": str(identity["version_id"]),
                    "content_digest": str(identity["content_hash"]),
                    "document_role": str(record.get("document_role") or "none"),
                    "surface_state": str(
                        record.get("surface_state") or "authored_source"
                    ),
                    "abi": copy.deepcopy(record["abi"]),
                    "signs": copy.deepcopy(record["signs"]),
                    "provenance": copy.deepcopy(record["provenance"]),
                    "freshness": copy.deepcopy(record["freshness"]),
                    "access": copy.deepcopy(record["access"]),
                    "owner_return_route": copy.deepcopy(record["owner_return_route"]),
                }
            )
        return contexts

    def _matches(
        self,
        node: _Node,
        *,
        node_classes: set[str] | None = None,
        kinds: set[str] | None = None,
        path_prefix: str = "",
        provenance_modes: set[str] | None = None,
        temporal_states: set[str] | None = None,
        abi_compatibilities: set[str] | None = None,
        sign_states: set[str] | None = None,
        access_scopes: set[str] | None = None,
    ) -> bool:
        if node_classes is not None and node.node_class not in node_classes:
            return False
        if kinds is not None and node.kind not in kinds:
            return False
        if path_prefix and not node.path.startswith(path_prefix):
            return False
        if not self._allowed(node, access_scopes=access_scopes):
            return False
        provenance = self._profile(node, "provenance", node.provenance_ref)
        if provenance_modes is not None and provenance["mode"] not in provenance_modes:
            return False
        temporal = self._profile(node, "temporal", node.temporal_ref)
        if temporal_states is not None and temporal["state"] not in temporal_states:
            return False
        source_contexts = self._source_contexts(node.source_record_ids)
        if abi_compatibilities is not None and not any(
            source["abi"]["compatibility"] in abi_compatibilities for source in source_contexts
        ):
            return False
        if sign_states is not None and not any(
            source["signs"]["verification_state"] in sign_states for source in source_contexts
        ):
            return False
        return True

    def _hit(
        self,
        node: _Node,
        score: float,
        *,
        relation_ids: Iterable[str] = (),
        evidence_anchor_ids: Iterable[str] = (),
    ) -> dict[str, Any]:
        relation_evidence = set(relation_ids)
        if node.node_class == "relation":
            relation_evidence.add(node.id)
        return {
            "id": node.id,
            "node_class": node.node_class,
            "kind": node.kind,
            "label": node.label,
            "path": node.path,
            "score": round(score, 8),
            "source_record_ids": list(node.source_record_ids),
            "anchor_ids": list(node.anchor_ids),
            "access_scope": node.access_scope,
            "provenance": self._profile(node, "provenance", node.provenance_ref),
            "temporal": self._profile(node, "temporal", node.temporal_ref),
            "trust": self._profile(node, "trust", node.trust_ref),
            "sources": self._source_contexts(node.source_record_ids),
            "record": copy.deepcopy(node.record),
            "evidence": {
                "relation_ids": sorted(relation_evidence),
                "anchor_ids": sorted(set(evidence_anchor_ids) | set(node.anchor_ids)),
            },
        }

    def discover(self) -> dict[str, Any]:
        node_counts = Counter(node.node_class for node in self._nodes.values())
        kind_counts: dict[str, dict[str, int]] = {}
        for node_class in sorted(node_counts):
            kind_counts[node_class] = dict(
                sorted(
                    Counter(
                        node.kind for node in self._nodes.values() if node.node_class == node_class
                    ).items()
                )
            )
        return {
            "schema_version": "aoa-repo-local-kag-discovery-v1",
            "repo": copy.deepcopy(self.repo),
            "source_index": {
                "local_id": self.source_index["index_identity"]["local_id"],
                "content_digest": self.freshness_digest,
                "git_ref": self.source_index["repo"]["git_ref"],
            },
            "query_modes": ["exact", "lexical", "graph", "hybrid"],
            "filter_fields": [
                "node_class",
                "kind",
                "path_prefix",
                "provenance_mode",
                "temporal_state",
                "abi_compatibility",
                "sign_state",
                "access_scope",
            ],
            "node_counts": dict(sorted(node_counts.items())),
            "kind_counts": kind_counts,
        }

    def read(
        self,
        record_id: str,
        *,
        access_scopes: set[str] | None = None,
    ) -> dict[str, Any] | None:
        node = self._nodes.get(record_id)
        if node is None or not self._allowed(node, access_scopes=access_scopes):
            return None
        return self._hit(node, 1.0)

    def filter(
        self,
        *,
        limit: int = 100,
        node_classes: set[str] | None = None,
        kinds: set[str] | None = None,
        path_prefix: str = "",
        provenance_modes: set[str] | None = None,
        temporal_states: set[str] | None = None,
        abi_compatibilities: set[str] | None = None,
        sign_states: set[str] | None = None,
        access_scopes: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        nodes = sorted(
            (
                node
                for node in self._nodes.values()
                if self._matches(
                    node,
                    node_classes=node_classes,
                    kinds=kinds,
                    path_prefix=path_prefix,
                    provenance_modes=provenance_modes,
                    temporal_states=temporal_states,
                    abi_compatibilities=abi_compatibilities,
                    sign_states=sign_states,
                    access_scopes=access_scopes,
                )
            ),
            key=lambda node: (node.node_class, node.kind, node.id),
        )
        return [self._hit(node, 1.0) for node in nodes[:limit]]

    def exact(
        self,
        value: str,
        *,
        limit: int = 20,
        node_classes: set[str] | None = None,
        access_scopes: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        needle = value.casefold()
        matches: list[tuple[float, _Node]] = []
        for node in self._nodes.values():
            if node_classes is not None and node.node_class not in node_classes:
                continue
            if not self._allowed(node, access_scopes=access_scopes):
                continue
            fields = (node.id.casefold(), node.path.casefold(), node.label.casefold())
            if needle in fields:
                matches.append((1.0, node))
            elif any(field.startswith(needle) for field in fields if field):
                matches.append((0.9, node))
        matches.sort(key=lambda item: (-item[0], item[1].id))
        return [self._hit(node, score) for score, node in matches[:limit]]

    def lexical(
        self,
        query: str,
        *,
        limit: int = 20,
        node_classes: set[str] | None = None,
        access_scopes: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        query_tokens = tokenize(query)
        if not query_tokens:
            return []
        candidates = [
            node
            for node in self._nodes.values()
            if (node_classes is None or node.node_class in node_classes)
            and self._allowed(node, access_scopes=access_scopes)
        ]
        if not candidates:
            return []
        document_frequency = Counter()
        lengths: dict[str, int] = {}
        term_frequencies: dict[str, Counter[str]] = {}
        for node in candidates:
            frequencies = Counter(self._tokens[node.id])
            term_frequencies[node.id] = frequencies
            lengths[node.id] = sum(frequencies.values())
            for token in set(query_tokens) & set(frequencies):
                document_frequency[token] += 1
        average_length = sum(lengths.values()) / max(len(lengths), 1)
        scored: list[tuple[float, _Node]] = []
        for node in candidates:
            score = 0.0
            frequencies = term_frequencies[node.id]
            for token in query_tokens:
                frequency = frequencies[token]
                if not frequency:
                    continue
                df = document_frequency[token]
                inverse = math.log(1 + (len(candidates) - df + 0.5) / (df + 0.5))
                denominator = frequency + 1.2 * (
                    1 - 0.75 + 0.75 * lengths[node.id] / max(average_length, 1)
                )
                score += inverse * frequency * 2.2 / denominator
            if score > 0:
                scored.append((score, node))
        scored.sort(key=lambda item: (-item[0], item[1].id))
        return [self._hit(node, score) for score, node in scored[:limit]]

    def traverse(
        self,
        seed_ids: Sequence[str],
        *,
        query: str = "",
        max_hops: int = 2,
        limit: int = 50,
        relation_kinds: set[str] | None = None,
        access_scopes: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        query_tokens = set(tokenize(query))
        queue = deque((seed_id, 0, (), ()) for seed_id in seed_ids if seed_id in self._nodes)
        best: dict[str, tuple[float, tuple[str, ...], tuple[str, ...]]] = {}
        while queue:
            node_id, hops, relation_path, anchor_path = queue.popleft()
            if hops >= max_hops:
                continue
            neighbors = []
            for neighbor_id, relation in self._adjacency.get(node_id, []):
                if relation_kinds is not None and relation["relation_kind"] not in relation_kinds:
                    continue
                neighbor = self._nodes.get(neighbor_id)
                if neighbor is None or not self._allowed(neighbor, access_scopes=access_scopes):
                    continue
                overlap = len(query_tokens & set(self._tokens[neighbor_id]))
                neighbors.append((overlap, neighbor, relation))
            neighbors.sort(key=lambda item: (-item[0], item[1].id))
            for overlap, neighbor, relation in neighbors[:64]:
                score = (1.0 / (hops + 2)) + overlap * 0.25
                next_relations = (*relation_path, str(relation["id"]))
                next_anchors = (*anchor_path, *(str(item) for item in relation["evidence_anchor_ids"]))
                previous = best.get(neighbor.id)
                if previous is None or score > previous[0]:
                    best[neighbor.id] = (score, next_relations, next_anchors)
                    queue.append((neighbor.id, hops + 1, next_relations, next_anchors))
        ranked = sorted(best.items(), key=lambda item: (-item[1][0], item[0]))[:limit]
        return [
            self._hit(
                self._nodes[node_id],
                score,
                relation_ids=relation_ids,
                evidence_anchor_ids=anchor_ids,
            )
            for node_id, (score, relation_ids, anchor_ids) in ranked
        ]

    def graph(
        self,
        query: str,
        *,
        limit: int = 20,
        max_hops: int = 2,
        access_scopes: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        seeds = self.lexical(query, limit=max(limit, 8), access_scopes=access_scopes)
        traversed = self.traverse(
            [hit["id"] for hit in seeds],
            query=query,
            max_hops=max_hops,
            limit=limit * 2,
            access_scopes=access_scopes,
        )
        return self._rrf([seeds, traversed], limit=limit)

    def hybrid(
        self,
        query: str,
        *,
        limit: int = 20,
        access_scopes: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        exact = self.exact(query, limit=limit, access_scopes=access_scopes)
        lexical = self.lexical(query, limit=limit * 2, access_scopes=access_scopes)
        graph = self.graph(query, limit=limit * 2, access_scopes=access_scopes)
        return self._rrf([exact, lexical, graph], limit=limit)

    def _rrf(self, rankings: Sequence[Sequence[dict[str, Any]]], *, limit: int) -> list[dict[str, Any]]:
        scores: dict[str, float] = defaultdict(float)
        evidence_relations: dict[str, set[str]] = defaultdict(set)
        evidence_anchors: dict[str, set[str]] = defaultdict(set)
        for ranking in rankings:
            for rank, hit in enumerate(ranking, start=1):
                node_id = str(hit["id"])
                scores[node_id] += 1.0 / (60 + rank)
                evidence_relations[node_id].update(hit["evidence"]["relation_ids"])
                evidence_anchors[node_id].update(hit["evidence"]["anchor_ids"])
        ranked = sorted(scores, key=lambda node_id: (-scores[node_id], node_id))[:limit]
        return [
            self._hit(
                self._nodes[node_id],
                scores[node_id],
                relation_ids=evidence_relations[node_id],
                evidence_anchor_ids=evidence_anchors[node_id],
            )
            for node_id in ranked
        ]

    def query(
        self,
        query: str,
        *,
        mode: str = "hybrid",
        limit: int = 20,
        access_scopes: set[str] | None = None,
    ) -> dict[str, Any]:
        routes = {
            "exact": self.exact,
            "lexical": self.lexical,
            "graph": self.graph,
            "hybrid": self.hybrid,
        }
        if mode not in routes:
            raise ValueError(f"unsupported query mode: {mode}")
        hits = routes[mode](query, limit=limit, access_scopes=access_scopes)
        return {
            "schema_version": "aoa-repo-local-kag-query-result-v1",
            "repo": copy.deepcopy(self.repo),
            "mode": mode,
            "query": query,
            "source_index": {
                "local_id": self.source_index["index_identity"]["local_id"],
                "content_digest": self.freshness_digest,
                "git_ref": self.source_index["repo"]["git_ref"],
            },
            "hits": hits,
        }
