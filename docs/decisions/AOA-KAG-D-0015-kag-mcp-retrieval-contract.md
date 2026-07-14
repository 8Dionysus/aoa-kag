# KAG MCP Retrieval Contract

## Index Metadata

- Decision ID: AOA-KAG-D-0015
- Original date: 2026-07-14
- Surface classes: kag/source-home, schema contract, generated readmodel, MCP handoff
- KAG surfaces: capability discovery, result envelope, qualified resources, retrieval ABI, provenance
- Source lanes: aoa-kag, OS Abyss repo-local kag homes, abyss-stack
- Guard families: owner namespace, source return, extensible kind, access isolation, bounded context, canonical fallback
- Posture: accepted

## Context

`AOA-KAG-D-0011` established the generated provider map before a real retrieval
service existed. Its per-provider resource/root/tool/prompt hints mixed owner
containment with MCP surface planning and could not express runtime strategy,
degradation, evidence, pagination, or projection state.

Laboratory use across realistic repositories compared a broad provider-tool
catalog, five stable KAG operations, and dynamic progressive tool discovery.
The same trials exercised owner collisions, unknown kinds, source changes,
conflicting claims, graph cycles, access scopes, hostile indexed text, and
degraded runtime projections.

## Decision

The KAG MCP contract consists of five operations: `kag_discover`, `kag_search`,
`kag_read`, `kag_traverse`, and `kag_explain`.

`schemas/kag-mcp-capabilities.schema.json` owns capability discovery.
`schemas/kag-mcp-result.schema.json` owns the result envelope, including
qualified identity, extensible kind, owner, source anchors, provenance, trust,
temporal and freshness state, ABI/signs, access, strategy, score, projection,
trace, resources, pagination, and degradation.

The generated provider map owns exact tool names, nine resource templates,
owner-containment boundaries, and the `abyss-stack` runtime route under
`mcp_handoff`. Provider readiness describes sources and ownership; the handoff
describes the executable MCP ABI.

## Options Considered

- Add one MCP tool for every provider-map lookup and runtime strategy.
- Keep five storage-neutral KAG operations and expand kinds through data and
  capabilities.
- Discover temporary tool names dynamically for each owner and backend.

## Rationale

Five stable operations produced the clearest agent route with the lowest
schema and retry cost. Qualified resources and three detail levels provided
progressive disclosure without changing tool names. New classes remain
compatible through base `record_class` plus extensible `kind`.

This split keeps canonical records with repositories, shared semantics with
`aoa-kag`, and mutable serving state with `abyss-stack`. Prompt content cannot
change tool metadata or access policy, and runtime degradation can return to
canonical owner records without changing the ABI.

## Consequences

- Provider-map lookup operations become internal composition inputs rather
  than public MCP tools.
- MCP Roots are client-owned; provider roots remain explicit containment
  metadata in the handoff.
- The current access plane publishes no prompts because resources and detail
  levels cover the measured scenarios.
- New owners, record classes, kinds, and backend implementations extend data
  and capabilities while the five-tool surface remains stable.

## Source Surfaces

- `schemas/kag-mcp-capabilities.schema.json`
- `schemas/kag-mcp-result.schema.json`
- `examples/kag_mcp_capabilities.example.json`
- `examples/kag_mcp_result.example.json`
- `scripts/generation/provider_map.py`
- `scripts/validators/repo_local_kag_index.py`
- `generated/local_kag_provider_map.min.json`
- `kag/LOCAL_SUBTREE_PROTOCOL.md`
- `abyss-stack:mcp/services/aoa-kag-mcp/`
- `abyss-stack:mechanics/federation-seams/parts/kag-seam/`

## Validation

Validation follows `docs/validation/COMMAND_AUTHORITY.md`, the provider-map
handoff validator, public schema examples, runtime application tests, and real
MCP client trajectories.
