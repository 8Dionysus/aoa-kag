# ToS Text Chunk Map

This document records the current second-wave ToS text chunk-map posture at the
KAG layer.

It materializes the first source-first chunk map derived from the current public
Zarathustra authority surface in `Tree-of-Sophia` without replacing ToS-authored
node law or splitting ToS node identity into a second canon.

## Core rule

A ToS text chunk map is a retrieval aid, not a second text canon.

`aoa-kag` may derive bounded chunk units from one source-owned ToS authority
surface, but those chunks must guide a reader back to the stronger authored
surface rather than pretending to become the source.

## Current pilot inputs

The current pilot stays deliberately narrow.
It derives only from:

- `Tree-of-Sophia/examples/source_node.example.json` as the authority surface
- `Tree-of-Sophia/docs/TINY_ENTRY_ROUTE.md` as the current route surface
- `Tree-of-Sophia/docs/ZARATHUSTRA_TRILINGUAL_ENTRY.md` as the current capsule
  surface

This keeps the wave aligned with the current bounded Zarathustra tiny-entry seam
rather than widening ToS corpus coverage early.
When `aoa-kag` reads the current tiny-entry route, `bounded_hop` should be
treated as the primary hop field. `lineage_or_context_hop` may remain as a
temporary compatibility alias during transition, but if both are present they
must resolve to the same ToS surface.

This pilot remains deliberately narrow even after `AOA-K-0010`: the new
route-pack wave does not widen `AOA-K-0005` beyond its current source-node
chunk-map posture.

## Chunk rule

The current chunk rule is:

- one chunk per shared `segment_id`
- preserve `node_id`, `segment_id`, and `source_anchor`
- preserve `source_ref`, `route_ref`, and `capsule_ref`
- preserve `interpretation_layers`
- preserve witness-specific `language`, `role`, and `text` inside each chunk
- attach `translation_tension` only when the source node already exposes it for
  that `segment_id`

This keeps the chunk map source-linked and retrieval-ready without turning one
ToS node into three language-split downstream nodes.

## Current pilot surfaces

The current pilot surfaces are:

- `schemas/tos-text-chunk-map.schema.json`
- `examples/tos_text_chunk_map.example.json`
- `manifests/tos_text_chunk_map.json`
- `generated/tos_text_chunk_map.json`
- `generated/tos_text_chunk_map.min.json`

## What this wave does not do

This wave does not:

- create one downstream chunk per language as though ToS had three separate
  source nodes
- infer summaries beyond what the source-owned node already says
- create cross-source node projections
- project counterpart edges
- activate source-owned federation exports
- replace the ToS authority surface

## Regeneration posture

Use:

```bash
python scripts/generate_kag.py
python scripts/validate_kag.py
```

If `Tree-of-Sophia` is not checked out beside this repository, point the
scripts at it with `TREE_OF_SOPHIA_ROOT`.
