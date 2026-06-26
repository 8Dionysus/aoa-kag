# aoa-kag

`aoa-kag` is the derived knowledge substrate layer of the AoA ecosystem.

It exists to make knowledge-ready structures explicit, reviewable, and bounded. Source repositories keep authored meaning. `aoa-kag` keeps the derived substrate built from those truths.

> Current release: `v0.2.2`. See [CHANGELOG](CHANGELOG.md) for release notes.

## Start here

Use the shortest route by need:

- role, system form, model, and source-first posture: [CHARTER](CHARTER.md), [DESIGN](DESIGN.md), [docs/KAG_MODEL](docs/KAG_MODEL.md), [docs/BOUNDARIES](docs/BOUNDARIES.md), and [docs/SOURCE_POLICY](docs/SOURCE_POLICY.md)
- local `/kag` source-home preflight for future repo-local indexes, nodes, edges, projections, and receipts: [kag](kag/README.md)
- repeatable KAG operation topology: [mechanics](mechanics/README.md)
- durable KAG route rationale: [docs/decisions](docs/decisions/README.md) and its generated lookup indexes
- one current bounded consumer path: [docs/CONSUMER_GUIDE](docs/CONSUMER_GUIDE.md), [tos-zarathustra-route-retrieval-pack](mechanics/boundary-bridge/parts/tos-retrieval-axis/docs/tos-zarathustra-route-retrieval-pack.md), and [federation-spine](mechanics/boundary-bridge/parts/federation-spine/docs/federation-spine.md)
- source-owned dependencies, bridge posture, and regrounding: [source-owned-export-dependencies](mechanics/boundary-bridge/parts/source-owned-export/docs/source-owned-export-dependencies.md), [docs/BRIDGE_CONTRACTS](docs/BRIDGE_CONTRACTS.md), [reasoning-handoff](mechanics/checkpoint/parts/reasoning-handoff/docs/reasoning-handoff.md), [recurrence-regrounding](mechanics/recurrence/parts/return-regrounding/docs/recurrence-regrounding.md), [docs/BOUNDARIES](docs/BOUNDARIES.md), and [docs/SOURCE_POLICY](docs/SOURCE_POLICY.md)
- maturity governance, owner wait states, and proof lanes: [kag-maturity-governance](mechanics/growth-cycle/parts/surface-growth-stop-rule/docs/kag-maturity-governance.md), [kag-owner-wait-states](mechanics/growth-cycle/parts/surface-growth-stop-rule/docs/kag-owner-wait-states.md), [kag-proof-expectations](mechanics/audit/parts/proof-expectation-refs/docs/kag-proof-expectations.md), and `mechanics/growth-cycle/parts/surface-growth-stop-rule/generated/kag_maturity_governance.min.json`
- additive stress and quarantine doctrine: [stress-regrounding](mechanics/antifragility/parts/projection-health/docs/stress-regrounding.md), [projection-quarantine](mechanics/antifragility/parts/projection-quarantine/docs/projection-quarantine.md), and [retrieval-outage-regrounding](mechanics/antifragility/parts/retrieval-outage-regrounding/docs/retrieval-outage-regrounding.md)
- federation and counterpart surfaces: [counterpart-consumer-contract](mechanics/boundary-bridge/parts/counterpart-edge/docs/counterpart-consumer-contract.md), [counterpart-federation-exposure-review](mechanics/audit/parts/exposure-review/docs/counterpart-federation-exposure-review.md), [federation-kag-readiness](mechanics/boundary-bridge/parts/source-owned-export/docs/federation-kag-readiness.md), [federation-spine](mechanics/boundary-bridge/parts/federation-spine/docs/federation-spine.md), and [counterpart-edge-contracts](mechanics/boundary-bridge/parts/counterpart-edge/docs/counterpart-edge-contracts.md)
- current derived pilots: [technique-lift-pack](mechanics/distillation/parts/technique-lift/docs/technique-lift-pack.md), [tos-text-chunk-map](mechanics/distillation/parts/tos-text-chunk-map/docs/tos-text-chunk-map.md), [tos-retrieval-axis-pack](mechanics/boundary-bridge/parts/tos-retrieval-axis/docs/tos-retrieval-axis-pack.md), [reasoning-handoff-pack](mechanics/checkpoint/parts/reasoning-handoff/docs/reasoning-handoff-pack.md), [tos-zarathustra-route-pack](mechanics/distillation/parts/tos-route-lift/docs/tos-zarathustra-route-pack.md), [tos-zarathustra-route-retrieval-pack](mechanics/boundary-bridge/parts/tos-retrieval-axis/docs/tos-zarathustra-route-retrieval-pack.md), [cross-source-node-projection](mechanics/boundary-bridge/parts/cross-source-projection/docs/cross-source-node-projection.md), and [tos-raw-table-intake-hold](mechanics/distillation/parts/tos-route-lift/docs/tos-raw-table-intake-hold.md)
- docs map: [docs/README](docs/README.md)
- current direction: [ROADMAP](ROADMAP.md)

## Route by need

- registry and substrate projections: `generated/kag_registry.json`, `generated/kag_registry.min.json`, `manifests/kag_registry.json`, and the OS Abyss ABI/SBOM-lite/SLSA bundle input in `docs/artifact-bundles/kag_registry.bundle.json`
- local `/kag` subtree protocol posture: [kag](kag/README.md), [source_home.manifest](kag/source_home.manifest.json), and [LOCAL_SUBTREE_PROTOCOL](kag/LOCAL_SUBTREE_PROTOCOL.md)
- durable decision rationale: `docs/decisions/AOA-KAG-D-*.md`, `docs/decisions/indexes/*.md`, and the `source-fast` validation lane
- manifest-driven donor and ToS lift packs: `mechanics/distillation/parts/technique-lift/generated/technique_lift_pack*.json`, `mechanics/distillation/parts/tos-text-chunk-map/generated/tos_text_chunk_map*.json`, `mechanics/boundary-bridge/parts/tos-retrieval-axis/generated/tos_retrieval_axis_pack*.json`, `mechanics/distillation/parts/tos-route-lift/generated/tos_zarathustra_route_pack*.json`, `mechanics/boundary-bridge/parts/tos-retrieval-axis/generated/tos_zarathustra_route_retrieval_pack*.json`, and the matching root or part-local manifests.
- maturity stop-rule and wait-state surface: `mechanics/growth-cycle/parts/surface-growth-stop-rule/generated/kag_maturity_governance*.json`, `mechanics/growth-cycle/parts/surface-growth-stop-rule/manifests/kag_maturity_governance.json`, [kag-maturity-governance](mechanics/growth-cycle/parts/surface-growth-stop-rule/docs/kag-maturity-governance.md), [kag-owner-wait-states](mechanics/growth-cycle/parts/surface-growth-stop-rule/docs/kag-owner-wait-states.md), and [kag-proof-expectations](mechanics/audit/parts/proof-expectation-refs/docs/kag-proof-expectations.md)
- reasoning, return, and federation bridge surfaces:
  `mechanics/checkpoint/parts/reasoning-handoff/generated/reasoning_handoff_pack*.json`,
  `mechanics/recurrence/parts/return-regrounding/generated/return_regrounding_pack*.json`,
  `mechanics/boundary-bridge/parts/federation-spine/generated/federation_spine*.json`,
  `mechanics/audit/parts/exposure-review/generated/counterpart_federation_exposure_review*.json`, and
  [federation-kag-readiness](mechanics/boundary-bridge/parts/source-owned-export/docs/federation-kag-readiness.md)
- additive projection-health and regrounding adjuncts: `mechanics/antifragility/parts/projection-health/schemas/projection_health_receipt_v1.json`, `mechanics/antifragility/parts/retrieval-outage-regrounding/schemas/regrounding_ticket_v1.json`, `mechanics/antifragility/parts/projection-health/examples/projection_health_receipt.example.json`, `mechanics/antifragility/parts/retrieval-outage-regrounding/examples/regrounding_ticket.example.json`, `mechanics/antifragility/parts/projection-health/examples/projection_health_receipt.retrieval-outage-honesty.example.json`, `mechanics/antifragility/parts/retrieval-outage-regrounding/examples/regrounding_ticket.retrieval-outage-honesty.example.json`, [stress-regrounding](mechanics/antifragility/parts/projection-health/docs/stress-regrounding.md), [projection-quarantine](mechanics/antifragility/parts/projection-quarantine/docs/projection-quarantine.md), and [retrieval-outage-regrounding](mechanics/antifragility/parts/retrieval-outage-regrounding/docs/retrieval-outage-regrounding.md)
- via negativa pruning checklist: [docs/VIA_NEGATIVA_CHECKLIST](docs/VIA_NEGATIVA_CHECKLIST.md)
- tiny consumer and bounded cross-source adjuncts: `mechanics/boundary-bridge/parts/tiny-consumer-bundle/generated/tiny_consumer_bundle*.json`, `mechanics/boundary-bridge/parts/cross-source-projection/generated/cross_source_node_projection*.json`, and focused part examples
- validation command authority: [docs/validation/COMMAND_AUTHORITY](docs/validation/COMMAND_AUTHORITY.md), with focused local checks routed by the nearest `AGENTS.md`

## What `aoa-kag` owns

This repository is the source of truth for:

- derived substrate structure
- provenance-aware lifted surfaces
- normalized node and edge views at the substrate layer
- retrieval-ready chunk, section, and route packs
- graph-friendly but bounded schemas and exports
- framework-neutral local `/kag` source-home and subtree protocol contracts
- framework-neutral substrate for later downstream consumers

## What it does not own

Do not treat this repository as the source of truth for:

- authored technique, skill, or eval meaning
- primary memory objects
- routing logic as such
- scenario composition
- Tree of Sophia source texts or canonical authored nodes
- giant framework-specific application code

`aoa-kag` is not a replacement for the source repositories it lifts from.

## Current public surfaces

The committed public surfaces group into these families:

- registry and core substrate: `generated/kag_registry.json`, `generated/kag_registry.min.json`, and `docs/artifact-bundles/kag_registry.bundle.json`
- local-subtree source-home preflight: `kag/README.md`, `kag/source_home.manifest.json`, and `kag/LOCAL_SUBTREE_PROTOCOL.md`
- manifest-driven lift packs: `mechanics/distillation/parts/technique-lift/generated/technique_lift_pack*.json`, `mechanics/distillation/parts/technique-lift/manifests/technique_lift_pack.json`, and [mechanics/distillation/parts/technique-lift/docs/technique-lift-pack.md](mechanics/distillation/parts/technique-lift/docs/technique-lift-pack.md)
- ToS-derived packs: `mechanics/distillation/parts/tos-text-chunk-map/generated/tos_text_chunk_map*.json`, `mechanics/boundary-bridge/parts/tos-retrieval-axis/generated/tos_retrieval_axis_pack*.json`, `mechanics/distillation/parts/tos-route-lift/generated/tos_zarathustra_route_pack*.json`, and `mechanics/boundary-bridge/parts/tos-retrieval-axis/generated/tos_zarathustra_route_retrieval_pack*.json`
- maturity governance and stop-rule surface: `mechanics/growth-cycle/parts/surface-growth-stop-rule/generated/kag_maturity_governance*.json`, `mechanics/growth-cycle/parts/surface-growth-stop-rule/manifests/kag_maturity_governance.json`, [mechanics/growth-cycle/parts/surface-growth-stop-rule/docs/kag-maturity-governance.md](mechanics/growth-cycle/parts/surface-growth-stop-rule/docs/kag-maturity-governance.md), [mechanics/growth-cycle/parts/surface-growth-stop-rule/docs/kag-owner-wait-states.md](mechanics/growth-cycle/parts/surface-growth-stop-rule/docs/kag-owner-wait-states.md), and [mechanics/audit/parts/proof-expectation-refs/docs/kag-proof-expectations.md](mechanics/audit/parts/proof-expectation-refs/docs/kag-proof-expectations.md)
- reasoning, return, and federation seams: `mechanics/checkpoint/parts/reasoning-handoff/generated/reasoning_handoff_pack*.json`, `mechanics/recurrence/parts/return-regrounding/generated/return_regrounding_pack*.json`, `mechanics/boundary-bridge/parts/federation-spine/generated/federation_spine*.json`, and the federation export / counterpart review families
- additive stress and quarantine adjuncts: `mechanics/antifragility/parts/projection-health/schemas/projection_health_receipt_v1.json`, `mechanics/antifragility/parts/retrieval-outage-regrounding/schemas/regrounding_ticket_v1.json`, `mechanics/antifragility/parts/projection-health/examples/projection_health_receipt.example.json`, `mechanics/antifragility/parts/retrieval-outage-regrounding/examples/regrounding_ticket.example.json`, `mechanics/antifragility/parts/projection-health/examples/projection_health_receipt.retrieval-outage-honesty.example.json`, `mechanics/antifragility/parts/retrieval-outage-regrounding/examples/regrounding_ticket.retrieval-outage-honesty.example.json`, [mechanics/antifragility/parts/projection-health/docs/stress-regrounding.md](mechanics/antifragility/parts/projection-health/docs/stress-regrounding.md), [mechanics/antifragility/parts/projection-quarantine/docs/projection-quarantine.md](mechanics/antifragility/parts/projection-quarantine/docs/projection-quarantine.md), and [mechanics/antifragility/parts/retrieval-outage-regrounding/docs/retrieval-outage-regrounding.md](mechanics/antifragility/parts/retrieval-outage-regrounding/docs/retrieval-outage-regrounding.md)
- tiny consumer and cross-source adjuncts: `mechanics/boundary-bridge/parts/tiny-consumer-bundle/generated/tiny_consumer_bundle*.json` and `mechanics/boundary-bridge/parts/cross-source-projection/generated/cross_source_node_projection*.json`

Schemas, examples, and manifests alongside those families make the derived surfaces reviewable without moving authority out of the owning repositories.

## Go here when...

- you need authored meaning for techniques, skills, evals, or source texts: go to the owning repository
- you need the ecosystem center and layer map: [`Agents-of-Abyss`](https://github.com/8Dionysus/Agents-of-Abyss)
- you need source-authored philosophy and canonical tree surfaces: [`Tree-of-Sophia`](https://github.com/8Dionysus/Tree-of-Sophia)
- you need navigation and dispatch rather than derived substrate semantics: [`aoa-routing`](https://github.com/8Dionysus/aoa-routing)
- you need explicit memory objects or recall posture: [`aoa-memo`](https://github.com/8Dionysus/aoa-memo)

## Build and validate

Use [docs/validation/COMMAND_AUTHORITY](docs/validation/COMMAND_AUTHORITY.md)
and the nearest `AGENTS.md` for executable validation commands.

`release_check.py` reads the `release` lane from `config/validation_lanes.json`;
the active command order lives there, not in this README. The release lane also
verifies the generated KAG registry as an OS Abyss ABI/SBOM-lite/SLSA artifact
bundle.

If neighboring donor repositories are not checked out beside `aoa-kag`, set the relevant root variables before running the generators or validators:

- `AOA_TECHNIQUES_ROOT`
- `AOA_PLAYBOOKS_ROOT`
- `AOA_EVALS_ROOT`
- `TREE_OF_SOPHIA_ROOT`
- `AOA_MEMO_ROOT`
- `AOA_AGENTS_ROOT`

## Current contour

`aoa-kag` remains intentionally bounded. The public baseline now includes manifest-driven lift packs, ToS-derived chunk and route packs, a multi-source reasoning handoff pack, a bounded recurrence regrounding pack, a maturity-governance stop-rule pack, a federation spine pilot, and one bounded cross-source projection without pretending the repository is already a full graph engine.

For `Tree-of-Sophia`, the live spine still starts from source-owned tiny-export posture. The downstream `aoa-kag` adjunct appears only after the source-owned tiny-entry handoff, so derived retrieval never silently replaces ToS authority.

`aoa-memo` also publishes a source-owned bridge-bearing donor export for readiness, and `aoa-memo/mechanics/readiness-boundary/docs/MEMORY_READINESS_BOUNDARY.md` is the memo-owned boundary for future durable-consequence, retention, and live-ledger pressure. The live spine intentionally stays narrower than that wider bridge horizon.

The current pause posture is explicit now: maintain and prove the existing `AOA-K-*` set, keep `AOA-K-0008` contract-only, and wait for neighboring owner layers to publish stronger source-owned exports, contracts, or proof lanes before widening the substrate.

## License

Apache-2.0
