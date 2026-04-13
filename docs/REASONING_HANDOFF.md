# Reasoning Handoff

This document defines the bounded runtime-to-KAG reasoning handoff seam for
`aoa-kag`.

The KAG layer may accept a retrieval or reasoning handoff from a runtime.
It returns derived guidance-to-source rather than a new source of truth.

## Source seed

Source seed ref:

- `Dionysus/seed_expansion/seed.aoa.agents-runtime-pack.v0.md#aoa-seed-r5-kag-reasoning-handoff`

## Core rule

`aoa-kag` may support a reasoning substrate for runtime handoff.

It does this by returning:

- bounded retrieval context
- provenance-aware source handles
- derived surface links that guide the caller back to stronger sources

It does not:

- own routing
- own memory truth
- author canon directly
- collapse AoA and ToS into one hidden layer

## Query modes

### `local_search`

Use `local_search` when the runtime needs bounded entity, section, or fragment
retrieval from already-known neighborhoods.

This mode should return compact source-linked context rather than a broad
architectural synthesis.

### `global_search`

Use `global_search` when the runtime needs wider synthesis, axis-level
architectonics, or a more global reasoning substrate across source-linked
surfaces.

This mode should still return guidance-to-source rather than an authored
replacement for source meaning.

### `drift_search`

Use `drift_search` when the runtime is exploring unexpected links, oblique
relations, or possible bridges that are not obvious from a narrow local query.

This mode is explicitly exploratory.
It should surface provenance and non-identity boundaries instead of pretending
that every discovered bridge is settled meaning.

## Return posture

Every reasoning handoff should be able to return:

- `source_refs`
- `axis_summary`
- `provenance_note`

It may also return:

- `lineage_refs`
- `conflict_refs`
- `practice_refs`
- `counterpart_refs`

These returns stay derived.
They should guide the caller toward stronger authored sources and existing
KAG-layer derived surfaces, not silently replace either.

When runtime use loses source trace, blurs non-identity posture, or reaches a
clear owner boundary, prefer a bounded regrounding return through
`generated/return_regrounding_pack.min.json` rather than a wider KAG-authored
continuation.

When the pressure is Agon-shaped memory readiness, including scar, retention, or
live memory-ledger questions, the stronger owner ref is
`aoa-memo/docs/PRE_AGON_MEMORY_READINESS.md`. KAG may return that ref, but it
must not turn the handoff into scar proof, retention policy, or live memory
state.

When `counterpart_refs` are returned in the current wave, they must stay
contract-or-example refs through:

- `docs/COUNTERPART_CONSUMER_CONTRACT.md`
- `examples/counterpart_consumer_contract.example.json`
- `docs/COUNTERPART_FEDERATION_EXPOSURE_REVIEW.md`

They may not point to a generated `AOA-K-0008` payload, because `AOA-K-0008`
remains planned.

## Boundary guardrails

- `aoa-routing` owns navigation and dispatch
- `aoa-memo` owns memory truth and writeback doctrine
- `Tree-of-Sophia` owns canon and source-authored meaning
- `aoa-kag` owns provenance-aware derived surface returns
- direct canon authorship from a KAG handoff is forbidden
- recurrence at this layer means regrounding back to stronger refs, not taking
  ownership of the next layer's decision
- pre-Agon memory readiness, scar, retention, and live-ledger pressure return to
  `aoa-memo`; they do not become KAG graph or routing readiness

This preserves the current law of the layer:

`AoA acts. ToS remembers. aoa-kag derives.`

## Existing bridge surfaces

The current handoff seam should reuse and respect the existing bridge surfaces:

- `docs/BRIDGE_CONTRACTS.md`
- `examples/tos_retrieval_axis_surface.example.json`
- `docs/COUNTERPART_EDGE_CONTRACTS.md`
- `docs/COUNTERPART_CONSUMER_CONTRACT.md`
- `docs/COUNTERPART_FEDERATION_EXPOSURE_REVIEW.md`
- `examples/counterpart_edge_view.example.json`
- `examples/counterpart_consumer_contract.example.json`

The reasoning handoff guardrail exists to keep those surfaces usable at runtime
without promoting them into a second canon.

## Reference scenarios

Reference scenarios only:

- `AOA-P-0008 long-horizon-model-tier-orchestra`
- `AOA-P-0009 restartable-inquiry-loop`

These scenarios may ask for KAG support.
They do not become KAG-owned scenario contracts here.

## Non-goals

- no routing ownership in `aoa-kag`
- no direct canon authorship from derived retrieval
- no implicit AoA and ToS collapse
- no hidden graph sovereignty
- no framework-specific runtime commitment
