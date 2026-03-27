# Source-Owned Export Dependencies

This document records the current source-owned export dependency contract for
`aoa-kag`.

It keeps the current external tiny-export assumptions explicit instead of
leaving them hidden inside generator or validator code.

## Purpose

The current contract is intentionally narrow:

- declare exactly which external source-owned exports the current experimental
  KAG surfaces depend on
- keep expected owner, kind, object id, and entry surface explicit
- make consumer-facing dependency drift reviewable before federation or
  projection outputs are widened

## Current pilot dependencies

The current bounded contract depends on:

- `aoa-techniques/generated/kag_export.min.json`
- `Tree-of-Sophia/generated/kag_export.min.json`

Those dependencies are declared in
`manifests/source_owned_export_dependencies.json`.

They also anchor the first `source_export_reentry` mode in
`generated/return_regrounding_pack.min.json`.

## What the contract keeps

Each dependency keeps:

- one stable `dependency_id`
- the source-owned `repo` and `path`
- the expected `owner_repo`, `kind`, and `object_id`
- the required top-level export fields
- the expected `entry_surface`
- the current `consumed_by` surface ids inside `aoa-kag`

## What this contract does not do

This contract does not:

- replace source-owned export doctrine in neighboring repositories
- claim that all future federation exports must match the current tiny pilot
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
