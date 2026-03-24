# AoA-ToS Bridge Contracts

This document records the first-wave bridge posture at the KAG layer.
It is the primary coordination note for the Dionysus seed
`archive/seed_rootline/seed.8dionysus.aoa-shared.bridges.md`.

It does not replace ToS ontology, memory contracts, or runtime implementation.
It names the derived bridge surfaces that make AoA-ToS exchange explicit.

## Coordination surfaces

The current explicit bridge home is split like this:

- this document is the primary coordination note for the first-wave bridge seed
- `schemas/bridge-retrieval-surface.schema.json` and `examples/tos_retrieval_axis_surface.example.json` define the KAG-side retrieval contract
- `aoa-memo/docs/KAG_TOS_BRIDGE_CONTRACT.md` defines the memo-side writeback and export companion contract
- `aoa-routing/docs/FEDERATION_ENTRY_ABI.md` defines the orientation-only entry companion and does not become bridge authority

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

## Retrieval axis contract

When KAG returns a bridge-ready retrieval surface, it should be able to expose:

- source refs
- lineage refs
- conflict refs where relevant
- practice refs where relevant
- bounded axis summary

This keeps retrieval richer than a similarity dump while still remaining derived and reviewable.

See `examples/tos_retrieval_axis_surface.example.json` for a compact bridge-ready example tied to `AOA-K-0007`.
The schema-backed contract for that surface is `schemas/bridge-retrieval-surface.schema.json`.

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
