# Consumer Guide

This guide gives the current narrow consumption path for experimental KAG
surfaces in `aoa-kag`.

Read these surfaces as bounded guides to source-owned meaning, not as
replacements for that meaning.

If you want the current machine-readable package for this path, start with
`generated/tiny_consumer_bundle.min.json`.

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

## Counterpart posture

`counterpart_refs` remain contract-only in the current wave.

Use:

- `docs/COUNTERPART_CONSUMER_CONTRACT.md`
- `examples/counterpart_consumer_contract.example.json`

Do not treat `examples/counterpart_edge_view.example.json` as an active
generated retrieval or projection payload.

## Recommended consumer posture

- use chunk maps when you need stable source-linked retrieval units
- use retrieval-axis packs when you need bounded handles back to source and
  bridge surfaces
- use the federation spine when you need repo-level entrypoints into current
  source-owned exports
- use cross-source projection only as a reviewable one-hop pairing, never as an
  ontology merger
- use the tiny consumer bundle when you want this same path as one stable
  machine-readable package

## Anti-goals

Do not treat these surfaces as:

- replacements for authored source meaning
- routing authority
- proof of counterpart identity
- activation of a generated counterpart surface
- graph-sovereign canon

## Verification posture

Use:

```bash
python scripts/release_check.py
```
