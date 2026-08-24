# AOA-KAG-D-0044 Cold CAS Evidence-Ref Exact Search

## Index Metadata

- Decision ID: AOA-KAG-D-0044
- Original date: 2026-08-24
- Surface classes: query contract, tiered delivery, public projection
- KAG surfaces: v4 cold-CAS loading, exact search, projection handles
- Source lanes: aoa-kag, abyss-stack
- Guard families: source-owned authority, fail-closed delivery, public-safe projection
- Posture: accepted

## Context

The canonical `aoa-kag` query contract already supports a v4 family assembled
from Git-hot records and an owner-approved cold CAS, but the MCP consumer did
not pass the configured artifact root into that contract. The event index also
retained immutable `evidence_refs` while the query node and projection-handle
surfaces omitted them from exact-match fields and public handles.

## Decision

Keep the v4 artifact root as an authored, optional `aoa-kag` consumer
configuration. When it is present, the canonical adapter passes it to
`load_family` and disables shadow-Git fallback; when absent, legacy owner
behavior remains available. Extend event exact matching with the existing
public `kind`/`ref` coordinates and carry only those coordinates into the
projection handle.

Dashboard readiness remains a bounded exact path lookup over the generated
provider-map surface. It does not promote a `source_preparation` owner to
`provider_ready`, and an artifact trust verdict remains owned by the artifact
policy route.

## Options Considered

- Bind a deployed Configs copy directly: rejected because runtime mirrors are
  not source authority.
- Rebuild or duplicate a parallel CAS/indexer: rejected because the owner
  route already defines v4 delivery and duplicate state would weaken identity.
- Add an authored consumer seam and preserve the existing event references:
  chosen.

## Rationale

`aoa-kag` owns the derived query schema and index shape. `abyss-stack` owns the
read-only adapter and service configuration path. Keeping those seams narrow
preserves the source/generated/installed/runtime claim boundary and avoids
adding private payload fields to a public KAG handle.

## Consequences

- A configured cold root is fail-closed against shadow-Git substitution.
- Exact immutable commit references and exact generated readiness paths are
  addressable through the same owner query contract.
- Current source/projection, artifact admission, runtime delivery, and human
  acceptance remain separate claims.

## Source Surfaces

- `scripts/repo_local/query.py`
- `schemas/repo-local-kag-federation.schema.json`
- `mcp/services/aoa-kag-mcp/` in the consumer owner
- `CHANGELOG.md`

## Validation

Run the owner family validator, focused query tests, and the consumer MCP
validator/test suite. Rebuild the existing canonical projection through the
owner sync route and verify exact event-reference and readiness-path queries
with source and projection digests.
