# ToS Retrieval Axis Pack

This document records the current third-wave ToS retrieval-axis posture at the
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

- `generated/tos_text_chunk_map.min.json`
- `docs/BRIDGE_CONTRACTS.md`
- `examples/tos_retrieval_axis_surface.example.json`
- `examples/aoa_tos_bridge_envelope.example.json`
- `aoa-memo/examples/memory_chunk_face.bridge.example.json`
- `aoa-memo/examples/memory_graph_face.bridge.example.json`
- `Tree-of-Sophia/docs/NODE_CONTRACT.md`
- `Tree-of-Sophia/docs/PRACTICE_BRANCH.md`
- `Tree-of-Sophia/examples/source_node.example.json`
- `Tree-of-Sophia/examples/concept_node.example.json`

This keeps the wave reference-driven and reviewable rather than introducing a
second hidden bridge program.

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

- `schemas/tos-retrieval-axis-pack.schema.json`
- `examples/tos_retrieval_axis_pack.example.json`
- `manifests/tos_retrieval_axis_pack.json`
- `generated/tos_retrieval_axis_pack.json`
- `generated/tos_retrieval_axis_pack.min.json`

## What this wave does not do

This wave does not:

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
