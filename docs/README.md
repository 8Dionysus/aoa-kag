# Documentation Map

This file is the human-first entrypoint for the `docs/` surface of `aoa-kag`.

Use it when you want to understand the AoA KAG layer rather than the broader
federation as a whole.

## Start here

- Read [CHARTER](../CHARTER.md) for the role and boundaries of the KAG layer.
- Read [DESIGN](../DESIGN.md) for the system form of the KAG layer.
- Read [kag](../kag/README.md) for the local-subtree source-home and protocol
  preflight.
- Read [mechanics](../mechanics/README.md) for repeatable KAG operation
  topology.
- Read [KAG_MODEL](KAG_MODEL.md) for the conceptual model.
- Read [KAG_TIERED_DISTRIBUTION](KAG_TIERED_DISTRIBUTION.md) for the separated
  corpus, delivery, Git-hot, artifact, runtime, and CI architecture.
- Read [KAG_TIERED_OPERATIONS](KAG_TIERED_OPERATIONS.md) for build, CAS-only
  validation, offline transfer, outage, rollback, retention, and GC routes.
- Read [KAG_TIERED_MIGRATION](KAG_TIERED_MIGRATION.md) for shadow publication,
  five-owner canary, 24-owner rollout, and final evidence stop-lines.
- Read [CONSUMER_GUIDE](CONSUMER_GUIDE.md) for the current narrow consumer path
  through experimental surfaces.
- Read
  [counterpart-consumer-contract](../mechanics/boundary-bridge/parts/counterpart-edge/docs/counterpart-consumer-contract.md)
  for the
  first explicit downstream consumer contract for `counterpart_refs`.
- Read
  [counterpart-federation-exposure-review](../mechanics/audit/parts/exposure-review/docs/counterpart-federation-exposure-review.md)
  for the current review-closed federation posture for `AOA-K-0008` while it
  remains planned.
- Read
  [federation-kag-readiness](../mechanics/boundary-bridge/parts/source-owned-export/docs/federation-kag-readiness.md)
  for the first public federation export contract.
- Read
  [federation-spine](../mechanics/boundary-bridge/parts/federation-spine/docs/federation-spine.md)
  for the current experimental federation spine pilot.
- Read
  [source-owned-export-dependencies](../mechanics/boundary-bridge/parts/source-owned-export/docs/source-owned-export-dependencies.md)
  for the explicit source-owned export dependency contract.
- Read [decisions](decisions/README.md) for durable KAG route rationale and
  generated decision lookup indexes.
- Read [validation command authority](validation/COMMAND_AUTHORITY.md) for
  active validation lanes, command storage, and script topology.
- Read [test topology](testing/TEST_TOPOLOGY.md) for test homes, coverage
  authority, and failure routes.
- Read [artifact bundles](artifact-bundles/README.md) for the portable
  release-input bundle contract over the root generated KAG registry readmodel.
- Read [BRIDGE_CONTRACTS](BRIDGE_CONTRACTS.md) for the AoA-ToS bridge
  posture.
- Read [RECURRENCE_REGROUNDING](../mechanics/recurrence/parts/return-regrounding/docs/recurrence-regrounding.md)
  for the bounded recurrence-law activation that regrounds callers back to
  stronger source or owner refs when derived posture weakens.
- Read [kag-maturity-governance](../mechanics/growth-cycle/parts/surface-growth-stop-rule/docs/kag-maturity-governance.md) for the rule that
  defines when `aoa-kag` is mature enough to pause widening and wait on owner
  repos.
- Read [kag-owner-wait-states](../mechanics/growth-cycle/parts/surface-growth-stop-rule/docs/kag-owner-wait-states.md) for the explicit map of
  what `aoa-kag` must still wait on from neighboring layers.
- Read [kag-proof-expectations](../mechanics/audit/parts/proof-expectation-refs/docs/kag-proof-expectations.md) for the bounded proof
  lanes that belong in `aoa-evals` rather than inside KAG doctrine.
- Read [stress-regrounding](../mechanics/antifragility/parts/projection-health/docs/stress-regrounding.md) for additive
  projection-health and source-first fallback doctrine under drift.
- Read [projection-quarantine](../mechanics/antifragility/parts/projection-quarantine/docs/projection-quarantine.md) for bounded
  quarantine posture when derived surfaces are unsafe to expand.
- Read [retrieval-outage-regrounding](../mechanics/antifragility/parts/retrieval-outage-regrounding/docs/retrieval-outage-regrounding.md) for the
  retrieval-outage honesty route over current KAG regrounding surfaces.
- Read [TOS_RETRIEVAL_AXIS_PACK](../mechanics/boundary-bridge/parts/tos-retrieval-axis/docs/tos-retrieval-axis-pack.md)
  for the current generated retrieval-axis pack.
- Read [REASONING_HANDOFF](../mechanics/checkpoint/parts/reasoning-handoff/docs/reasoning-handoff.md)
  for the runtime-to-KAG handoff boundary.
- Read [TECHNIQUE_LIFT_PACK](../mechanics/distillation/parts/technique-lift/docs/technique-lift-pack.md)
  for the first manifest-driven generated lift seam from `aoa-techniques`.
- Read [TOS_TEXT_CHUNK_MAP](../mechanics/distillation/parts/tos-text-chunk-map/docs/tos-text-chunk-map.md) for the current ToS chunk-map
  pilot.
- Read
  [tos-raw-table-intake-hold](../mechanics/distillation/parts/tos-route-lift/docs/tos-raw-table-intake-hold.md)
  for the current
  non-activated placeholder seam for future ToS raw candidate tables.
- Read
  [cross-source-node-projection](../mechanics/boundary-bridge/parts/cross-source-projection/docs/cross-source-node-projection.md)
  for the current bounded cross-source projection pilot.
- Read [REASONING_HANDOFF_PACK](../mechanics/checkpoint/parts/reasoning-handoff/docs/reasoning-handoff-pack.md)
  for the first multi-source generated handoff seam for `AOA-P-0008` and
  `AOA-P-0009`.
- Read [BOUNDARIES](BOUNDARIES.md) for ownership discipline relative to
  neighboring AoA layers.
- Read [SOURCE_POLICY](SOURCE_POLICY.md) for source-first rules.
- Read [ROADMAP](../ROADMAP.md) for the current direction.

## Docs in this repository

- [KAG_MODEL](KAG_MODEL.md) - what the KAG layer is for
- [KAG_TIERED_DISTRIBUTION](KAG_TIERED_DISTRIBUTION.md) - the v4 corpus and
  distribution architecture, owner split, budgets, consumer states, and CI
  fan-out contract
- [KAG_TIERED_OPERATIONS](KAG_TIERED_OPERATIONS.md) - deterministic owner
  build, validation, exact v2 assembly, offline transfer, degradation,
  rollback, retention, and GC
- [KAG_TIERED_MIGRATION](KAG_TIERED_MIGRATION.md) - the mandatory shadow,
  canary, rollout, landing, and live-verification sequence for all 24 owners
- [root DESIGN](../DESIGN.md) - the system form of the KAG layer
- [root kag](../kag/README.md) - the source-home preflight for future repo-local KAG
  subtrees
- [root mechanics](../mechanics/README.md) - repeatable KAG operation topology
- [CONSUMER_GUIDE](CONSUMER_GUIDE.md) - the current narrow consumer path
  through chunk maps, retrieval axes, the federation spine, and bounded
  cross-source projection
- [counterpart-consumer-contract](../mechanics/boundary-bridge/parts/counterpart-edge/docs/counterpart-consumer-contract.md) - the first
  explicit downstream consumer contract for `counterpart_refs` while
  `AOA-K-0008` remains planned
- [counterpart-federation-exposure-review](../mechanics/audit/parts/exposure-review/docs/counterpart-federation-exposure-review.md)
  - the current review artifact that closes the federation-exposure gate for
  `AOA-K-0008` without promoting it
- [federation-kag-readiness](../mechanics/boundary-bridge/parts/source-owned-export/docs/federation-kag-readiness.md) -
  the public contract for future source-owned federation exports
- [federation-spine](../mechanics/boundary-bridge/parts/federation-spine/docs/federation-spine.md) -
  the current experimental federation spine pack built from real source-owned
  tiny exports in `aoa-techniques` and `Tree-of-Sophia`
- [source-owned-export-dependencies](../mechanics/boundary-bridge/parts/source-owned-export/docs/source-owned-export-dependencies.md) -
  the explicit contract for the current external source-owned exports consumed
  by `aoa-kag`
- [decisions](decisions/README.md) - durable KAG route rationale, canonical
  `AOA-KAG-D` decision records, and generated lookup indexes
- [validation/COMMAND_AUTHORITY](validation/COMMAND_AUTHORITY.md) - active
  validation lanes, command storage, script inventory, and failure routes
- [testing/TEST_TOPOLOGY](testing/TEST_TOPOLOGY.md) - test homes, coverage
  authority, and test inventory route
- [artifact-bundles](artifact-bundles/README.md) - portable release-input
  bundle manifests for root public generated KAG readmodels
- [BRIDGE_CONTRACTS](BRIDGE_CONTRACTS.md) - how the derived layer returns
  retrieval context without replacing authored sources
- [RECURRENCE_REGROUNDING](../mechanics/recurrence/parts/return-regrounding/docs/recurrence-regrounding.md) - how the KAG layer
  regrounds callers back to stronger source-owned and owner-owned refs when a
  derived surface begins to overreach
- [kag-maturity-governance](../mechanics/growth-cycle/parts/surface-growth-stop-rule/docs/kag-maturity-governance.md) - how `aoa-kag` defines
  pause-worthy maturity, stability tiers, stop-rules, and donor governance
- [kag-owner-wait-states](../mechanics/growth-cycle/parts/surface-growth-stop-rule/docs/kag-owner-wait-states.md) - what `aoa-kag` may
  consume now and what must still wait on owner-side growth
- [kag-proof-expectations](../mechanics/audit/parts/proof-expectation-refs/docs/kag-proof-expectations.md) - which bounded claims
  should be proven in `aoa-evals` rather than claimed inside KAG
- [stress-regrounding](../mechanics/antifragility/parts/projection-health/docs/stress-regrounding.md) - how projection-health
  receipts and regrounding tickets keep consumers source-first when derived
  surfaces drift
- [projection-quarantine](../mechanics/antifragility/parts/projection-quarantine/docs/projection-quarantine.md) - how quarantine
  preserves provenance, fallback refs, and explicit re-entry instead of hiding
  unstable projections
- [retrieval-outage-regrounding](../mechanics/antifragility/parts/retrieval-outage-regrounding/docs/retrieval-outage-regrounding.md) - how the
  retrieval-outage honesty example family maps onto current KAG return and
  handoff surfaces without absorbing runtime or eval ownership
- [TOS_RETRIEVAL_AXIS_PACK](../mechanics/boundary-bridge/parts/tos-retrieval-axis/docs/tos-retrieval-axis-pack.md) - how the current
  generated retrieval-axis pack materializes `AOA-K-0007` without adding
  ranking or routing policy
- [TOS_TEXT_CHUNK_MAP](../mechanics/distillation/parts/tos-text-chunk-map/docs/tos-text-chunk-map.md) - how the current ToS chunk-map
  pack materializes stable source-linked chunk units
- [tos-raw-table-intake-hold](../mechanics/distillation/parts/tos-route-lift/docs/tos-raw-table-intake-hold.md) - how future raw
  candidate tables from `Tree-of-Sophia/intake/...` are reserved conceptually
  without activating a new KAG pack yet
- [cross-source-node-projection](../mechanics/boundary-bridge/parts/cross-source-projection/docs/cross-source-node-projection.md) -
  how the current bounded node projection pairs one source-owned technique
  export with one supporting ToS export
- [REASONING_HANDOFF](../mechanics/checkpoint/parts/reasoning-handoff/docs/reasoning-handoff.md) - how runtime handoff may ask KAG
  for derived retrieval context without promoting it into source truth
- [TECHNIQUE_LIFT_PACK](../mechanics/distillation/parts/technique-lift/docs/technique-lift-pack.md) - how the first manifest-driven
  technique lift pack materializes active KAG surfaces from `aoa-techniques`
- [REASONING_HANDOFF_PACK](../mechanics/checkpoint/parts/reasoning-handoff/docs/reasoning-handoff-pack.md) - how the first
  multi-source reasoning handoff pack materializes bounded scenario capsules for
  `AOA-P-0008` and `AOA-P-0009`
- [BOUNDARIES](BOUNDARIES.md) - what the KAG layer owns and must not absorb
- [SOURCE_POLICY](SOURCE_POLICY.md) - how authoritative sources and derived KAG
  surfaces should relate
- [decisions/AOA-KAG-D-0001-kag-maturity-hardening](decisions/AOA-KAG-D-0001-kag-maturity-hardening.md)
  - why the repository now hardens around maturity governance, wait states, and
  stop-rules
- [decisions/AOA-KAG-D-0002-owner-route-catalog-refresh](decisions/AOA-KAG-D-0002-owner-route-catalog-refresh.md)
  - why KAG follows current owner route surfaces rather than stale consumer
  paths
- `../mechanics/boundary-bridge/parts/tos-retrieval-axis/examples/tos_retrieval_axis_surface.example.json` - compact example of the
  bridge retrieval surface
- `../mechanics/boundary-bridge/parts/tos-retrieval-axis/examples/tos_retrieval_axis_pack.example.json` - compact example of the
  generated retrieval-axis pack
- `../mechanics/boundary-bridge/parts/counterpart-edge/examples/counterpart_consumer_contract.example.json` - compact example of
  the first explicit downstream consumer contract for counterpart refs
- `../mechanics/audit/parts/exposure-review/examples/counterpart_federation_exposure_review.example.json` - compact
  example of the current machine-readable federation exposure review for
  counterpart posture
- `../mechanics/boundary-bridge/parts/cross-source-projection/examples/cross_source_node_projection.example.json` - compact example of
  the bounded cross-source projection pack
- `../mechanics/checkpoint/parts/reasoning-handoff/examples/reasoning_handoff_guardrail.example.json` - compact example of
  the runtime-to-KAG guardrail surface
- `../mechanics/boundary-bridge/parts/source-owned-export/examples/federation_kag_export.example.json` - compact example of the
  future source-owned federation export capsule

## Notes

This repository should stay bounded.
If a document starts trying to become an authored technique corpus, workflow
corpus, proof corpus, memory store, or routing surface, it probably belongs in a
neighboring AoA repository or in Tree of Sophia instead.
