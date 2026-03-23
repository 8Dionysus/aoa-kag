# Technique Lift Pack

This document records the first manifest-driven generated lift pack inside
`aoa-kag`.

It materializes the current active single-source KAG surfaces that derive from
`aoa-techniques` without claiming that the lifted pack replaces the authored
technique corpus.

## Purpose

The goal of this pack is narrow:

- move `aoa-kag` from bootstrap-only doctrine into a reproducible lift seam
- keep the registry generated from a source manifest rather than hand-maintained
- materialize the first active KAG surfaces as reviewable generated output
- preserve source-first ownership by pointing back to `aoa-techniques`

## Source inputs

The current pack derives only from these bounded donor surfaces in
`aoa-techniques`:

- `generated/technique_section_manifest.min.json`
- `generated/technique_catalog.json`
- `generated/technique_evidence_note_manifest.min.json`

Those inputs are declared in `manifests/technique_lift_pack.json`.

## Surface mapping

The current generated pack materializes these active KAG surfaces:

- `AOA-K-0001` -> `section_lift`
- `AOA-K-0002` -> `metadata_spine`
- `AOA-K-0003` -> `relation_view`
- `AOA-K-0004` -> `provenance_view`

The generated outputs live at:

- `generated/kag_registry.json`
- `generated/kag_registry.min.json`
- `generated/technique_lift_pack.json`
- `generated/technique_lift_pack.min.json`

## What the pack does

For each technique, the current pack keeps:

- one `source_ref` back to the authoritative `TECHNIQUE.md`
- bounded section heading and order data
- bounded metadata spine fields for identity and routing
- bounded direct relation hints
- bounded provenance note handles and review date

## What the pack does not do

This first wave does not:

- copy authored markdown bodies into a new canonical home
- infer graph semantics beyond bounded direct relation hints
- turn evidence notes into a note graph
- absorb routing, eval, or memory doctrine into `aoa-kag`
- replace the source meaning owned by `aoa-techniques`

## Regeneration posture

Use:

```bash
python scripts/generate_kag.py
python scripts/validate_kag.py
```

If `aoa-techniques` is not checked out next to this repository, point the
scripts at it with `AOA_TECHNIQUES_ROOT`.
