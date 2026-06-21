# ToS Retrieval Axis Pack

This document records the current bounded ToS retrieval-axis posture at the
KAG layer.

It materializes the first generated retrieval-axis pack for `AOA-K-0007`
without turning bridge returns into ranking logic, routing ownership, or graph
sovereignty.

## Core rule

A retrieval axis should return bounded handles, not hidden policy.

`aoa-kag` may derive one bridge-ready axis object from one current ToS
authority-node chunk set, but that object must point readers back toward
stronger source-owned and memo-owned surfaces rather than pretending to become
authored truth.

## Current pilot inputs

The current pilot stays deliberately narrow.
It derives only from already-legible bridge and chunk-map surfaces:

- `mechanics/distillation/parts/tos-text-chunk-map/generated/tos_text_chunk_map.min.json`
- `docs/BRIDGE_CONTRACTS.md`
- `mechanics/boundary-bridge/parts/tos-retrieval-axis/examples/tos_retrieval_axis_surface.example.json`
- `mechanics/boundary-bridge/parts/tos-retrieval-axis/examples/aoa_tos_bridge_envelope.example.json`
- `aoa-memo/mechanics/consumer-handoff/parts/kag-tos-bridge-handoff/examples/memory_chunk_face.bridge.example.json`
- `aoa-memo/mechanics/consumer-handoff/parts/kag-tos-bridge-handoff/examples/memory_graph_face.bridge.example.json`
- `Tree-of-Sophia/ToS/doctrine/NODE_CONTRACT.md`
- `Tree-of-Sophia/ToS/doctrine/PRACTICE_BRANCH.md`
- `Tree-of-Sophia/ToS/public-compatibility/source_node.example.json`
- `Tree-of-Sophia/ToS/public-compatibility/concept_node.example.json`

This keeps the pilot reference-driven and reviewable rather than introducing a
second hidden bridge program.

This pilot also remains deliberately narrow after `AOA-K-0010`: the new
canonical-tree-derived route bundle does not widen `AOA-K-0007` into a broader
consumer-facing retrieval surface in this first downstream pass.

After `AOA-K-0011`, that narrowness still stands: the new standalone
route-family retrieval surface is an additive adjunct over `AOA-K-0010`, not a
replacement or widening of the tiny-entry retrieval-axis pilot.

## Axis rule

The current retrieval-axis rule is:

- one axis object per current ToS authority-node chunk set
- preserve the source `node_id`
- preserve the current chunk ids through `chunk_map_ref`
- return explicit `source_refs`
- return bounded `lineage_refs`
- return bounded `conflict_refs`
- return bounded `practice_refs`
- point to the compact bridge surface, shared envelope, and memo faces
- keep only one `axis_summary` with no scoring, ranking, or routing policy

## Current pilot surfaces

The current pilot surfaces are:

- `mechanics/boundary-bridge/parts/tos-retrieval-axis/schemas/tos-retrieval-axis-pack.schema.json`
- `mechanics/boundary-bridge/parts/tos-retrieval-axis/examples/tos_retrieval_axis_pack.example.json`
- `mechanics/boundary-bridge/parts/tos-retrieval-axis/manifests/tos_retrieval_axis_pack.json`
- `mechanics/boundary-bridge/parts/tos-retrieval-axis/generated/tos_retrieval_axis_pack.json`
- `mechanics/boundary-bridge/parts/tos-retrieval-axis/generated/tos_retrieval_axis_pack.min.json`

## What this pilot does not do

This pilot does not:

- rank chunks or sources
- add hidden retrieval routing logic
- normalize a graph ontology
- activate counterpart mapping
- replace ToS-authored authority or memo-owned bridge faces

## Regeneration posture

Use:

```bash
python scripts/generate_kag.py
python scripts/validate_kag.py
```
