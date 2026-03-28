# Cross-Source Node Projection

This document records the current fifth-wave bounded cross-source node
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
- `Tree-of-Sophia/generated/kag_export.min.json`
- `generated/tos_retrieval_axis_pack.min.json`
- `generated/federation_spine.min.json`

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
`manifests/cross_source_node_projection.json` under `projection_pairings`.
That keeps the bounded one-hop pairing reviewable instead of leaving it hidden
inside generator code.

## Current pilot surfaces

The current pilot surfaces are:

- `schemas/cross-source-node-projection.schema.json`
- `examples/cross_source_node_projection.example.json`
- `manifests/cross_source_node_projection.json`
- `generated/cross_source_node_projection.json`
- `generated/cross_source_node_projection.min.json`

## What this wave does not do

This wave does not:

- activate counterpart edges
- widen into many-hop graph expansion
- claim ontology merger
- move routing ownership into `aoa-kag`
- replace source-owned exports

## Regeneration posture

Use:

```bash
python scripts/release_check.py
```

For the current deferred counterpart posture, see
`COUNTERPART_CONSUMER_CONTRACT.md` and
`COUNTERPART_EDGE_CONTRACTS.md#activation-gates`.

The current projection is also explicitly covered by
`COUNTERPART_FEDERATION_EXPOSURE_REVIEW.md` so its non-identity posture remains
reviewable without implying counterpart activation.
