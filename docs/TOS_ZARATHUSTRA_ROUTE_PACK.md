# ToS Zarathustra Route Pack

This document records the first direct canonical-tree-derived Zarathustra route
pack at the KAG layer.

It materializes one bounded route-local bundle for
`thus-spoke-zarathustra/prologue-1` without widening the older tiny-entry pilot
surfaces and without activating raw-table intake.

## Core rule

The route pack is a derived carrier, not a second canon.

`aoa-kag` may derive one route-local bundle from canonical `Tree-of-Sophia`
tree surfaces plus the canonical ToS relation pack, but the resulting payload
must remain explicitly subordinate to those stronger authored surfaces.

## Current pilot inputs

The current pilot derives only from canonical ToS route surfaces:

- the canonical source node for Zarathustra `prologue-1`
- the canonical `becoming` and `overcoming` concept nodes
- the canonical route-local lineage node
- the route-local `principle`, `event`, `state`, `support`, `analogy`, and
  `synthesis` family roots
- the canonical route-local relation pack
- the Zarathustra route capsule doc

This wave does not derive from:

- `Tree-of-Sophia/intake/**`
- `Tree-of-Sophia/examples/**`
- `Tree-of-Sophia/generated/kag_export*`

## Pack rule

The current pack keeps:

- one bounded `route_id`
- one explicit `route_capsule_ref`
- one explicit `relation_pack_ref`
- one ordered node bundle with authority refs back to exact ToS `tree/**`
  surfaces
- one ordered edge bundle copied from the canonical ToS relation pack
- node and edge counts that remain reviewable at the pack level

This keeps the pack route-local, canonical-tree-derived, and provenance-visible
without pretending that `aoa-kag` now owns Zarathustra meaning.

The route pack itself still keeps `consumer_projection = deferred` in its own
bounded contract. The first bounded consumer-facing activation now lives
separately in `AOA-K-0011`, which reads the route pack as one standalone
handles-only retrieval adjunct rather than widening the pack itself into a
ranked or routing-bearing surface.

## Current pilot surfaces

The current pilot surfaces are:

- `schemas/tos-zarathustra-route-pack-manifest.schema.json`
- `schemas/tos-zarathustra-route-pack.schema.json`
- `examples/tos_zarathustra_route_pack.example.json`
- `manifests/tos_zarathustra_route_pack.json`
- `generated/tos_zarathustra_route_pack.json`
- `generated/tos_zarathustra_route_pack.min.json`

## What this wave does not do

This wave does not:

- widen `AOA-K-0005` or `AOA-K-0007`
- activate raw-table candidate intake from `Tree-of-Sophia/intake/**`
- replace the current tiny-entry pilot surfaces
- add consumer-facing retrieval ranking or routing policy inside `AOA-K-0010`
- grant graph sovereignty to the KAG layer

## Regeneration posture

Use:

```bash
python scripts/generate_kag.py
python scripts/validate_kag.py
```

If `Tree-of-Sophia` is not checked out beside this repository, point the
scripts at it with `TREE_OF_SOPHIA_ROOT`.
