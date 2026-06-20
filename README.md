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
- one current bounded consumer path: [docs/CONSUMER_GUIDE](docs/CONSUMER_GUIDE.md), [docs/TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK](docs/TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK.md), and [docs/FEDERATION_SPINE](docs/FEDERATION_SPINE.md)
- source-owned dependencies, bridge posture, and regrounding: [docs/SOURCE_OWNED_EXPORT_DEPENDENCIES](docs/SOURCE_OWNED_EXPORT_DEPENDENCIES.md), [docs/BRIDGE_CONTRACTS](docs/BRIDGE_CONTRACTS.md), [docs/REASONING_HANDOFF](docs/REASONING_HANDOFF.md), [docs/RECURRENCE_REGROUNDING](docs/RECURRENCE_REGROUNDING.md), [docs/BOUNDARIES](docs/BOUNDARIES.md), and [docs/SOURCE_POLICY](docs/SOURCE_POLICY.md)
- maturity governance, owner wait states, and proof lanes: [docs/KAG_MATURITY_GOVERNANCE](docs/KAG_MATURITY_GOVERNANCE.md), [docs/KAG_OWNER_WAIT_STATES](docs/KAG_OWNER_WAIT_STATES.md), [docs/KAG_PROOF_EXPECTATIONS](docs/KAG_PROOF_EXPECTATIONS.md), and `generated/kag_maturity_governance.min.json`
- additive stress and quarantine doctrine: [stress-regrounding](mechanics/antifragility/parts/projection-health/docs/stress-regrounding.md), [projection-quarantine](mechanics/antifragility/parts/projection-quarantine/docs/projection-quarantine.md), and [retrieval-outage-regrounding](mechanics/antifragility/parts/retrieval-outage-regrounding/docs/retrieval-outage-regrounding.md)
- federation and counterpart surfaces: [docs/COUNTERPART_CONSUMER_CONTRACT](docs/COUNTERPART_CONSUMER_CONTRACT.md), [docs/COUNTERPART_FEDERATION_EXPOSURE_REVIEW](docs/COUNTERPART_FEDERATION_EXPOSURE_REVIEW.md), [docs/FEDERATION_KAG_READINESS](docs/FEDERATION_KAG_READINESS.md), [docs/FEDERATION_SPINE](docs/FEDERATION_SPINE.md), and [docs/COUNTERPART_EDGE_CONTRACTS](docs/COUNTERPART_EDGE_CONTRACTS.md)
- current derived pilots: [docs/TECHNIQUE_LIFT_PACK](docs/TECHNIQUE_LIFT_PACK.md), [docs/TOS_TEXT_CHUNK_MAP](docs/TOS_TEXT_CHUNK_MAP.md), [docs/TOS_RETRIEVAL_AXIS_PACK](docs/TOS_RETRIEVAL_AXIS_PACK.md), [docs/REASONING_HANDOFF_PACK](docs/REASONING_HANDOFF_PACK.md), [docs/TOS_ZARATHUSTRA_ROUTE_PACK](docs/TOS_ZARATHUSTRA_ROUTE_PACK.md), [docs/TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK](docs/TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK.md), [docs/CROSS_SOURCE_NODE_PROJECTION](docs/CROSS_SOURCE_NODE_PROJECTION.md), and [docs/TOS_RAW_TABLE_INTAKE_HOLD](docs/TOS_RAW_TABLE_INTAKE_HOLD.md)
- docs map: [docs/README](docs/README.md)
- current direction: [ROADMAP](ROADMAP.md)

## Route by need

- registry and substrate projections: `generated/kag_registry.json`, `generated/kag_registry.min.json`, and `manifests/kag_registry.json`
- local `/kag` subtree protocol posture: [kag](kag/README.md), [source_home.manifest](kag/source_home.manifest.json), and [LOCAL_SUBTREE_PROTOCOL](kag/LOCAL_SUBTREE_PROTOCOL.md)
- durable decision rationale: `docs/decisions/AOA-KAG-D-*.md`, `docs/decisions/indexes/*.md`, and the `source-fast` validation lane
- manifest-driven donor and ToS lift packs: `generated/technique_lift_pack*.json`, `generated/tos_text_chunk_map*.json`, `generated/tos_retrieval_axis_pack*.json`, `generated/tos_zarathustra_route_pack*.json`, `generated/tos_zarathustra_route_retrieval_pack*.json`, and the matching `manifests/*.json`
- maturity stop-rule and wait-state surface: `generated/kag_maturity_governance*.json`, `manifests/kag_maturity_governance.json`, [docs/KAG_MATURITY_GOVERNANCE](docs/KAG_MATURITY_GOVERNANCE.md), [docs/KAG_OWNER_WAIT_STATES](docs/KAG_OWNER_WAIT_STATES.md), and [docs/KAG_PROOF_EXPECTATIONS](docs/KAG_PROOF_EXPECTATIONS.md)
- reasoning, return, and federation bridge surfaces: `generated/reasoning_handoff_pack*.json`, `generated/return_regrounding_pack*.json`, `generated/federation_spine*.json`, `generated/counterpart_federation_exposure_review*.json`, and [docs/FEDERATION_KAG_READINESS](docs/FEDERATION_KAG_READINESS.md)
- additive projection-health and regrounding adjuncts: `mechanics/antifragility/parts/projection-health/schemas/projection_health_receipt_v1.json`, `mechanics/antifragility/parts/retrieval-outage-regrounding/schemas/regrounding_ticket_v1.json`, `mechanics/antifragility/parts/projection-health/examples/projection_health_receipt.example.json`, `mechanics/antifragility/parts/retrieval-outage-regrounding/examples/regrounding_ticket.example.json`, `mechanics/antifragility/parts/projection-health/examples/projection_health_receipt.retrieval-outage-honesty.example.json`, `mechanics/antifragility/parts/retrieval-outage-regrounding/examples/regrounding_ticket.retrieval-outage-honesty.example.json`, [stress-regrounding](mechanics/antifragility/parts/projection-health/docs/stress-regrounding.md), [projection-quarantine](mechanics/antifragility/parts/projection-quarantine/docs/projection-quarantine.md), and [retrieval-outage-regrounding](mechanics/antifragility/parts/retrieval-outage-regrounding/docs/retrieval-outage-regrounding.md)
- via negativa pruning checklist: [docs/VIA_NEGATIVA_CHECKLIST](docs/VIA_NEGATIVA_CHECKLIST.md)
- tiny consumer and bounded cross-source adjuncts: `generated/tiny_consumer_bundle*.json`, `generated/cross_source_node_projection*.json`, and `examples/*.example.json`
- current-state validation: `python scripts/ci_gate.py --mode source-fast`
- generated parity and targeted regeneration: `python scripts/ci_gate.py --mode generated`
- release-prep parity: `python scripts/release_check.py` and `git status -sb`

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

- registry and core substrate: `generated/kag_registry.json` and `generated/kag_registry.min.json`
- local-subtree source-home preflight: `kag/README.md`, `kag/source_home.manifest.json`, and `kag/LOCAL_SUBTREE_PROTOCOL.md`
- manifest-driven lift packs: `generated/technique_lift_pack*.json`, `manifests/technique_lift_pack.json`, and [docs/TECHNIQUE_LIFT_PACK.md](docs/TECHNIQUE_LIFT_PACK.md)
- ToS-derived packs: `generated/tos_text_chunk_map*.json`, `generated/tos_retrieval_axis_pack*.json`, `generated/tos_zarathustra_route_pack*.json`, and `generated/tos_zarathustra_route_retrieval_pack*.json`
- maturity governance and stop-rule surface: `generated/kag_maturity_governance*.json`, `manifests/kag_maturity_governance.json`, [docs/KAG_MATURITY_GOVERNANCE.md](docs/KAG_MATURITY_GOVERNANCE.md), [docs/KAG_OWNER_WAIT_STATES.md](docs/KAG_OWNER_WAIT_STATES.md), and [docs/KAG_PROOF_EXPECTATIONS.md](docs/KAG_PROOF_EXPECTATIONS.md)
- reasoning, return, and federation seams: `generated/reasoning_handoff_pack*.json`, `generated/return_regrounding_pack*.json`, `generated/federation_spine*.json`, and the federation export / counterpart review families
- additive stress and quarantine adjuncts: `mechanics/antifragility/parts/projection-health/schemas/projection_health_receipt_v1.json`, `mechanics/antifragility/parts/retrieval-outage-regrounding/schemas/regrounding_ticket_v1.json`, `mechanics/antifragility/parts/projection-health/examples/projection_health_receipt.example.json`, `mechanics/antifragility/parts/retrieval-outage-regrounding/examples/regrounding_ticket.example.json`, `mechanics/antifragility/parts/projection-health/examples/projection_health_receipt.retrieval-outage-honesty.example.json`, `mechanics/antifragility/parts/retrieval-outage-regrounding/examples/regrounding_ticket.retrieval-outage-honesty.example.json`, [mechanics/antifragility/parts/projection-health/docs/stress-regrounding.md](mechanics/antifragility/parts/projection-health/docs/stress-regrounding.md), [mechanics/antifragility/parts/projection-quarantine/docs/projection-quarantine.md](mechanics/antifragility/parts/projection-quarantine/docs/projection-quarantine.md), and [mechanics/antifragility/parts/retrieval-outage-regrounding/docs/retrieval-outage-regrounding.md](mechanics/antifragility/parts/retrieval-outage-regrounding/docs/retrieval-outage-regrounding.md)
- tiny consumer and cross-source adjuncts: `generated/tiny_consumer_bundle*.json` and `generated/cross_source_node_projection*.json`

Schemas, examples, and manifests alongside those families make the derived surfaces reviewable without moving authority out of the owning repositories.

## Go here when...

- you need authored meaning for techniques, skills, evals, or source texts: go to the owning repository
- you need the ecosystem center and layer map: [`Agents-of-Abyss`](https://github.com/8Dionysus/Agents-of-Abyss)
- you need source-authored philosophy and canonical tree surfaces: [`Tree-of-Sophia`](https://github.com/8Dionysus/Tree-of-Sophia)
- you need navigation and dispatch rather than derived substrate semantics: [`aoa-routing`](https://github.com/8Dionysus/aoa-routing)
- you need explicit memory objects or recall posture: [`aoa-memo`](https://github.com/8Dionysus/aoa-memo)

## Build and validate

For a read-only current-state pass, run:

```bash
python scripts/ci_gate.py --mode source-fast
```

For release-prep parity, run:

```bash
python scripts/release_check.py
git status -sb
```

`release_check.py` reads the `release` lane from `config/validation_lanes.json`;
the active command order lives there, not in this README.

If you need targeted regeneration and direct validation, run:

```bash
python scripts/ci_gate.py --mode generated
```

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

`aoa-memo` also publishes a source-owned bridge-bearing donor export for readiness, and `docs/MEMORY_READINESS_BOUNDARY.md` is the memo-owned boundary for future durable-consequence, retention, and live-ledger pressure. The live spine intentionally stays narrower than that wider bridge horizon.

The current pause posture is explicit now: maintain and prove the existing `AOA-K-*` set, keep `AOA-K-0008` contract-only, and wait for neighboring owner layers to publish stronger source-owned exports, contracts, or proof lanes before widening the substrate.

## License

Apache-2.0
