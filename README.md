# aoa-kag

`aoa-kag` is the knowledge substrate layer of the AoA ecosystem.

It exists to make derived knowledge-ready structures explicit, reviewable, and bounded.

This repository is not the primary source of truth for techniques, skills, evals, memory objects, or Tree of Sophia texts.
Its role is different: it should hold derived knowledge-ready structures, graph-friendly projections, provenance-aware lifted surfaces, and framework-neutral retrieval substrates built from authoritative sources.

## Start here

If you are new to this repository, use this path:

1. Read [CHARTER](CHARTER.md) for the role and boundaries of the KAG layer.
2. Read [docs/KAG_MODEL](docs/KAG_MODEL.md) for the conceptual model.
3. Read [docs/CONSUMER_GUIDE](docs/CONSUMER_GUIDE.md) for the current narrow consumer path through experimental surfaces.
4. Read [docs/COUNTERPART_CONSUMER_CONTRACT](docs/COUNTERPART_CONSUMER_CONTRACT.md) for the first explicit downstream consumer contract for `counterpart_refs`.
5. Read [docs/COUNTERPART_FEDERATION_EXPOSURE_REVIEW](docs/COUNTERPART_FEDERATION_EXPOSURE_REVIEW.md) for the current review-closed federation posture for `AOA-K-0008` while it remains planned.
6. Read [docs/FEDERATION_KAG_READINESS](docs/FEDERATION_KAG_READINESS.md) for the first public federation-facing export contract.
7. Read [docs/FEDERATION_SPINE](docs/FEDERATION_SPINE.md) for the current experimental federation spine pilot.
8. Read [docs/SOURCE_OWNED_EXPORT_DEPENDENCIES](docs/SOURCE_OWNED_EXPORT_DEPENDENCIES.md) for the explicit source-owned export dependency contract.
9. Read [docs/BRIDGE_CONTRACTS](docs/BRIDGE_CONTRACTS.md) for first-wave AoA-ToS bridge posture at the derived layer.
10. Read [docs/REASONING_HANDOFF](docs/REASONING_HANDOFF.md) for the runtime-to-KAG handoff boundary.
11. Read [docs/RECURRENCE_REGROUNDING](docs/RECURRENCE_REGROUNDING.md) for the bounded recurrence-law landing that regrounds callers back to stronger source or owner refs.
12. Read [docs/TOS_RETRIEVAL_AXIS_PACK](docs/TOS_RETRIEVAL_AXIS_PACK.md) for the current third-wave generated retrieval-axis pack.
13. Read [docs/CROSS_SOURCE_NODE_PROJECTION](docs/CROSS_SOURCE_NODE_PROJECTION.md) for the current fifth-wave bounded cross-source projection pilot.
14. Read [docs/COUNTERPART_EDGE_CONTRACTS](docs/COUNTERPART_EDGE_CONTRACTS.md) for the current deferred counterpart-edge posture and activation gates.
15. Read [docs/TECHNIQUE_LIFT_PACK](docs/TECHNIQUE_LIFT_PACK.md) for the first manifest-driven generated lift pack.
16. Read [docs/TOS_TEXT_CHUNK_MAP](docs/TOS_TEXT_CHUNK_MAP.md) for the current second-wave ToS text chunk-map pilot.
17. Read [docs/REASONING_HANDOFF_PACK](docs/REASONING_HANDOFF_PACK.md) for the first multi-source generated handoff pack.
18. Read [docs/TOS_ZARATHUSTRA_ROUTE_PACK](docs/TOS_ZARATHUSTRA_ROUTE_PACK.md) for the first direct canonical-tree-derived Zarathustra route bundle.
19. Read [docs/TOS_RAW_TABLE_INTAKE_STUB](docs/TOS_RAW_TABLE_INTAKE_STUB.md) for the current non-activated placeholder seam for future raw candidate tables from `Tree-of-Sophia`.
20. Read [docs/BOUNDARIES](docs/BOUNDARIES.md) for ownership rules.
21. Read [docs/SOURCE_POLICY](docs/SOURCE_POLICY.md) for source-first discipline.
22. Read [ROADMAP](ROADMAP.md) for the current direction.

## What this repository is for

`aoa-kag` should own KAG-layer meaning about:
- lifted knowledge units derived from authoritative sources
- normalized node and edge views
- provenance-aware derived structures
- retrieval-ready section and chunk maps
- graph-friendly but bounded schemas
- framework-neutral substrate for later consumers such as HippoRAG and LlamaIndex
- contracts for turning source-first markdown and related corpora into knowledge-ready outputs

## What this repository is not for

This repository should not become the main home for:
- authored technique bundles
- authored skill bundles
- authored eval bundles
- primary memory objects
- routing logic as such
- giant framework-specific application code
- a graph platform that quietly replaces source repositories

`aoa-kag` is not the source of truth for authored meaning.
It is the derived knowledge substrate built from those truths.

## Relationship to the AoA federation

Within AoA:
- `aoa-techniques` owns practice meaning
- `aoa-skills` owns execution meaning
- `aoa-evals` owns bounded proof meaning
- `aoa-routing` should own dispatch and navigation surfaces
- `aoa-memo` should own memory and recall meaning
- `aoa-agents` should own role and persona meaning
- `aoa-playbooks` should own scenario-level compositions
- `aoa-kag` should own derived knowledge substrate meaning

## Local validation

This repository includes a compact machine-readable KAG-layer registry at:
- `generated/kag_registry.json`
- `generated/kag_registry.min.json`

It also now includes the first manifest-driven technique lift pack at:
- `generated/technique_lift_pack.json`
- `generated/technique_lift_pack.min.json`
- `manifests/technique_lift_pack.json`
- `docs/TECHNIQUE_LIFT_PACK.md`

It now also includes the first experimental ToS text chunk map pilot at:
- `generated/tos_text_chunk_map.json`
- `generated/tos_text_chunk_map.min.json`
- `manifests/tos_text_chunk_map.json`
- `docs/TOS_TEXT_CHUNK_MAP.md`

It now also includes one explicit documentation stub for future raw candidate
table intake from `Tree-of-Sophia` at:
- `docs/TOS_RAW_TABLE_INTAKE_STUB.md`

It now also includes the first experimental ToS retrieval-axis pack at:
- `generated/tos_retrieval_axis_pack.json`
- `generated/tos_retrieval_axis_pack.min.json`
- `manifests/tos_retrieval_axis_pack.json`
- `docs/TOS_RETRIEVAL_AXIS_PACK.md`

It now also includes the first direct canonical-tree-derived Zarathustra route
pack at:
- `generated/tos_zarathustra_route_pack.json`
- `generated/tos_zarathustra_route_pack.min.json`
- `manifests/tos_zarathustra_route_pack.json`
- `schemas/tos-zarathustra-route-pack.schema.json`
- `examples/tos_zarathustra_route_pack.example.json`
- `docs/TOS_ZARATHUSTRA_ROUTE_PACK.md`

It now also includes the explicit source-owned export dependency contract at:
- `manifests/source_owned_export_dependencies.json`
- `schemas/source-owned-export-dependencies.schema.json`
- `docs/SOURCE_OWNED_EXPORT_DEPENDENCIES.md`

It also includes a ToS text chunk map schema and example at:
- `schemas/tos-text-chunk-map.schema.json`
- `examples/tos_text_chunk_map.example.json`

It also includes a ToS retrieval-axis pack schema and example at:
- `schemas/tos-retrieval-axis-pack.schema.json`
- `examples/tos_retrieval_axis_pack.example.json`

It also includes a bridge retrieval schema and example at:
- `schemas/bridge-retrieval-surface.schema.json`
- `examples/tos_retrieval_axis_surface.example.json`

It also includes a shared AoA-ToS bridge envelope schema and example at:
- `schemas/bridge-envelope.schema.json`
- `examples/aoa_tos_bridge_envelope.example.json`

It now also includes a counterpart-edge schema and example at:
- `schemas/counterpart-edge-surface.schema.json`
- `examples/counterpart_edge_view.example.json`

It now also includes a counterpart consumer contract schema and example at:
- `schemas/counterpart-consumer-contract.schema.json`
- `examples/counterpart_consumer_contract.example.json`

It now also includes a counterpart federation exposure review family at:
- `schemas/counterpart-federation-exposure-review-manifest.schema.json`
- `schemas/counterpart-federation-exposure-review.schema.json`
- `examples/counterpart_federation_exposure_review.example.json`
- `manifests/counterpart_federation_exposure_review.json`
- `generated/counterpart_federation_exposure_review.json`
- `generated/counterpart_federation_exposure_review.min.json`

It now also includes a cross-source node projection schema and example at:
- `schemas/cross-source-node-projection.schema.json`
- `examples/cross_source_node_projection.example.json`

It now also includes a reasoning handoff guardrail schema and example at:
- `schemas/reasoning-handoff-guardrail.schema.json`
- `examples/reasoning_handoff_guardrail.example.json`

It now also includes a multi-source reasoning handoff pack at:
- `generated/reasoning_handoff_pack.json`
- `generated/reasoning_handoff_pack.min.json`
- `manifests/reasoning_handoff_pack.json`
- `docs/REASONING_HANDOFF_PACK.md`

It now also includes one bounded recurrence regrounding pack at:
- `generated/return_regrounding_pack.json`
- `generated/return_regrounding_pack.min.json`
- `manifests/return_regrounding_pack.json`
- `docs/RECURRENCE_REGROUNDING.md`

It now also includes the current experimental federation spine pilot at:
- `generated/federation_spine.json`
- `generated/federation_spine.min.json`
- `manifests/federation_spine.json`
- `docs/FEDERATION_SPINE.md`

It now also includes the first bounded cross-source node projection pack at:
- `generated/cross_source_node_projection.json`
- `generated/cross_source_node_projection.min.json`
- `manifests/cross_source_node_projection.json`
- `docs/CROSS_SOURCE_NODE_PROJECTION.md`

It now also includes one machine-readable tiny consumer bundle at:
- `generated/tiny_consumer_bundle.json`
- `generated/tiny_consumer_bundle.min.json`
- `manifests/tiny_consumer_bundle.json`

It also includes a human-first experimental consumer path guide at:
- `docs/CONSUMER_GUIDE.md`

It now also includes the first federation KAG export contract surface at:
- `schemas/federation-kag-export.schema.json`
- `examples/federation_kag_export.example.json`

It now also requires nested local guidance surfaces at:
- `manifests/AGENTS.md`
- `generated/AGENTS.md`
- `schemas/AGENTS.md`
- `examples/AGENTS.md`

To run the canonical release-ready check locally, run:

```bash
python scripts/release_check.py
```

To regenerate and validate the current KAG-layer surfaces directly, run:

```bash
python scripts/generate_kag.py
python scripts/validate_kag.py
```

If the neighboring donor repositories are not checked out beside `aoa-kag`,
set:

- `AOA_TECHNIQUES_ROOT`
- `AOA_PLAYBOOKS_ROOT`
- `AOA_EVALS_ROOT`
- `TREE_OF_SOPHIA_ROOT`
- `AOA_MEMO_ROOT`
- `AOA_AGENTS_ROOT`

## Current status

`aoa-kag` is in bootstrap.
The current baseline now includes the first manifest-driven generated lift seam from `aoa-techniques`.
It now also includes the first experimental ToS text chunk-map pilot built from the current source-owned Zarathustra authority surface plus the current tiny-entry route and capsule surfaces in `Tree-of-Sophia`.
It now also names, but does not activate, a future raw-table intake seam for candidate material that may later appear under `Tree-of-Sophia/intake/...`.
It now also includes the first experimental ToS retrieval-axis pack built from that chunk map plus the current bounded bridge and memo-side bridge faces.
`AOA-K-0005` and `AOA-K-0007` remain those narrow tiny-entry pilots in the current wave.
It now also includes `AOA-K-0010`, the first direct canonical-tree-derived Zarathustra route bundle built from canonical `Tree-of-Sophia/tree/**` surfaces plus the canonical relation pack rather than from tiny-entry examples or raw intake.
It now also includes the first bounded multi-source reasoning handoff pack for `AOA-P-0008` and `AOA-P-0009`.
It now also includes one bounded recurrence regrounding pack so retrieval axis use, federation entry, reasoning handoff, and cross-source projection can return callers toward stronger source-owned or owner-owned refs when derived posture weakens.
It now also includes the first public federation-facing KAG export contract, one experimental federation spine pilot built from real source-owned tiny exports in `aoa-techniques` and `Tree-of-Sophia`, and the first bounded cross-source node projection built on top of that loop.
It now also includes one explicit source-owned export dependency contract, one manifest-driven projection pairing law for `AOA-K-0006`, a narrow consumer guide, and one canonical release-check path so the experimental stack is easier to verify without widening it.
It now also includes one explicit counterpart consumer contract and one machine-readable tiny consumer bundle so downstream readers can consume the current path without activating `AOA-K-0008`.
It now also includes one explicit counterpart federation exposure review artifact so the last current activation gate for `AOA-K-0008` is review-closed while the surface remains planned.
`aoa-routing` now consumes that widened spine through separate `kag_view` entries for `aoa-techniques` and `Tree-of-Sophia`, while the spine and projection surfaces remain experimental and non-authoritative.
The goal remains to define the role, boundaries, and bounded machine-readable KAG-layer surfaces without overbuilding a graph engine too early.

## Principles

- source repositories keep authored meaning
- derived knowledge surfaces should stay explicit and reviewable
- provenance should stay visible where possible
- bridges should return bounded retrieval context rather than pretending to be source truth
- graph readiness should be bounded, not theatrical
- framework adapters should stay downstream of the substrate
- the KAG layer should not swallow neighboring AoA layers

## License

Apache-2.0
