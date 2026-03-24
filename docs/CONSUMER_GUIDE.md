# Consumer Guide

This guide gives the current narrow consumption path for experimental KAG
surfaces in `aoa-kag`.

Read these surfaces as bounded guides to source-owned meaning, not as
replacements for that meaning.

## Recommended read path

1. Start with `generated/tos_text_chunk_map.min.json`.
   This gives the current source-linked retrieval units for the bounded
   Zarathustra authority slice.
2. Move to `generated/tos_retrieval_axis_pack.min.json`.
   This adds bounded source, lineage, conflict, practice, and memo handles
   without ranking or routing policy.
3. Read `generated/federation_spine.min.json`.
   This gives the current two-repo source-owned tiny export entrypoints for
   `aoa-techniques` and `Tree-of-Sophia`.
4. Read `generated/cross_source_node_projection.min.json`.
   This gives the current one-hop projection that pairs one primary AoA export
   with one supporting ToS export while keeping non-identity explicit.

## Recommended consumer posture

- use chunk maps when you need stable source-linked retrieval units
- use retrieval-axis packs when you need bounded handles back to source and
  bridge surfaces
- use the federation spine when you need repo-level entrypoints into current
  source-owned exports
- use cross-source projection only as a reviewable one-hop pairing, never as an
  ontology merger

## Anti-goals

Do not treat these surfaces as:

- replacements for authored source meaning
- routing authority
- proof of counterpart identity
- graph-sovereign canon

## Verification posture

Use:

```bash
python scripts/release_check.py
```
