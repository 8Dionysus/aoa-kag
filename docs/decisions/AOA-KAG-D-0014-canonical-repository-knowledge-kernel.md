# Canonical Repository Knowledge Kernel

## Index Metadata

- Decision ID: AOA-KAG-D-0014
- Original date: 2026-07-11
- Surface classes: kag/source-home, schema contract, generated readmodel, validation guard, query foundation, federation input
- KAG surfaces: repo-self index family, owner-qualified identity, structural anchors, repository events, evidence relations, profile-aware query
- Source lanes: aoa-kag, OS Abyss repo-local kag homes, connectors, bundles, runtime source repositories
- Guard families: owner namespace, Git lineage, source coverage, anchor precision, relation evidence, profile resolution, incremental parity, source return, access isolation
- Posture: accepted

## Context

AOA-KAG-D-0013 established the source-surface index as the first common
repo-local atom. Its initial repository projections separated artifacts,
entities, and repository-visible events, while graph extraction and scalable
retrieval still lacked a shared canonical input.

OS Abyss needs one universal repository self-description that keeps each
owner's files, directories, documents, code symbols, mechanics, events, and
relations distinct across a rapidly changing multi-repository system. The same
kernel must also preserve native domain indexes as owner surfaces, including
the session-memory and connector index systems.

## Decision

The common repo-self kernel is a normalized family under each owner's
`kag/indexes/`:

- `source_surface_index.json` owns tracked artifact classification, versions,
  ABI/sign posture, freshness, access, source routes, and tool coordinates;
- `repo_artifact_index.json` owns physical and lineage-stable artifact records;
- `repo_anchor_index.json` owns addressable internal structure and outbound
  reference declarations;
- `repo_entity_index.json` owns logical repository, directory, document,
  mechanics, contract, command, and code-symbol identities;
- `repo_event_index.json` owns source-declared operations and observed Git
  lifecycle events;
- `repo_assertion_index.json` owns quality-gated evidence-bearing claims about
  canonical nodes and literal, node, or reference objects;
- `repo_relation_index.json` owns evidence-bearing edges between current
  canonical nodes.

Every identity carries the repository namespace. Artifact logical identity is
derived from Git lineage, while version identity is derived from content. The
repository family resolves shared extractor, parser, provenance, temporal, and
trust profiles by reference. Assertions and relations carry source anchors,
evidence class, confidence, temporal validity, provenance, and trust.

The anchor index retains normalized outbound reference declarations so an
incremental build can reuse unchanged parsing results and still recompute
relations against the current node set. Full and incremental generation produce
the same canonical payload.

`scripts/repo_local/query.py` reads validated canonical records through owner
discovery, addressed read, profile-aware filtering, exact lookup, BM25,
query-aware graph traversal, and hybrid fusion. Query results return source
contexts with ABI, signs, provenance, freshness, access, owner routes, trust,
and evidence.

`aoa-kag` owns the schemas, extraction rules, validation, query kernel, owner
registry, and federation assembly. Each repository owns its generated repo-self
family and optional domain-index catalog. `abyss-stack` materializes large
lexical, vector, and graph stores from these canonical inputs.

## Options Considered

- Extend the source index with more embedded fields: keeps one file, while
  coupling physical artifacts, semantic nodes, history, and graph assertions.
- Commit fully materialized retrieval and graph stores in every repository:
  gives direct serving artifacts, with high churn and storage cost across all
  owners.
- Use a normalized canonical kernel with runtime projections: keeps the Git
  surface reviewable, supports incremental extraction, and gives every runtime
  projection the same reproducible inputs.

## Rationale

The normalized kernel gives new repository surfaces a stable artifact and
directory address immediately, then adds richer owner or parser semantics as
evidence becomes available. Qualified identities preserve owner boundaries in
federation. Profile references keep repeated provenance and trust metadata
compact. Persisted outbound declarations make incremental relation rebuilds
accurate when targets move or disappear.

This route supplies the stable read/query substrate needed by federation and
later MCP access while preserving the function of each repository's native
index and graph systems.

## Consequences

- D-0013's first index atom evolves into a seven-file v2 repository family.
- Every tracked file receives lineage-stable artifact identity and an artifact
  anchor; supported structures receive parser-qualified internal anchors.
- Repository and directory nodes expose a navigable tree before semantic graph
  enrichment.
- Git add, modify, rename, copy, delete, and staged changes retain stable object
  identities and historical evidence.
- Owner adoption includes schema migration, family regeneration, local
  validation, and federation integrity checks.
- Runtime projection builders can rebuild exact, lexical, vector, hybrid, and
  graph stores from owner-published canonical records.

## Source Surfaces

- `schemas/repo-local-kag-index.schema.json`
- `schemas/repo-local-kag-repository-index.schema.json`
- `schemas/repo-local-kag-query-result.schema.json`
- `examples/repo_local_kag_index.example.json`
- `examples/repo_local_kag_query_result.example.json`
- `scripts/generate_repo_local_kag_index.py`
- `scripts/query_repo_local_kag.py`
- `scripts/repo_local/`
- `scripts/validators/repo_local_kag_index.py`
- `kag/indexes/source_surface_index.json`
- `kag/indexes/repo_artifact_index.json`
- `kag/indexes/repo_anchor_index.json`
- `kag/indexes/repo_entity_index.json`
- `kag/indexes/repo_event_index.json`
- `kag/indexes/repo_assertion_index.json`
- `kag/indexes/repo_relation_index.json`
- `tests/test_repo_local_kag_index.py`
- `tests/test_repo_local_kag_repository_indexes.py`

## Validation

Validation follows `docs/validation/COMMAND_AUTHORITY.md`, the repo-local family
validator, focused contract tests, generated parity, and each adopting owner's
canonical landing route.
