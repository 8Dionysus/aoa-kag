# ToS Raw Table Intake Stub

This document records the current placeholder posture for future raw-table
candidate intake from `Tree-of-Sophia`.

The point is not to activate a new pack or a hidden ingestion pipeline yet.
The point is to name the future seam explicitly so later work has a bounded
place to land.

## Core rule

Future raw-table inputs from `Tree-of-Sophia/intake/...` should be treated as
candidate material, not as source authority.

If a later KAG surface consumes those files, it must preserve the distinction
between:

- primary witness and source files in `Tree-of-Sophia/sources/`
- canonical authored tree surfaces in `Tree-of-Sophia/tree/`
- public compatibility and export surfaces in `Tree-of-Sophia/examples/` and
  `Tree-of-Sophia/generated/`
- raw candidate tables in `Tree-of-Sophia/intake/`

## Current non-activation posture

At the current wave, `aoa-kag` does not define:

- a new raw-table manifest
- a new schema for raw-table ingestion
- a new generated pack
- a new registry surface id
- CSV or TSV normalization logic for ToS candidate tables

Current ToS-facing KAG packs still derive from the public tiny-entry and export
seam rather than directly from raw intake tables.

## Current upstream expectation

When the first real raw tables arrive, the expected upstream path shape is:

- `Tree-of-Sophia/intake/...` for raw candidate tables

That future path should remain subordinate to stronger ToS-owned authority
surfaces rather than being mistaken for a new source of truth.
