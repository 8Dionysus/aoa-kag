# Documentation Map

This file is the human-first entrypoint for the `docs/` surface of `aoa-kag`.

Use it when you want to understand the AoA KAG layer rather than the broader federation as a whole.

## Start here

- Read [CHARTER](../CHARTER.md) for the role and boundaries of the KAG layer.
- Read [KAG_MODEL](KAG_MODEL.md) for the conceptual model.
- Read [BRIDGE_CONTRACTS](BRIDGE_CONTRACTS.md) for the first-wave AoA-ToS bridge posture.
- Read [BOUNDARIES](BOUNDARIES.md) for ownership discipline relative to neighboring AoA layers.
- Read [SOURCE_POLICY](SOURCE_POLICY.md) for source-first rules.
- Read [ROADMAP](../ROADMAP.md) for the current direction.

## Docs in this repository

- [KAG_MODEL](KAG_MODEL.md) — what the KAG layer is for
- [BRIDGE_CONTRACTS](BRIDGE_CONTRACTS.md) — how the derived layer returns retrieval context without replacing authored sources
- [BOUNDARIES](BOUNDARIES.md) — what the KAG layer owns and must not absorb
- [SOURCE_POLICY](SOURCE_POLICY.md) — how authoritative sources and derived KAG surfaces should relate
- `../examples/tos_retrieval_axis_surface.example.json` — compact example of the bridge retrieval surface

## Notes

This repository should stay bounded.
If a document starts trying to become an authored technique corpus, workflow corpus, proof corpus, memory store, or routing surface, it probably belongs in a neighboring AoA repository or in Tree of Sophia instead.
