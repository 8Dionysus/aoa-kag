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
5. When provenance weakens or a derived surface starts sounding stronger than
   the source that feeds it, read `generated/return_regrounding_pack.min.json`.
   This gives the current bounded re-entry map back to stronger source-owned or
   owner-owned refs.

## Standalone adjunct

`AOA-K-0011` is available as a separate standalone adjunct at:

- `generated/tos_zarathustra_route_retrieval_pack.min.json`

Use it when you want one handles-only route-family read surface over the full
canonical Zarathustra `prologue-1` bundle. Do not treat it as a replacement for
the numbered path above, and do not treat it as routing or ranking policy.

Its payload is intentionally explicit about that limit:

- `adjunct_budget` keeps it as one opt-in standalone adjunct outside the
  numbered tiny path
- `subordinate_posture` points back to
  `Tree-of-Sophia/examples/tos_tiny_entry_route.example.json` before wider
  derived use

## Counterpart posture

`counterpart_refs` remain contract-only in the current wave.

Use:

- `generated/counterpart_federation_exposure_review.min.json`
- `docs/COUNTERPART_CONSUMER_CONTRACT.md`
- `examples/counterpart_consumer_contract.example.json`

Do not treat `examples/counterpart_edge_view.example.json` as an active
generated retrieval or projection payload.

## Recommended consumer posture

- use chunk maps when you need stable source-linked retrieval units
- use retrieval-axis packs when you need bounded handles back to source and
  bridge surfaces
- use the standalone Zarathustra route retrieval pack when you need family-level
  handles over the full canonical `prologue-1` route bundle without widening
  the numbered tiny-entry path
- use the federation spine when you need repo-level entrypoints into current
  source-owned exports
- use cross-source projection only as a reviewable one-hop pairing, never as an
  ontology merger
- use the return regrounding pack when provenance weakens, owner boundaries
  appear, or a derived surface needs to hand the caller back to a stronger ref
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

For a read-only current-state pass, use:

```bash
python scripts/validate_kag.py
python scripts/validate_nested_agents.py
python -m unittest discover -s tests -p 'test_*.py'
```

For release-prep parity, use:

```bash
python scripts/release_check.py
git status -sb
```
