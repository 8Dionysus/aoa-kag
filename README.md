# aoa-kag

`aoa-kag` is the knowledge substrate layer of the AoA ecosystem.

It exists to make derived knowledge-ready structures explicit, reviewable, and bounded.

This repository is not the primary source of truth for techniques, skills, evals, memory objects, or Tree of Sophia texts.
Its role is different: it should hold derived knowledge-ready structures, graph-friendly projections, provenance-aware lifted surfaces, and framework-neutral retrieval substrates built from authoritative sources.

## Start here

If you are new to this repository, use this path:

1. Read [CHARTER](CHARTER.md) for the role and boundaries of the KAG layer.
2. Read [docs/KAG_MODEL](docs/KAG_MODEL.md) for the conceptual model.
3. Read [docs/BOUNDARIES](docs/BOUNDARIES.md) for ownership rules.
4. Read [docs/SOURCE_POLICY](docs/SOURCE_POLICY.md) for source-first discipline.
5. Read [ROADMAP](ROADMAP.md) for the current direction.

For the shortest next route by intent:
- if you need the ecosystem center and layer map, go to [`Agents-of-Abyss`](https://github.com/8Dionysus/Agents-of-Abyss)
- if you need navigation and dispatch rather than derived substrate work, go to [`aoa-routing`](https://github.com/8Dionysus/aoa-routing)
- if you need source-authored knowledge world material, go to [`Tree-of-Sophia`](https://github.com/8Dionysus/Tree-of-Sophia)
- if you need authored practice, execution, or proof meaning, go to [`aoa-techniques`](https://github.com/8Dionysus/aoa-techniques), [`aoa-skills`](https://github.com/8Dionysus/aoa-skills), or [`aoa-evals`](https://github.com/8Dionysus/aoa-evals)

## Quick route table

| repository | owns | go here when |
|---|---|---|
| `aoa-kag` | derived knowledge-ready structures, provenance-aware lifts, graph-ready projections, retrieval substrate contracts | you need derived substrate work built from source-first repositories |
| `Agents-of-Abyss` | ecosystem identity, layer map, federation rules, program-level direction | you need the center and the constitutional view of AoA |
| `aoa-routing` | navigation and dispatch surfaces | you need the smallest next object rather than a derived substrate layer |
| `Tree-of-Sophia` | living knowledge architecture for philosophy and world thought | you need source-authored knowledge world material rather than derived structures |
| `aoa-techniques` / `aoa-skills` / `aoa-evals` | authored practice, execution, and proof meaning | you need source-owned meaning rather than KAG projections |

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

To validate the current KAG-layer surface locally, run:

```bash
python scripts/validate_kag.py
```

## Current status

`aoa-kag` is in bootstrap.
The goal of this first public baseline is to define the role, boundaries, and first machine-readable KAG-layer surface without overbuilding a graph engine too early.

## Principles

- source repositories keep authored meaning
- derived knowledge surfaces should stay explicit and reviewable
- provenance should stay visible where possible
- graph readiness should be bounded, not theatrical
- framework adapters should stay downstream of the substrate
- the KAG layer should not swallow neighboring AoA layers

## License

Apache-2.0
