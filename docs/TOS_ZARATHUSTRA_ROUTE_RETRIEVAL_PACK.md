# ToS Zarathustra Route Retrieval Pack

This document records `AOA-K-0011`, the first standalone consumer-facing
retrieval surface derived from the canonical-tree-derived Zarathustra route
pack.

It materializes one handles-only retrieval adjunct for
`thus-spoke-zarathustra/prologue-1` without widening the numbered tiny consumer
path and without taking routing ownership.

## Core rule

The retrieval pack returns handles back to ToS authority; it does not replace
that authority.

`aoa-kag` may derive one bounded route-local retrieval surface from
`generated/tos_zarathustra_route_pack.min.json`, but that surface must remain a
consumer-facing adjunct that points readers back toward canonical
`Tree-of-Sophia/tree/**` node ownership and the canonical ToS relation pack.

## Current pilot inputs

The current pilot derives only from:

- `generated/tos_zarathustra_route_pack.min.json`

This wave does not derive from:

- `Tree-of-Sophia/intake/**`
- `aoa-memo/**`
- `aoa-routing/**`
- widened `AOA-K-0005` or `AOA-K-0007` donors

## Retrieval rule

The current retrieval rule is:

- one retrieval route object for the bounded Zarathustra `prologue-1` route
- preserve the canonical `route_id`
- preserve `route_pack_ref`, `route_capsule_ref`, and `relation_pack_ref`
- preserve `node_type_counts` and `edge_kind_counts` from `AOA-K-0010`
- return family-level handle arrays only
- keep each handle item limited to `node_id` plus `authority_ref`
- keep one bounded `retrieval_summary`
- add no ranking, scoring, path bundles, query cards, or routing hints

## Current pilot surfaces

The current pilot surfaces are:

- `schemas/tos-zarathustra-route-retrieval-pack-manifest.schema.json`
- `schemas/tos-zarathustra-route-retrieval-pack.schema.json`
- `examples/tos_zarathustra_route_retrieval_pack.example.json`
- `manifests/tos_zarathustra_route_retrieval_pack.json`
- `generated/tos_zarathustra_route_retrieval_pack.json`
- `generated/tos_zarathustra_route_retrieval_pack.min.json`

## What this wave does not do

This wave does not:

- replace `AOA-K-0005` or `AOA-K-0007`
- join the numbered recommended consumer path yet
- add segment entrypoints or thematic bundles
- rank sources, nodes, or route families
- widen into routing policy or graph normalization
- replace ToS route-pack authority with KAG-owned summaries

## Regeneration posture

Use:

```bash
python scripts/generate_kag.py
python scripts/validate_kag.py
```
