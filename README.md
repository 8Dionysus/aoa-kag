# aoa-kag

`aoa-kag` is the derived knowledge substrate layer of the AoA ecosystem.

It exists to make knowledge-ready structures explicit, reviewable, and bounded. Source repositories keep authored meaning. `aoa-kag` keeps the derived substrate built from those truths.

> Current release: `v0.2.2`. See [CHANGELOG](CHANGELOG.md) for release notes.

## Start here

Use the shortest route by need:

- role, model, and source-first posture: [CHARTER](CHARTER.md), [docs/KAG_MODEL](docs/KAG_MODEL.md), [docs/BOUNDARIES](docs/BOUNDARIES.md), and [docs/SOURCE_POLICY](docs/SOURCE_POLICY.md)
- one current bounded consumer path: [docs/CONSUMER_GUIDE](docs/CONSUMER_GUIDE.md), [docs/TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK](docs/TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK.md), and [docs/FEDERATION_SPINE](docs/FEDERATION_SPINE.md)
- source-owned dependencies, bridge posture, and regrounding: [docs/SOURCE_OWNED_EXPORT_DEPENDENCIES](docs/SOURCE_OWNED_EXPORT_DEPENDENCIES.md), [docs/BRIDGE_CONTRACTS](docs/BRIDGE_CONTRACTS.md), [docs/REASONING_HANDOFF](docs/REASONING_HANDOFF.md), [docs/RECURRENCE_REGROUNDING](docs/RECURRENCE_REGROUNDING.md), [docs/BOUNDARIES](docs/BOUNDARIES.md), and [docs/SOURCE_POLICY](docs/SOURCE_POLICY.md)
- maturity governance, owner wait states, and proof lanes: [docs/KAG_MATURITY_GOVERNANCE](docs/KAG_MATURITY_GOVERNANCE.md), [docs/KAG_OWNER_WAIT_STATES](docs/KAG_OWNER_WAIT_STATES.md), [docs/KAG_PROOF_EXPECTATIONS](docs/KAG_PROOF_EXPECTATIONS.md), and `generated/kag_maturity_governance.min.json`
- additive stress and quarantine doctrine: [docs/KAG_STRESS_REGROUNDING](docs/KAG_STRESS_REGROUNDING.md), [docs/KAG_PROJECTION_QUARANTINE](docs/KAG_PROJECTION_QUARANTINE.md), and [docs/KAG_REGROUNDING_CHAOS_WAVE1.md](docs/KAG_REGROUNDING_CHAOS_WAVE1.md)
- federation and counterpart surfaces: [docs/COUNTERPART_CONSUMER_CONTRACT](docs/COUNTERPART_CONSUMER_CONTRACT.md), [docs/COUNTERPART_FEDERATION_EXPOSURE_REVIEW](docs/COUNTERPART_FEDERATION_EXPOSURE_REVIEW.md), [docs/FEDERATION_KAG_READINESS](docs/FEDERATION_KAG_READINESS.md), [docs/FEDERATION_SPINE](docs/FEDERATION_SPINE.md), and [docs/COUNTERPART_EDGE_CONTRACTS](docs/COUNTERPART_EDGE_CONTRACTS.md)
- current derived pilots: [docs/TECHNIQUE_LIFT_PACK](docs/TECHNIQUE_LIFT_PACK.md), [docs/TOS_TEXT_CHUNK_MAP](docs/TOS_TEXT_CHUNK_MAP.md), [docs/TOS_RETRIEVAL_AXIS_PACK](docs/TOS_RETRIEVAL_AXIS_PACK.md), [docs/REASONING_HANDOFF_PACK](docs/REASONING_HANDOFF_PACK.md), [docs/TOS_ZARATHUSTRA_ROUTE_PACK](docs/TOS_ZARATHUSTRA_ROUTE_PACK.md), [docs/TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK](docs/TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK.md), [docs/CROSS_SOURCE_NODE_PROJECTION](docs/CROSS_SOURCE_NODE_PROJECTION.md), and [docs/TOS_RAW_TABLE_INTAKE_STUB](docs/TOS_RAW_TABLE_INTAKE_STUB.md)
- docs map: [docs/README](docs/README.md)
- current direction: [ROADMAP](ROADMAP.md)

## Route by need

- registry and substrate projections: `generated/kag_registry.json`, `generated/kag_registry.min.json`, and `manifests/kag_registry.json`
- manifest-driven donor and ToS lift packs: `generated/technique_lift_pack*.json`, `generated/tos_text_chunk_map*.json`, `generated/tos_retrieval_axis_pack*.json`, `generated/tos_zarathustra_route_pack*.json`, `generated/tos_zarathustra_route_retrieval_pack*.json`, and the matching `manifests/*.json`
- maturity stop-rule and wait-state surface: `generated/kag_maturity_governance*.json`, `manifests/kag_maturity_governance.json`, [docs/KAG_MATURITY_GOVERNANCE](docs/KAG_MATURITY_GOVERNANCE.md), [docs/KAG_OWNER_WAIT_STATES](docs/KAG_OWNER_WAIT_STATES.md), and [docs/KAG_PROOF_EXPECTATIONS](docs/KAG_PROOF_EXPECTATIONS.md)
- reasoning, return, and federation bridge surfaces: `generated/reasoning_handoff_pack*.json`, `generated/return_regrounding_pack*.json`, `generated/federation_spine*.json`, `generated/counterpart_federation_exposure_review*.json`, and [docs/FEDERATION_KAG_READINESS](docs/FEDERATION_KAG_READINESS.md)
- additive projection-health and regrounding adjuncts: `schemas/projection_health_receipt_v1.json`, `schemas/regrounding_ticket_v1.json`, `examples/projection_health_receipt.example.json`, `examples/regrounding_ticket.example.json`, `examples/projection_health_receipt.retrieval-outage-honesty.example.json`, `examples/regrounding_ticket.retrieval-outage-honesty.example.json`, [docs/KAG_STRESS_REGROUNDING](docs/KAG_STRESS_REGROUNDING.md), [docs/KAG_PROJECTION_QUARANTINE](docs/KAG_PROJECTION_QUARANTINE.md), and [docs/KAG_REGROUNDING_CHAOS_WAVE1.md](docs/KAG_REGROUNDING_CHAOS_WAVE1.md)
- via negativa pruning checklist: [docs/VIA_NEGATIVA_CHECKLIST](docs/VIA_NEGATIVA_CHECKLIST.md)
- tiny consumer and bounded cross-source adjuncts: `generated/tiny_consumer_bundle*.json`, `generated/cross_source_node_projection*.json`, and `examples/*.example.json`
- current-state validation: `python scripts/validate_kag.py`, `python scripts/validate_nested_agents.py`, and `python -m unittest discover -s tests -p 'test_*.py'`
- release-prep parity and targeted regeneration: `python scripts/release_check.py`, `python scripts/generate_kag.py`, and `git status -sb`

## What `aoa-kag` owns

This repository is the source of truth for:

- derived substrate structure
- provenance-aware lifted surfaces
- normalized node and edge views at the substrate layer
- retrieval-ready chunk, section, and route packs
- graph-friendly but bounded schemas and exports
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
- manifest-driven lift packs: `generated/technique_lift_pack*.json`, `manifests/technique_lift_pack.json`, and [docs/TECHNIQUE_LIFT_PACK.md](docs/TECHNIQUE_LIFT_PACK.md)
- ToS-derived packs: `generated/tos_text_chunk_map*.json`, `generated/tos_retrieval_axis_pack*.json`, `generated/tos_zarathustra_route_pack*.json`, and `generated/tos_zarathustra_route_retrieval_pack*.json`
- maturity governance and stop-rule surface: `generated/kag_maturity_governance*.json`, `manifests/kag_maturity_governance.json`, [docs/KAG_MATURITY_GOVERNANCE.md](docs/KAG_MATURITY_GOVERNANCE.md), [docs/KAG_OWNER_WAIT_STATES.md](docs/KAG_OWNER_WAIT_STATES.md), and [docs/KAG_PROOF_EXPECTATIONS.md](docs/KAG_PROOF_EXPECTATIONS.md)
- reasoning, return, and federation seams: `generated/reasoning_handoff_pack*.json`, `generated/return_regrounding_pack*.json`, `generated/federation_spine*.json`, and the federation export / counterpart review families
- additive stress and quarantine adjuncts: `schemas/projection_health_receipt_v1.json`, `schemas/regrounding_ticket_v1.json`, `examples/projection_health_receipt.example.json`, `examples/regrounding_ticket.example.json`, `examples/projection_health_receipt.retrieval-outage-honesty.example.json`, `examples/regrounding_ticket.retrieval-outage-honesty.example.json`, [docs/KAG_STRESS_REGROUNDING.md](docs/KAG_STRESS_REGROUNDING.md), [docs/KAG_PROJECTION_QUARANTINE.md](docs/KAG_PROJECTION_QUARANTINE.md), and [docs/KAG_REGROUNDING_CHAOS_WAVE1.md](docs/KAG_REGROUNDING_CHAOS_WAVE1.md)
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
python scripts/validate_kag.py
python scripts/validate_nested_agents.py
python -m unittest discover -s tests -p 'test_*.py'
```

For release-prep parity, run:

```bash
python scripts/release_check.py
git status -sb
```

`release_check.py` is side-effectful because it regenerates KAG outputs before validating them.

If you need targeted regeneration and direct validation, run:

```bash
python scripts/generate_kag.py
python scripts/validate_kag.py
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
