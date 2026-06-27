# Provider Map MCP Handoff

## Index Metadata

- Decision ID: AOA-KAG-D-0011
- Original date: 2026-06-27
- Surface classes: kag/source-home, generated readmodel, validation guard, sibling provider homes, MCP handoff
- KAG surfaces: local KAG provider map, provider packet, readiness matrix, source-return projection, MCP resource shape
- Source lanes: aoa-kag, Agents-of-Abyss, Tree-of-Sophia, aoa-techniques, aoa-skills, aoa-agents, aoa-playbooks, aoa-memo, aoa-evals, aoa-routing, aoa-sdk, abyss-stack
- Guard families: source-owned authority, provider readiness, source-return route, generated parity, MCP handoff, runtime-state boundary
- Posture: accepted

## Context

AOA-KAG-D-0010 activated the local KAG provider contract with `aoa-kag`,
`Tree-of-Sophia`, and `aoa-techniques` as the first provider-ready homes.
Preparing `aoa-kag-mcp` now requires the broader source-ready organ layer to be
available as validated provider packets and as a compact handoff read model.

The current provider expansion covers:

- center doctrine and ecosystem registry in `Agents-of-Abyss/kag/`;
- canonical skill graph in `aoa-skills/kag/`;
- role and capability surfaces in `aoa-agents/kag/`;
- scenario and playbook registry surfaces in `aoa-playbooks/kag/`;
- memory registry and reviewed corpus route in `aoa-memo/kag/`;
- proof bundle and report-index route in `aoa-evals/kag/`;
- routing source-home and cross-repo route registry in `aoa-routing/kag/`;
- SDK source-home and typed KAG helper route in `aoa-sdk/kag/`.

## Decision

Source-ready OS Abyss repos become provider-ready only when they carry a real
local `kag/` packet with manifest, node, edge, index, projection, and receipt
records.

`aoa-kag` also publishes `generated/local_kag_provider_map.json` and
`generated/local_kag_provider_map.min.json` from
`manifests/local_kag_readiness.json` and validated provider homes. This read
model is the handoff packet for `aoa-kag-mcp`: it names provider manifests,
record coverage, owner-return routes, OS surface rows, resource URI templates,
root boundaries, tool names, prompt names, and the expected
`abyss-stack/mcp/services/aoa-kag-mcp` package route.

## Options Considered

- Let `aoa-kag-mcp` scan every repo at runtime: flexible, but it repeats source
  topology work inside the access plane.
- Keep only `manifests/local_kag_readiness.json`: compact, but it lacks checked
  provider record counts and exact MCP handoff planes.
- Publish a generated provider map from readiness plus provider homes: keeps
  source ownership local, gives MCP one compact entrypoint, and lets validation
  catch provider drift before runtime.

## Rationale

The chosen route keeps the owner split clear.

Repo-local `kag/` homes own portable records and source-return handles for their
own source surfaces. `aoa-kag` owns the shared schema, readiness matrix,
generated provider map, and validation contract. `abyss-stack` remains the
runnable MCP service owner.

This prevents the MCP layer from becoming a second source of KAG topology while
still giving agents a direct resource/root/tool/prompt map.

## Consequences

- `manifests/local_kag_readiness.json` now treats the source-ready organ repos
  as provider-ready.
- `scripts/validators/local_kag_subtree.py` requires the full source-ready
  provider set and validates each provider home when the checkout is present.
- `scripts/generate_kag.py` emits the provider map alongside the root KAG
  registry outputs.
- `generated/local_kag_provider_map.min.json` becomes the compact entrypoint for
  future `aoa-kag-mcp` implementation.
- Runtime graph, vector, embedding, cache, and serving state remain outside Git
  with runtime owners.
- Source-preparation and runtime-consumer rows stay visible in the provider map
  as remaining routes, not as empty provider homes.

## Source Surfaces

- `kag/README.md`
- `kag/LOCAL_SUBTREE_PROTOCOL.md`
- `kag/source_home.manifest.json`
- `kag/projections/mcp_contract_resource.json`
- `manifests/local_kag_readiness.json`
- `generated/local_kag_provider_map.json`
- `generated/local_kag_provider_map.min.json`
- `scripts/generation/provider_map.py`
- `scripts/validators/local_kag_subtree.py`
- `tests/test_kag_generation.py`
- `tests/test_validate_kag.py`
- sibling `kag/` provider homes listed in the context section

## Validation

Use `docs/validation/COMMAND_AUTHORITY.md` and the nearest `AGENTS.md` for executable validation commands.

The route is validated by the local KAG provider validator, generated parity,
decision-record validation, and the touched provider owner gates.
