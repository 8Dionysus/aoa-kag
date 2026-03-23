# aoa-kag

`aoa-kag` is the knowledge substrate layer of the AoA ecosystem.

It exists to make derived knowledge-ready structures explicit, reviewable, and bounded.

This repository is not the primary source of truth for techniques, skills, evals, memory objects, or Tree of Sophia texts.
Its role is different: it should hold derived knowledge-ready structures, graph-friendly projections, provenance-aware lifted surfaces, and framework-neutral retrieval substrates built from authoritative sources.

## Start here

If you are new to this repository, use this path:

1. Read [CHARTER](CHARTER.md) for the role and boundaries of the KAG layer.
2. Read [docs/KAG_MODEL](docs/KAG_MODEL.md) for the conceptual model.
3. Read [docs/BRIDGE_CONTRACTS](docs/BRIDGE_CONTRACTS.md) for first-wave AoA-ToS bridge posture at the derived layer.
4. Read [docs/REASONING_HANDOFF](docs/REASONING_HANDOFF.md) for the runtime-to-KAG handoff boundary.
5. Read [docs/COUNTERPART_EDGE_CONTRACTS](docs/COUNTERPART_EDGE_CONTRACTS.md) for the current third-wave counterpart-edge posture.
6. Read [docs/BOUNDARIES](docs/BOUNDARIES.md) for ownership rules.
7. Read [docs/SOURCE_POLICY](docs/SOURCE_POLICY.md) for source-first discipline.
8. Read [ROADMAP](ROADMAP.md) for the current direction.

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
- `generated/kag_registry.min.json`

It also includes a bridge retrieval schema and example at:
- `schemas/bridge-retrieval-surface.schema.json`
- `examples/tos_retrieval_axis_surface.example.json`

It now also includes a counterpart-edge schema and example at:
- `schemas/counterpart-edge-surface.schema.json`
- `examples/counterpart_edge_view.example.json`

It now also includes a reasoning handoff guardrail schema and example at:
- `schemas/reasoning-handoff-guardrail.schema.json`
- `examples/reasoning_handoff_guardrail.example.json`

To validate the current KAG-layer surface locally, run:

```bash
python scripts/validate_kag.py
```

## Current status

`aoa-kag` is in bootstrap.
The goal of this public baseline is to define the role, boundaries, and bounded machine-readable KAG-layer surfaces without overbuilding a graph engine too early.

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
