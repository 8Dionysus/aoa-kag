# Documentation Map

This file is the human-first entrypoint for the `docs/` surface of `aoa-kag`.

Use it when you want to understand the AoA KAG layer rather than the broader
federation as a whole.

## Start here

- Read [CHARTER](../CHARTER.md) for the role and boundaries of the KAG layer.
- Read [KAG_MODEL](KAG_MODEL.md) for the conceptual model.
- Read [CONSUMER_GUIDE](CONSUMER_GUIDE.md) for the current narrow consumer path
  through experimental surfaces.
- Read [COUNTERPART_CONSUMER_CONTRACT](COUNTERPART_CONSUMER_CONTRACT.md) for the
  first explicit downstream consumer contract for `counterpart_refs`.
- Read
  [COUNTERPART_FEDERATION_EXPOSURE_REVIEW](COUNTERPART_FEDERATION_EXPOSURE_REVIEW.md)
  for the current review-closed federation posture for `AOA-K-0008` while it
  remains planned.
- Read [FEDERATION_KAG_READINESS](FEDERATION_KAG_READINESS.md) for the first
  public federation export contract.
- Read [FEDERATION_SPINE](FEDERATION_SPINE.md) for the current experimental
  federation spine pilot.
- Read [SOURCE_OWNED_EXPORT_DEPENDENCIES](SOURCE_OWNED_EXPORT_DEPENDENCIES.md)
  for the explicit source-owned export dependency contract.
- Read [BRIDGE_CONTRACTS](BRIDGE_CONTRACTS.md) for the first-wave AoA-ToS bridge
  posture.
- Read [RECURRENCE_REGROUNDING](RECURRENCE_REGROUNDING.md) for the bounded
  recurrence-law landing that regrounds callers back to stronger source or
  owner refs when derived posture weakens.
- Read [KAG_MATURITY_GOVERNANCE](KAG_MATURITY_GOVERNANCE.md) for the rule that
  defines when `aoa-kag` is mature enough to pause widening and wait on owner
  repos.
- Read [KAG_OWNER_WAIT_STATES](KAG_OWNER_WAIT_STATES.md) for the explicit map of
  what `aoa-kag` must still wait on from neighboring layers.
- Read [KAG_PROOF_EXPECTATIONS](KAG_PROOF_EXPECTATIONS.md) for the bounded proof
  lanes that belong in `aoa-evals` rather than inside KAG doctrine.
- Read [KAG_STRESS_REGROUNDING](KAG_STRESS_REGROUNDING.md) for additive
  projection-health and source-first fallback doctrine under drift.
- Read [KAG_PROJECTION_QUARANTINE](KAG_PROJECTION_QUARANTINE.md) for bounded
  quarantine posture when derived surfaces are unsafe to expand.
- Read [KAG_REGROUNDING_CHAOS_WAVE1](KAG_REGROUNDING_CHAOS_WAVE1.md) for the
  retrieval-outage honesty landing over current KAG regrounding surfaces.
- Read [TOS_RETRIEVAL_AXIS_PACK](TOS_RETRIEVAL_AXIS_PACK.md) for the current
  generated retrieval-axis pack.
- Read [REASONING_HANDOFF](REASONING_HANDOFF.md) for the runtime-to-KAG handoff
  boundary.
- Read [TECHNIQUE_LIFT_PACK](TECHNIQUE_LIFT_PACK.md) for the first
  manifest-driven generated lift seam from `aoa-techniques`.
- Read [TOS_TEXT_CHUNK_MAP](TOS_TEXT_CHUNK_MAP.md) for the current ToS chunk-map
  pilot.
- Read [TOS_RAW_TABLE_INTAKE_STUB](TOS_RAW_TABLE_INTAKE_STUB.md) for the current
  non-activated placeholder seam for future ToS raw candidate tables.
- Read [CROSS_SOURCE_NODE_PROJECTION](CROSS_SOURCE_NODE_PROJECTION.md) for the
  current bounded cross-source projection pilot.
- Read [REASONING_HANDOFF_PACK](REASONING_HANDOFF_PACK.md) for the first
  multi-source generated handoff seam for `AOA-P-0008` and `AOA-P-0009`.
- Read [BOUNDARIES](BOUNDARIES.md) for ownership discipline relative to
  neighboring AoA layers.
- Read [SOURCE_POLICY](SOURCE_POLICY.md) for source-first rules.
- Read [ROADMAP](../ROADMAP.md) for the current direction.

## Docs in this repository

- [KAG_MODEL](KAG_MODEL.md) - what the KAG layer is for
- [CONSUMER_GUIDE](CONSUMER_GUIDE.md) - the current narrow consumer path
  through chunk maps, retrieval axes, the federation spine, and bounded
  cross-source projection
- [COUNTERPART_CONSUMER_CONTRACT](COUNTERPART_CONSUMER_CONTRACT.md) - the first
  explicit downstream consumer contract for `counterpart_refs` while
  `AOA-K-0008` remains planned
- [COUNTERPART_FEDERATION_EXPOSURE_REVIEW](COUNTERPART_FEDERATION_EXPOSURE_REVIEW.md)
  - the current review artifact that closes the federation-exposure gate for
  `AOA-K-0008` without promoting it
- [FEDERATION_KAG_READINESS](FEDERATION_KAG_READINESS.md) - the public contract
  for future source-owned federation exports
- [FEDERATION_SPINE](FEDERATION_SPINE.md) - the current experimental federation
  spine pack built from real source-owned tiny exports in `aoa-techniques` and
  `Tree-of-Sophia`
- [SOURCE_OWNED_EXPORT_DEPENDENCIES](SOURCE_OWNED_EXPORT_DEPENDENCIES.md) - the
  explicit contract for the current external source-owned exports consumed by
  `aoa-kag`
- [BRIDGE_CONTRACTS](BRIDGE_CONTRACTS.md) - how the derived layer returns
  retrieval context without replacing authored sources
- [RECURRENCE_REGROUNDING](RECURRENCE_REGROUNDING.md) - how the KAG layer
  regrounds callers back to stronger source-owned and owner-owned refs when a
  derived surface begins to overreach
- [KAG_MATURITY_GOVERNANCE](KAG_MATURITY_GOVERNANCE.md) - how `aoa-kag` defines
  pause-worthy maturity, stability tiers, stop-rules, and donor governance
- [KAG_OWNER_WAIT_STATES](KAG_OWNER_WAIT_STATES.md) - what `aoa-kag` may
  consume now and what must still wait on owner-side growth
- [KAG_PROOF_EXPECTATIONS](KAG_PROOF_EXPECTATIONS.md) - which bounded claims
  should be proven in `aoa-evals` rather than claimed inside KAG
- [KAG_STRESS_REGROUNDING](KAG_STRESS_REGROUNDING.md) - how projection-health
  receipts and regrounding tickets keep consumers source-first when derived
  surfaces drift
- [KAG_PROJECTION_QUARANTINE](KAG_PROJECTION_QUARANTINE.md) - how quarantine
  preserves provenance, fallback refs, and explicit re-entry instead of hiding
  unstable projections
- [KAG_REGROUNDING_CHAOS_WAVE1](KAG_REGROUNDING_CHAOS_WAVE1.md) - how the
  retrieval-outage honesty example family maps onto current KAG return and
  handoff surfaces without absorbing runtime or eval ownership
- [TOS_RETRIEVAL_AXIS_PACK](TOS_RETRIEVAL_AXIS_PACK.md) - how the current
  generated retrieval-axis pack materializes `AOA-K-0007` without adding
  ranking or routing policy
- [TOS_TEXT_CHUNK_MAP](TOS_TEXT_CHUNK_MAP.md) - how the current ToS chunk-map
  pack materializes stable source-linked chunk units
- [TOS_RAW_TABLE_INTAKE_STUB](TOS_RAW_TABLE_INTAKE_STUB.md) - how future raw
  candidate tables from `Tree-of-Sophia/intake/...` are reserved conceptually
  without activating a new KAG pack yet
- [CROSS_SOURCE_NODE_PROJECTION](CROSS_SOURCE_NODE_PROJECTION.md) - how the
  current bounded node projection pairs one source-owned technique export with
  one supporting ToS export
- [REASONING_HANDOFF](REASONING_HANDOFF.md) - how runtime handoff may ask KAG
  for derived retrieval context without promoting it into source truth
- [TECHNIQUE_LIFT_PACK](TECHNIQUE_LIFT_PACK.md) - how the first manifest-driven
  technique lift pack materializes active KAG surfaces from `aoa-techniques`
- [REASONING_HANDOFF_PACK](REASONING_HANDOFF_PACK.md) - how the first
  multi-source reasoning handoff pack materializes bounded scenario capsules for
  `AOA-P-0008` and `AOA-P-0009`
- [BOUNDARIES](BOUNDARIES.md) - what the KAG layer owns and must not absorb
- [SOURCE_POLICY](SOURCE_POLICY.md) - how authoritative sources and derived KAG
  surfaces should relate
- [decisions/2026-04-13-kag-maturity-hardening](decisions/2026-04-13-kag-maturity-hardening.md)
  - why the repository now hardens around maturity governance, wait states, and
  stop-rules
- `../examples/tos_retrieval_axis_surface.example.json` - compact example of the
  bridge retrieval surface
- `../examples/tos_retrieval_axis_pack.example.json` - compact example of the
  generated retrieval-axis pack
- `../examples/counterpart_consumer_contract.example.json` - compact example of
  the first explicit downstream consumer contract for counterpart refs
- `../examples/counterpart_federation_exposure_review.example.json` - compact
  example of the current machine-readable federation exposure review for
  counterpart posture
- `../examples/cross_source_node_projection.example.json` - compact example of
  the bounded cross-source projection pack
- `../examples/reasoning_handoff_guardrail.example.json` - compact example of
  the runtime-to-KAG guardrail surface
- `../examples/federation_kag_export.example.json` - compact example of the
  future source-owned federation export capsule

## Notes

This repository should stay bounded.
If a document starts trying to become an authored technique corpus, workflow
corpus, proof corpus, memory store, or routing surface, it probably belongs in a
neighboring AoA repository or in Tree of Sophia instead.
