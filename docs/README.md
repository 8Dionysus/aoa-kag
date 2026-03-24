# Documentation Map

This file is the human-first entrypoint for the `docs/` surface of `aoa-kag`.

Use it when you want to understand the AoA KAG layer rather than the broader federation as a whole.

## Start here

- Read [CHARTER](../CHARTER.md) for the role and boundaries of the KAG layer.
- Read [KAG_MODEL](KAG_MODEL.md) for the conceptual model.
- Read [FEDERATION_KAG_READINESS](FEDERATION_KAG_READINESS.md) for the first public federation export contract.
- Read [FEDERATION_SPINE](FEDERATION_SPINE.md) for the first experimental federation spine pilot.
- Read [BRIDGE_CONTRACTS](BRIDGE_CONTRACTS.md) for the first-wave AoA-ToS bridge posture.
- Read [REASONING_HANDOFF](REASONING_HANDOFF.md) for the runtime-to-KAG handoff boundary.
- Read [TECHNIQUE_LIFT_PACK](TECHNIQUE_LIFT_PACK.md) for the first manifest-driven generated lift seam from `aoa-techniques`.
- Read [REASONING_HANDOFF_PACK](REASONING_HANDOFF_PACK.md) for the first multi-source generated handoff seam for `AOA-P-0008` and `AOA-P-0009`.
- Read [BOUNDARIES](BOUNDARIES.md) for ownership discipline relative to neighboring AoA layers.
- Read [SOURCE_POLICY](SOURCE_POLICY.md) for source-first rules.
- Read [ROADMAP](../ROADMAP.md) for the current direction.

## Docs in this repository

- [KAG_MODEL](KAG_MODEL.md) — what the KAG layer is for
- [FEDERATION_KAG_READINESS](FEDERATION_KAG_READINESS.md) — the public contract for future source-owned federation exports
- [FEDERATION_SPINE](FEDERATION_SPINE.md) — the first experimental federation spine pack built from existing generated donor surfaces
- [BRIDGE_CONTRACTS](BRIDGE_CONTRACTS.md) — how the derived layer returns retrieval context without replacing authored sources
- [REASONING_HANDOFF](REASONING_HANDOFF.md) — how runtime handoff may ask KAG for derived retrieval context without promoting it into source truth
- [TECHNIQUE_LIFT_PACK](TECHNIQUE_LIFT_PACK.md) — how the first manifest-driven technique lift pack materializes active KAG surfaces from `aoa-techniques`
- [REASONING_HANDOFF_PACK](REASONING_HANDOFF_PACK.md) — how the first multi-source reasoning handoff pack materializes bounded scenario capsules for `AOA-P-0008` and `AOA-P-0009`
- [BOUNDARIES](BOUNDARIES.md) — what the KAG layer owns and must not absorb
- [SOURCE_POLICY](SOURCE_POLICY.md) — how authoritative sources and derived KAG surfaces should relate
- `../examples/tos_retrieval_axis_surface.example.json` — compact example of the bridge retrieval surface
- `../examples/reasoning_handoff_guardrail.example.json` — compact example of the runtime-to-KAG guardrail surface
- `../examples/federation_kag_export.example.json` — compact example of the future source-owned federation export capsule

## Notes

This repository should stay bounded.
If a document starts trying to become an authored technique corpus, workflow corpus, proof corpus, memory store, or routing surface, it probably belongs in a neighboring AoA repository or in Tree of Sophia instead.
