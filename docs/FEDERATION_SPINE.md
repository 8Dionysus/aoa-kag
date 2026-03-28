# Federation Spine

This document records the current generated federation spine pack in `aoa-kag`.

It is the current bounded pilot for federation KAG readiness.

## Purpose

This wave is intentionally narrow:

- materialize one reviewable federation spine surface
- keep the landing entirely inside `aoa-kag` as a derived spine
- prove the first real two-repo source-owned export loop before widening beyond
  `tiny`
- keep the new surface experimental rather than claiming a finished federation
  export loop

## Current pilot posture

The current spine is a two-repo experimental pilot.

For `aoa-techniques`, it now derives from:

- `generated/kag_export.min.json`

For `Tree-of-Sophia`, it now derives from:

- `generated/kag_export.min.json`

Those donor surfaces are declared in `manifests/federation_spine.json`.
The current external export expectations are made explicit in
`manifests/source_owned_export_dependencies.json` and documented in
`SOURCE_OWNED_EXPORT_DEPENDENCIES.md`.

The generated outputs live at:

- `generated/federation_spine.json`
- `generated/federation_spine.min.json`

## What the spine keeps

For each current pilot repo, the generated pack keeps:

- the source-owned export ref
- the bounded exported object id and kind
- the current exported entry surface ref
- one short exported summary
- explicit provenance and non-identity notes

## What the spine does not do

This wave does not:

- claim that all AoA or ToS repositories now expose the same export contract
- move routing ownership into `aoa-kag`
- move canon authorship into `aoa-kag`
- replace source-owned entry surfaces with KAG-authored meaning

## Why the pilot starts this way

`aoa-techniques` now publishes one bounded source-owned tiny export for the
current pilot object.

`Tree-of-Sophia` now also publishes one bounded source-owned tiny export for
the current Zarathustra authority slice.

That keeps the pilot source-owned and reviewable without turning the spine into
a wider federation claim.

## Downstream note

`aoa-routing` now consumes this spine through separate `kag_view` entries for
`aoa-techniques` and `Tree-of-Sophia`.

That downstream handoff remains additive: it does not turn `aoa-kag` into
routing authority, and it does not turn the spine into ToS or AoA canon.

For `Tree-of-Sophia`, the spine now also advertises one bounded adjunct
retrieval surface:

- `generated/tos_zarathustra_route_retrieval_pack.min.json`

That adjunct remains handles-only and subordinate to the source-owned
tiny-entry posture. It does not replace the tiny-entry route, does not
activate a new federation kind, and does not grant routing or canon ownership
to `aoa-kag`.

The current spine is also explicitly covered by
`COUNTERPART_FEDERATION_EXPOSURE_REVIEW.md`.
That review confirms that the current two-repo federation spine does not expose
counterpart payloads or imply `AOA-K-0008` activation.

## Regeneration posture

Use:

```bash
python scripts/release_check.py
```

If you only need regeneration and drift validation, use:

```bash
python scripts/generate_kag.py
python scripts/validate_kag.py
```
