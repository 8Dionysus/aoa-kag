# Local KAG Provider Activation

## Index Metadata

- Decision ID: AOA-KAG-D-0010
- Original date: 2026-06-26
- Surface classes: kag/source-home, schemas, examples, manifests, validation guard, sibling provider homes, OS surface layer, docs/decisions
- KAG surfaces: local KAG subtree contract, provider packet, direct repo readiness, OS surface readiness, MCP access shape, registry/composition input
- Source lanes: aoa-kag, Tree-of-Sophia, aoa-techniques, abyss-stack, abyss-machine, aoa-session-memory, connectors, .aoa, .agents
- Guard families: source-owned authority, local provider validation, owner-return route, runtime-state boundary, registry readiness, MCP resource shape
- Posture: accepted

## Context

AOA-KAG-D-0004 and AOA-KAG-D-0007 established the pressure for repo-local KAG
subtrees and gave `aoa-kag/kag/` a source-home route. That was enough to prevent
template copying, but it left the OS Abyss graph forest without a concrete
portable provider packet.

The current work adds the missing contract surfaces:

- `schemas/local-kag-subtree.schema.json`
- `examples/local_kag_subtree.example.json`
- `manifests/local_kag_readiness.json`
- `scripts/validators/local_kag_subtree.py`
- active provider records under `aoa-kag/kag/`
- first sibling provider homes under `Tree-of-Sophia/kag/` and `aoa-techniques/kag/`
- OS surface readiness rows for runtime source repos, runtime mirror, organ
  homes, bundle homes, and connector repos

## Decision

`aoa-kag/kag/` becomes an active protocol and provider home.

The shared repo-local KAG contract uses one manifest plus five record classes:
node, edge, index, projection, and receipt. Provider-ready repositories expose
those classes under a local `kag/` home, with source refs, freshness posture,
owner-return routes, validation routes, storage posture, and MCP access shape.

The first provider-ready homes are:

| Repository | Home | First source route |
| --- | --- | --- |
| `aoa-kag` | `kag/` | local subtree schema and readiness matrix |
| `Tree-of-Sophia` | `kag/` | `ToS/derived-exports/kag_export.min.json` |
| `aoa-techniques` | `kag/` | `generated/kag_export.min.json` and `AOA-T-0043` |

`manifests/local_kag_readiness.json` is the adoption-order and provider status
map for every direct OS Abyss repository and the surrounding OS surface layer.
The OS surface layer covers runtime source repos, the runtime mirror, organ
homes, bundle homes, collection homes, and connector repos.

## Options Considered

- Keep `kag/` as protocol text only: simple, but it leaves MCP and runtime
  consumers without a real packet shape.
- Build only `aoa-kag` local records: validates the contract owner, but leaves
  sibling readiness unproven.
- Activate `aoa-kag`, `Tree-of-Sophia`, and `aoa-techniques` together: gives
  the contract one owner packet, one ToS source-export packet, and one technique
  source-export packet.
- Add direct repo and OS surface readiness to the same matrix: gives MCP and
  runtime consumers one route for source repos, connectors, bundles, organs, and
  host/runtime stack surfaces.

## Rationale

The chosen route proves the topology across three different source postures:

- `aoa-kag` owns schema, readiness, validation, and composition law;
- `Tree-of-Sophia` owns source-first philosophical export surfaces;
- `aoa-techniques` owns reusable technique source-lift export surfaces.

This gives future `aoa-kag-mcp` a concrete access contract: resources and roots
can read provider manifests and records; tools can validate, check freshness,
and follow owner-return routes; prompts can stay bounded to validated provider
records.

## Consequences

- Provider-ready rows now require real local `kag/` packets when the sibling
  checkout is present.
- `aoa-kag` validation checks manifest and record JSON against the shared schema
  definitions and verifies local source refs.
- The readiness validator checks the direct repo set, the OS surface set, the
  connector repo set, and the filesystem roots named by OS surface rows.
- Runtime serving state remains downstream in `abyss-stack` or `.aoa`; Git
  carries compact provider records and receipts.
- Candidate repositories keep exact source surfaces and adoption order in the
  readiness matrix until their owner route can supply all record classes.
- D-0007 remains the rationale for creating the source home; this decision
  records its activation into a provider contract.

## Source Surfaces

- `kag/AGENTS.md`
- `kag/README.md`
- `kag/LOCAL_SUBTREE_PROTOCOL.md`
- `kag/source_home.manifest.json`
- `kag/manifest.json`
- `kag/nodes/`
- `kag/edges/`
- `kag/indexes/`
- `kag/projections/`
- `kag/receipts/`
- `schemas/local-kag-subtree.schema.json`
- `examples/local_kag_subtree.example.json`
- `manifests/local_kag_readiness.json`
- `scripts/validators/local_kag_subtree.py`
- `tests/test_kag_home.py`
- `tests/test_validate_kag.py`
- `Tree-of-Sophia/kag/`
- `aoa-techniques/kag/`
- `/home/dionysus/src/abyss-stack`
- `/home/dionysus/src/abyss-machine`
- `/srv/AbyssOS/.aoa`
- `/srv/AbyssOS/.agents`
- `/srv/AbyssOS/bundles/aoa-session-memory`
- `/srv/AbyssOS/connectors/`

## Validation

Use `docs/validation/COMMAND_AUTHORITY.md` and the nearest `AGENTS.md` for executable validation commands.

The activation is validated by the repo release lane and the provider-ready
sibling release lanes.
