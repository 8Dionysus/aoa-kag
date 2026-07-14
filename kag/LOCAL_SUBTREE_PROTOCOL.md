# Local KAG Subtree Protocol

## Purpose

A repo-local KAG subtree is a repository-owned derived knowledge home for
source-linked indexes, graph nodes, graph edges, projections, and receipts.

Its job is to make local knowledge structure reviewable while preserving source
ownership and giving runtime/MCP consumers stable return handles.

## Required Home

| Surface | Record class | Role |
| --- | --- | --- |
| `AGENTS.md` | route | agent operating card |
| `README.md` | route | human operating card |
| `manifest.json` | manifest | source refs, record classes, storage posture, validation routes |
| `nodes/` | node | documents, entities, events, source surfaces, route surfaces |
| `edges/` | edge | direct or declared derived relations between local nodes |
| `indexes/` | index | repository source/artifact/anchor/entity/event/assertion/relation indexes and owner-specific catalogs |
| `projections/` | projection | compact consumer views derived from local records |
| `receipts/` | receipt | generation, validation, freshness, and regrounding evidence |

## Record Envelope

Every portable local KAG record carries:

- `schema_version`
- `repo`
- `local_id`
- `record_class`
- `source_refs`
- `source_owner`
- `provenance_mode`
- `derived_method`
- `generated_or_authored`
- `status`
- `owner_return_route`
- `freshness`
- `builder`
- `validator`
- `storage_posture`
- `consumer_route`

Edges add `from_id`, `to_id`, `edge_kind`, and `edge_trace`.
Indexes and projections name their `source_record_ids`.
Receipts name `receipt_kind`, `result`, and `fallback_route`.

## Repository Index Family

Every provider carries one generated repo-self family over its Git source tree:

| Index | Carries |
| --- | --- |
| `source_surface_index.json` | complete source inventory and classification coordinates |
| `repo_artifact_index.json` | compact physical artifact identity and source-record handles |
| `repo_anchor_index.json` | parser-qualified artifact, section, symbol, and structured-data addresses |
| `repo_entity_index.json` | repository, directory, document, mechanics, contract, command, and code identities |
| `repo_event_index.json` | declared operations and observed Git lifecycle events |
| `repo_assertion_index.json` | quality-gated evidence-bearing claims about canonical nodes and values |
| `repo_relation_index.json` | evidence-bearing graph edges between canonical nodes |

The six normalized indexes pin the source-index digest and resolve common
extractor, parser, provenance, temporal, and trust profiles. Runtime stores
materialize search and graph projections from this canonical family.

Repositories with native domain indexes may also publish
`domain_index_catalog.json`. The catalog carries routes, authority,
materialization, storage, and freshness coordinates while the indexed domain
data remains with its owner.

## Source Ownership

Source repositories keep authored meaning. Local KAG records carry reviewable
handles back to those sources. `aoa-kag` owns the shared schema, registry,
composition, and validation contract.

## Storage Posture

Git carries compact, portable, reviewable provider records and read models.
Runtime serving state routes to `abyss-stack` or `.aoa` stores. Provider
records carry enough metadata for a runtime consumer to check freshness and
return to the owning source.

## Registry And Composition

`manifests/local_kag_readiness.json` records every direct OS Abyss repository,
its current provider status, first record classes, validation route, adoption
order, and owner-return coordinates.

The same matrix carries the OS surface layer used by runtime and MCP routing:

| Surface class | Carries |
| --- | --- |
| `runtime_source_repo` | `abyss-stack` and `abyss-machine` source routes |
| `runtime_mirror` | host-side runtime config/service/log surfaces |
| `organ_home` | `.aoa` session-memory, `.agents` capability, and `.codex` Codex-plane access homes |
| `bundle_repo` | portable organ source repos such as `aoa-session-memory` |
| `connector_repo` | external-source connector repos |
| `collection_home` | collection roots for connector and bundle families |

Provider-ready repositories expose a local `kag/` packet with all five record
classes. Candidate repositories keep exact source surfaces and adoption order
in the readiness matrix until their owner route is ready.

## MCP Access Shape

The generated handoff gives `aoa-kag-mcp` one compact agent protocol:

| Surface | Carries |
| --- | --- |
| `kag_discover` | owners, classes, kinds, strategies, freshness, projections, access, and bounds |
| `kag_search` | exact, lexical, semantic, hybrid, graph, and automatic retrieval with filters and pagination |
| `kag_read` | addressed owner manifests, canonical records, documents, anchors, sources, schemas, traces, and projections |
| `kag_traverse` | bounded owner-qualified relation paths and traversal evidence |
| `kag_explain` | route, adapter, degradation, projection, and evidence explanation for a trace |

`mcp_handoff.resource_templates` owns the nine `aoa-kag://` shapes.
`mcp_handoff.root_boundaries` carries containment and owner-return metadata for
the runtime adapter. MCP Roots remain a client capability rather than a
repo-provider declaration.

## Current Providers

| Repository | Home | First source route |
| --- | --- | --- |
| `aoa-kag` | `kag/` | local subtree schema and readiness matrix |
| `Tree-of-Sophia` | `kag/` | ToS source-owned KAG export and graph projection |
| `aoa-techniques` | `kag/` | technique source-owned KAG export and AOA-T-0043 bundle |
| `aoa-skills` | `kag/` | skill graph and canonical skill source home |
| `Agents-of-Abyss` | `kag/` | ecosystem registry and federation rules |
| `aoa-agents` | `kag/` | agent source-home manifest and role registry |
| `aoa-playbooks` | `kag/` | playbook source-home manifest and scenario registry |
| `aoa-memo` | `kag/` | memory registry and reviewed memory corpus route |
| `aoa-evals` | `kag/` | eval report index and proof bundle route |
| `aoa-routing` | `kag/` | routing source-home manifest and cross-repo registry |
| `aoa-sdk` | `kag/` | SDK source-home manifest and typed KAG helper route |
| `aoa-session-memory` | `kag/` | session-memory kernel, route atlas, and manifest schema |
| `8Dionysus` | `kag/` | public ecosystem profile and workspace memory map |
| `Dionysus` | `kag/` | seed garden route map and registry |
| `ATM10-Agent` | `kag/` | project-local KAG runtime and operator runbook route |
| `aoa-stats` | `kag/` | derived KAG stats observability registry |
| `aoa-4pda-connector` | `kag/` | 4PDA connector source policy and storage boundary |
| `aoa-course-connector` | `kag/` | course connector boundaries and source/storage policies |
| `aoa-discord-connector` | `kag/` | Discord connector permission policy and storage boundary |
| `aoa-stackoverflow-connector` | `kag/` | StackOverflow connector source policy and storage boundary |
| `aoa-telegram-connector` | `kag/` | Telegram connector permission policy and storage boundary |
| `aoa-xda-connector` | `kag/` | XDA connector source policy and storage boundary |
| `abyss-stack` | `kag/` | runtime source topology and MCP access planes |
| `abyss-machine` | `kag/` | host source contracts and validation lanes |
