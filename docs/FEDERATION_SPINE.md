# Federation Spine

This document records the first generated federation spine pack in `aoa-kag`.

It is the first bounded pilot for federation KAG readiness.

## Purpose

This wave is intentionally narrow:

- materialize one reviewable federation spine surface
- keep the landing entirely inside `aoa-kag`
- prove the pack shape before any source repository publishes a dedicated
  `generated/kag_export.min.json`
- keep the new surface experimental rather than claiming a finished federation
  export loop

## Current pilot posture

The current spine is an `aoa-techniques`-only pilot.

It derives from existing generated source-owned surfaces:

- `generated/repo_doc_surface_manifest.min.json`
- `generated/technique_catalog.min.json`

Those donor surfaces are declared in `manifests/federation_spine.json`.

The generated outputs live at:

- `generated/federation_spine.json`
- `generated/federation_spine.min.json`

## What the spine keeps

For the current pilot repo, the generated pack keeps:

- the current bounded entry surface refs
- the current bounded object-spine ref
- a small deterministic sample of object ids
- the planned future export ref
- explicit provenance and non-identity notes

## What the spine does not do

This wave does not:

- claim that `aoa-techniques` already publishes `generated/kag_export.min.json`
- claim that all AoA or ToS repositories now expose the same export contract
- move routing ownership into `aoa-kag`
- move canon authorship into `aoa-kag`
- replace source-owned entry surfaces with KAG-authored meaning

## Why the pilot starts this way

`aoa-techniques` already exposes bounded generated surfaces that are strong
enough for a reviewable pilot:

- repo-level entry surfaces
- object-level metadata spine surfaces

That makes it a good first donor without forcing cross-repo edits in the same
wave.

## Regeneration posture

Use:

```bash
python scripts/generate_kag.py
python scripts/validate_kag.py
```

If `aoa-techniques` is not checked out beside this repository, point the
scripts at it with `AOA_TECHNIQUES_ROOT`.
