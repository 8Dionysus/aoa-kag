# Repo-Local Source Surface Index

## Index Metadata

- Decision ID: AOA-KAG-D-0013
- Original date: 2026-06-28
- Surface classes: kag/source-home, schema contract, generated readmodel, validation guard, MCP handoff
- KAG surfaces: repo-local source surface index, OS Abyss coverage report, document records, mechanics records, command records, provenance posture
- Source lanes: aoa-kag, OS Abyss repo-local kag homes, connectors, bundles
- Guard families: source-owned authority, repo-local index atom, document coverage, mechanics coverage, command coverage, ABI posture, provenance posture, generated parity, MCP handoff
- Posture: accepted

## Context

AOA-KAG-D-0010 through AOA-KAG-D-0012 activated local KAG provider packets and
the generated provider map for `aoa-kag-mcp`. That gave the MCP layer a
provider-ready route, but the repo-local index records were still lightweight
provider inventories. They did not yet expose the broader source/document/
artifact atom needed before graph extraction.

OS Abyss needs a first indexing layer that can classify ordinary files, route
docs, decisions, mechanics, scripts, tests, validators, schemas, generated
read models, receipts, and unknown/candidate surfaces before graph/KAG
relationship extraction.

## Decision

`aoa-kag` adds a repo-local source surface index contract:

- `schemas/repo-local-kag-index.schema.json`
- `examples/repo_local_kag_index.example.json`
- `scripts/generate_repo_local_kag_index.py`
- `scripts/validators/repo_local_kag_index.py`
- `kag/indexes/source_surface_index.json`

The index atom carries identity, observed form, surface state, artifact role,
document role, code role, mechanics role, command role, ABI posture, signs,
provenance, toolchain, classification, freshness, access, source coordinates,
owner-return route, validator route, and MCP consumer route.

`aoa-kag` also adds an OS Abyss coverage report:

- `schemas/repo-local-kag-coverage.schema.json`
- `scripts/generate_repo_local_kag_coverage.py`
- `generated/repo_local_kag_coverage.json`
- `generated/repo_local_kag_coverage.min.json`

The coverage report gives every discovered owner a status:
`passed`, `migration-needed`, `missing`, or `owner-specific`.

## Options Considered

- Keep only lightweight provider inventory records: preserves the existing
  provider packet shape, but leaves document/mechanics/command coverage outside
  a checkable contract.
- Move directly to graph extraction: creates relation pressure before stable
  source coordinates, digests, ABI posture, and provenance are available.
- Add a repo-local source surface index foundation: gives each owner a stable
  index atom and gives future graph/KAG/MCP layers a validated input.

## Rationale

The chosen route makes indexing the first durable layer before graph work.
Markdown documents become first-class records with heading coordinates. Mechanics
surfaces, commands, validators, tests, scripts, schemas, generated read models,
and receipts all receive owner routes and validation routes.

The index is source-return oriented. It gives `aoa-kag-mcp` stable resources and
coordinates while preserving the stronger owner surface for meaning changes.

## Consequences

- `kag/indexes/source_surface_index.json` becomes the repo-local source surface
  index for `aoa-kag`.
- Existing sibling `source_surface_index.json` files can move through
  `migration-needed` coverage status until their owners adopt the new atom.
- Generated parity now includes the source surface index and OS-wide coverage
  report.
- Graph/KAG extraction can consume stable IDs, digests, heading refs,
  provenance, ABI posture, and owner routes as input.
- Future `aoa-kag-mcp` can expose repo-local index resources through the same
  contract.

## Source Surfaces

- `schemas/repo-local-kag-index.schema.json`
- `schemas/repo-local-kag-coverage.schema.json`
- `examples/repo_local_kag_index.example.json`
- `scripts/generate_repo_local_kag_index.py`
- `scripts/generate_repo_local_kag_coverage.py`
- `scripts/validators/repo_local_kag_index.py`
- `kag/indexes/source_surface_index.json`
- `generated/repo_local_kag_coverage.json`
- `generated/repo_local_kag_coverage.min.json`
- `tests/test_repo_local_kag_index.py`
- `config/validation_lanes.json`
- `docs/validation/SCRIPT_TOPOLOGY.md`
- `docs/validation/VALIDATOR_TOPOLOGY.md`

## Validation

Use `docs/validation/COMMAND_AUTHORITY.md` and the nearest `AGENTS.md` for executable validation commands.

The route is validated by repo-local index tests, JSON schema checks,
`scripts/validate_kag.py`, generated parity, decision index generation, and the
source-fast lane.
