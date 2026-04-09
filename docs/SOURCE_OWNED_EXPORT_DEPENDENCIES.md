# Source-Owned Export Dependencies

This document records the current source-owned export dependency contract for
`aoa-kag`.

It keeps the current external tiny-export assumptions explicit instead of
leaving them hidden inside generator or validator code.

## Purpose

The current contract is intentionally narrow:

- declare exactly which external source-owned exports the current experimental
  KAG surfaces recognize as invariant-backed donors
- keep expected owner, kind, object id, and entry surface explicit
- keep live consumption separate from donor activation so widening remains
  reviewable

## Current pilot dependencies

The current bounded contract depends on:

- `aoa-techniques/generated/kag_export.min.json`
- `Tree-of-Sophia/generated/kag_export.min.json`
- `aoa-memo/generated/kag_export.min.json`

`aoa-memo/generated/kag_export.min.json` is now listed as an invariant-backed
donor export, but its `consumed_by` list is intentionally empty in this wave.
That keeps the donor contract explicit without pretending the live generated KAG
surfaces already consume it.

Those dependencies are declared in
`manifests/source_owned_export_dependencies.json`.

Live donor visibility is now declared separately in
`manifests/federation_export_registry.json`.
That registry decides whether a donor is only registry-visible or also live in
the spine and downstream routing.

They also anchor the first `source_export_reentry` mode in
`generated/return_regrounding_pack.min.json`.

## What the contract keeps

Each dependency keeps:

- one stable `dependency_id`
- the source-owned `repo` and `path`
- the expected `owner_repo`, `kind`, and `object_id`
- the required top-level export fields
- the expected `entry_surface`
- the current live `consumed_by` surface ids inside `aoa-kag`

## What this contract does not do

This contract does not:

- replace source-owned export doctrine in neighboring repositories
- claim that every declared donor is already live in the spine
- widen `aoa-kag` into source ownership

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
