# Cross-Source Node Projection

This document records the current bounded cross-source node
projection posture at the KAG layer.

It materializes the first generated `AOA-K-0006` projection from two real
source-owned federation exports plus the current retrieval-axis and federation
spine surfaces.

## Core rule

A cross-source node projection is a one-hop pairing, not an identity claim.

`aoa-kag` may derive one bounded projection that pairs one primary AoA export
object with one supporting ToS export object, but the projection must keep
provenance explicit and must not collapse the two sources into one canon.

## Current pilot inputs

The current pilot stays deliberately narrow.
It derives only from:

- `aoa-techniques/generated/kag_export.min.json`
- `Tree-of-Sophia/ToS/derived-exports/kag_export.min.json`
- `mechanics/boundary-bridge/parts/tos-retrieval-axis/generated/tos_retrieval_axis_pack.min.json`
- `mechanics/boundary-bridge/parts/federation-spine/generated/federation_spine.min.json`

This keeps the projection grounded in source-owned export capsules and current
bounded KAG surfaces rather than wider graph claims.

## Projection rule

The current projection rule is:

- one primary input and one or more supporting inputs per projection
- preserve `repo`, `export_ref`, `kind`, and `object_id` for every input
- keep one `retrieval_axis_ref`
- keep one `federation_spine_ref`
- keep one bounded `projection_summary`
- keep one explicit `non_identity_boundary`

The current pilot pairing law is declared in
`mechanics/boundary-bridge/parts/cross-source-projection/manifests/cross_source_node_projection.json` under `projection_pairings`.
That keeps the bounded one-hop pairing reviewable instead of leaving it hidden
inside generator code.

## Current pilot surfaces

The current pilot surfaces are:

- `mechanics/boundary-bridge/parts/cross-source-projection/schemas/cross-source-node-projection.schema.json`
- `mechanics/boundary-bridge/parts/cross-source-projection/examples/cross_source_node_projection.example.json`
- `mechanics/boundary-bridge/parts/cross-source-projection/manifests/cross_source_node_projection.json`
- `mechanics/boundary-bridge/parts/cross-source-projection/generated/cross_source_node_projection.json`
- `mechanics/boundary-bridge/parts/cross-source-projection/generated/cross_source_node_projection.min.json`

## What this projection scope does not do

This projection scope does not:

- activate counterpart edges
- widen into many-hop graph expansion
- claim ontology merger
- move routing ownership into `aoa-kag`
- replace source-owned exports

## Regeneration posture

Use `docs/validation/COMMAND_AUTHORITY.md` and the nearest `AGENTS.md` for executable validation commands.

For the current deferred counterpart posture, see
`mechanics/boundary-bridge/parts/counterpart-edge/docs/counterpart-consumer-contract.md`
and
`mechanics/boundary-bridge/parts/counterpart-edge/docs/counterpart-edge-contracts.md#activation-gates`.

The current projection is also explicitly covered by
`mechanics/audit/parts/exposure-review/docs/counterpart-federation-exposure-review.md`
so its non-identity posture remains reviewable without implying counterpart
activation.
