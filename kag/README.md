# KAG Source Home

`kag/` is the source home and local provider home for `aoa-kag`.

It defines the shared repo-local KAG contract and carries the `aoa-kag`
repo-self provider packet. OS Abyss repositories publish the same common family
with owner-specific catalogs where their domain requires them.

## Operating Card

| Field | Route |
| --- | --- |
| role | KAG local-subtree protocol and `aoa-kag` provider packet |
| input | schema, example, readiness matrix, provider-ready sibling packets |
| output | manifest, node, edge, index, projection, receipt, registry/composition inputs |
| owner | `kag/AGENTS.md`, this README, `source_home.manifest.json`, `manifest.json` |
| consumer route | `aoa-kag` federation, `abyss-stack` runtime projections, `aoa-kag-mcp` |
| owner return | `schemas/`, `examples/`, `manifests/`, `scripts/validators/`, `tests/` |

## Current Files

| Surface | Role |
| --- | --- |
| `AGENTS.md` | agent route card |
| `README.md` | human operating card |
| `source_home.manifest.json` | machine-readable source-home atlas |
| `LOCAL_SUBTREE_PROTOCOL.md` | shared local KAG subtree protocol |
| `manifest.json` | `aoa-kag` local provider manifest |
| `nodes/` | source-linked contract and readiness nodes |
| `edges/` | local relation records |
| `indexes/` | repository index family and optional owner-domain catalog |
| `projections/` | MCP/resource-facing compact views |
| `receipts/` | validation receipts |

The common logical family under `indexes/` separates source classification, physical
artifacts, internal anchors, logical entities, repository events,
quality-gated assertions, and evidence-bearing relations. Owner-qualified
identities, Git lineage,
ABI/signs, provenance, freshness, access, temporal state, and trust remain
resolvable through the family.

Git tracks that family as `index_family.manifest.json` and bounded
content-addressed JSONL shards. Source, structure, outbound declarations, and
repository history are the portable corpus; artifact, entity, assertion, and
relation files are deterministic compatibility views assembled on demand.
Tracked bytes and generated change amplification are blocking budgets.

The family supports both home-port generations. A v1 manifest distinguishes a
canonical owner skill under `skills/` from its exact declared repository copy
under `.agents/skills/`; both files remain addressable and a typed
`derives_from` relation returns to the owner. A v2 manifest declares selection
through the OS user profile and forbids a same-name repository copy, so the
canonical owner skill is the only repo-local source record.

`scripts/query_repo_local_kag.py` exposes validated exact, lexical, graph, and
hybrid retrieval. The programmatic query kernel also provides discovery,
addressed read, and profile-aware filtering. An owner with native indexes adds
`domain_index_catalog.json` as a route catalog governed by
`schemas/domain-index-catalog.schema.json`.

`scripts/assemble_repo_local_kag_family.py` reconstructs the exact seven-file
v2 view for compatibility consumers without restoring those monoliths as
tracked source-repository artifacts.

## Provider Role

The `aoa-kag` provider packet anchors the OS Abyss local KAG contract:

- schema identity lives in `schemas/local-kag-subtree.schema.json`
- example packet identity lives in `examples/local_kag_subtree.example.json`
- repo readiness lives in `manifests/local_kag_readiness.json`
- validation lives in `scripts/validators/local_kag_subtree.py`
- focused tests live in `tests/test_validate_kag.py`

## OS Surface Layer

`manifests/local_kag_readiness.json` covers direct repos and the surrounding OS
surfaces that matter for indexing and MCP access:

| Layer | Surfaces |
| --- | --- |
| runtime source | `/home/dionysus/src/abyss-stack`, `/home/dionysus/src/abyss-machine` |
| runtime mirror | `/srv/AbyssOS/abyss-stack` |
| organs | `/srv/AbyssOS/.aoa`, `/srv/AbyssOS/.agents` |
| bundles | `/srv/AbyssOS/bundles`, `bundles/aoa-session-memory` |
| connectors | `/srv/AbyssOS/connectors` and its connector repos |

## OS Abyss Provider Pattern

The provider-ready homes are:

| Repository | Local home | First source route |
| --- | --- | --- |
| `aoa-kag` | `kag/` | local subtree schema and readiness matrix |
| `Tree-of-Sophia` | `kag/` | `ToS/derived-exports/kag_export.min.json` |
| `aoa-techniques` | `kag/` | `generated/kag_export.min.json` |
| `aoa-skills` | `kag/` | `generated/skill_graph.json` |
| `Agents-of-Abyss` | `kag/` | `generated/ecosystem_registry.min.json` |
| `aoa-agents` | `kag/` | `agents/source_home.manifest.json` |
| `aoa-playbooks` | `kag/` | `playbooks/source_home.manifest.json` |
| `aoa-memo` | `kag/` | `generated/memory/memo_registry.min.json` |
| `aoa-evals` | `kag/` | `generated/eval_report_index.min.json` |
| `aoa-routing` | `kag/` | `routing/source_home.manifest.json` |
| `aoa-sdk` | `kag/` | `sdk/source_home.manifest.json` |
| `aoa-session-memory` | `kag/` | `schemas/session.manifest.schema.json` |
| `8Dionysus` | `kag/` | `generated/workspace_memory_map.min.json` |
| `Dionysus` | `kag/` | `generated/seed_route_map.min.json` |
| `ATM10-Agent` | `kag/` | `src/kag/baseline.py` |
| `aoa-stats` | `kag/` | `generated/agon_kag_stats_observability_registry.min.json` |
| `abyss-stack` | `kag/` | `mcp/README.md` |
| `abyss-machine` | `kag/` | `manifests/repo_scaffold.manifest.json` |
| `aoa-4pda-connector` | `kag/` | `connector/SOURCE_POLICY.md` |
| `aoa-course-connector` | `kag/` | `connector/SOURCE_POLICY.md` |
| `aoa-discord-connector` | `kag/` | `connector/SOURCE_POLICY.md` |
| `aoa-stackoverflow-connector` | `kag/` | `connector/SOURCE_POLICY.md` |
| `aoa-telegram-connector` | `kag/` | `connector/SOURCE_POLICY.md` |
| `aoa-xda-connector` | `kag/` | `connector/SOURCE_POLICY.md` |

All homes expose the same record classes while returning to their own source
owners.

## Consumer Route

`aoa-kag` composes provider packets into a verified federation bundle.
`abyss-stack` materializes runtime search and graph projections. `aoa-kag-mcp`
serves the shared `discover`, `search`, `read`, `traverse`, and `explain`
contract from canonical owner records and those runtime projections.

`generated/local_kag_provider_map.min.json#/mcp_handoff` is the machine route
for the five tools, nine `aoa-kag://` resource shapes, owner boundaries, and
runtime owner. The result and capability envelopes live in
`schemas/kag-mcp-result.schema.json` and
`schemas/kag-mcp-capabilities.schema.json`.
