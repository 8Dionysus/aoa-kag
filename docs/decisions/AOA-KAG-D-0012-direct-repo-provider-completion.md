# Direct Repo Provider Completion

## Index Metadata

- Decision ID: AOA-KAG-D-0012
- Original date: 2026-06-28
- Surface classes: kag/source-home, sibling provider homes, generated readmodel, validation guard, MCP handoff
- KAG surfaces: local KAG provider map, readiness matrix, provider packet, source-return projection, freshness handles
- Source lanes: aoa-kag, 8Dionysus, Dionysus, ATM10-Agent, aoa-stats, abyss-stack
- Guard families: source-owned authority, provider readiness, source-return route, freshness handle, generated parity, MCP handoff, runtime-state boundary
- Posture: accepted

## Context

AOA-KAG-D-0011 made `generated/local_kag_provider_map.min.json` the compact
handoff packet for `aoa-kag-mcp`, but four direct OS Abyss repositories still
remained outside the provider-ready set: `8Dionysus`, `Dionysus`,
`ATM10-Agent`, and `aoa-stats`.

Leaving these rows as source-preparation or runtime-consumer entries would make
the first `aoa-kag-mcp` implementation carry too much topology judgment at
runtime. The provider map needs to be a complete access foundation for direct
repo roots, with runtime/collection surfaces handled separately through
`os_surfaces`.

## Decision

All direct OS Abyss repository rows in `manifests/local_kag_readiness.json` now
become provider-ready when their source route is present in the local workspace
and they expose a real repo-local `kag/` packet with manifest, node, edge,
index, projection, and receipt records.

The completion adds provider homes for `8Dionysus`, `Dionysus`, `ATM10-Agent`,
and `aoa-stats`. `ATM10-Agent` keeps its project-local runtime identity, but
its `kag/` packet gives `aoa-kag-mcp` source-return handles to the project
runbook and KAG runtime modules instead of making the MCP layer infer them.

`generated/local_kag_provider_map.json` also carries explicit
`provider_status` and `freshness_handles` for provider rows. MCP consumers can
read status and freshness routes from the provider map before deciding whether
to inspect provider records directly.

## Options Considered

- Keep the four rows as remaining routes: preserves the previous matrix shape,
  but leaves direct-repo topology work for the MCP service.
- Promote only the three source-preparation rows: keeps `ATM10-Agent` as a
  pure runtime-consumer row, but leaves one direct repo without a root provider
  packet despite its project-local KAG source route.
- Complete direct repo provider coverage: keeps runtime and source meanings
  with their owners while giving the MCP layer one complete direct-repo
  provider map.

## Rationale

The chosen route keeps the owner split clear.

Repo-local `kag/` homes own portable records and source-return handles for their
own source surfaces. `aoa-kag` owns the shared schema, readiness matrix,
generated provider map, freshness-handle projection, and validation contract.
`abyss-stack` remains the runnable MCP service owner.

This prevents `aoa-kag-mcp` from becoming a topology crawler while still
preserving source-return paths to the stronger owner surfaces.

## Consequences

- Direct OS Abyss repo rows now have complete provider packets.
- `remaining_routes` in the provider map is reserved for future non-provider
  repo rows rather than current direct-repo debt.
- Compatibility canary must checkout the full provider-ready sibling set.
- Provider map consumers can inspect status and freshness handles without
  scanning receipt directories first.
- Runtime graph, vector, embedding, cache, and serving state remain outside Git
  with runtime owners.

## Source Surfaces

- `manifests/local_kag_readiness.json`
- `generated/local_kag_provider_map.json`
- `generated/local_kag_provider_map.min.json`
- `scripts/generation/context.py`
- `scripts/generation/provider_map.py`
- `scripts/validators/local_kag_subtree.py`
- `tests/test_kag_generation.py`
- `tests/test_validate_kag.py`
- `tests/test_kag_home.py`
- `.github/workflows/compatibility-canary.yml`
- sibling `kag/` provider homes in `8Dionysus`, `Dionysus`, `ATM10-Agent`, and `aoa-stats`

## Validation

Use `docs/validation/COMMAND_AUTHORITY.md` and the nearest `AGENTS.md` for executable validation commands.

The route is validated by the local KAG provider validator, generated parity,
decision-record validation, compatibility-canary coverage tests, and touched
provider owner gates.
