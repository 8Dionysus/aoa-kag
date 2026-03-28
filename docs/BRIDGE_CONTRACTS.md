# AoA-ToS Bridge Contracts

This document records the first-wave bridge posture at the KAG layer.

It does not replace ToS ontology, memory contracts, or runtime implementation.
It names the derived bridge surfaces that make AoA-ToS exchange explicit.

## Core rule

AoA acts.
ToS remembers.
`aoa-kag` derives bridge-ready substrate without replacing either side.

## Bridge directions

### ToS and memory into KAG

The KAG layer may derive from:

- ToS source-authored fragments and nodes
- `aoa-memo` bridge-bearing memory objects
- reviewable note surfaces with explicit provenance

Every lift should preserve the path back to the stronger authored source.

When more than one repo contributes to a bridge surface, the KAG registry should preserve:

- top-level `source_class` as the primary semantic class
- `source_inputs` as the full multi-source provenance list
- exactly one `primary` input
- any additional inputs as `supporting`

### KAG back into AoA

The KAG layer may return bounded retrieval surfaces to AoA such as:

- lineage-aware retrieval bundles
- conflict-aware relation views
- practice-aware context bundles
- chunk maps with stable source handles

These returns should guide AoA toward sources.
They should not pretend to be final authored truth.

If bridge use loses source trace or starts treating a derived bridge surface as
final authored meaning, `aoa-kag` should answer with bounded regrounding return
instead of a wider bridge synthesis.

## Retrieval axis contract

When KAG returns a bridge-ready retrieval surface, it should be able to expose:

- source refs
- lineage refs
- conflict refs where relevant
- practice refs where relevant
- bounded axis summary

This keeps retrieval richer than a similarity dump while still remaining derived and reviewable.

See `examples/tos_retrieval_axis_surface.example.json` for a compact bridge-ready example tied to `AOA-K-0007`.
The current generated pack that materializes that same bounded axis posture now
lives at:

- `generated/tos_retrieval_axis_pack.json`
- `generated/tos_retrieval_axis_pack.min.json`
- `docs/TOS_RETRIEVAL_AXIS_PACK.md`

## Shared bridge envelope contract

Strict first-wave closure for the AoA-ToS bridge now uses one shared linkage object:

- `schemas/bridge-envelope.schema.json`
- `examples/aoa_tos_bridge_envelope.example.json`

This envelope is intentionally narrow.
It keeps only:

- `bridge_id`
- `source_class`
- `source_inputs`
- `tos_refs`
- `memory_refs`
- `kag_lift_status`
- `faces`

The envelope does not duplicate retrieval, chunk-face, or graph-face payload bodies.
It links the stronger authored and derived surfaces together so a reviewer can inspect one bounded cross-repo bridge contract without confusing linkage with ownership.

The current example ties together:

- the KAG retrieval face in `examples/tos_retrieval_axis_surface.example.json`
- the memo chunk face in `aoa-memo/examples/memory_chunk_face.bridge.example.json`
- the memo graph face in `aoa-memo/examples/memory_graph_face.bridge.example.json`

## Writeback caution

KAG may support writeback preparation, but it does not own the final authored writeback into ToS or the explicit memory write into `aoa-memo`.

The bridge remains explicit because:

- ToS owns authored source-linked knowledge
- `aoa-memo` owns explicit memory objects
- `aoa-kag` owns the derived bridge substrate

## Anti-goals

Avoid turning bridge contracts into:

- hidden routing logic
- source replacement
- framework lock-in disguised as ontology
- opaque graph sovereignty
