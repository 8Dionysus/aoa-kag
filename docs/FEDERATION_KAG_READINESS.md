# Federation KAG Readiness

This document records the first public contract for federation KAG readiness in
`aoa-kag`.

It defines how neighboring source repositories may later publish bounded
KAG-ready exports without turning `aoa-kag` into a replacement source of truth.

## Purpose

This wave is intentionally narrow:

- make the federation-facing export contract public
- keep the first landing fully inside `aoa-kag`
- name the bounded surface families that `aoa-kag` may compose
- separate donor invariants, donor activation, and live spine exposure
- keep source-owned exports distinct from the derived KAG layer

## Source-owned export rule

The intended long-term posture is:

- source repositories publish their own bounded `kag_export.min.json`
- `aoa-kag` consumes those exports into derived substrate surfaces
- downstream consumers read the derived layer as a guide to source, not as a
  new author of meaning

The current generic ingress rule is now explicit:

- each source-owned export must keep exactly one `primary` input
- that `primary` input must belong to `owner_repo`
- `supporting` inputs may belong to other repos

This contract is public now.
`aoa-techniques`, `Tree-of-Sophia`, and now `aoa-memo` can publish bounded
source-owned exports, even though the live federation spine still activates only
the current two-repo pilot.

The donor activation split is also public now:

- `registry_visible`
- `spine_visible`
- `routing_visible`

Those gates are declared in `manifests/federation_export_registry.json` and
materialized in:

- `generated/federation_export_registry.json`
- `generated/federation_export_registry.min.json`

## `federation_kag_export`

The future source-owned export capsule should keep:

- `owner_repo`
- `kind`
- `object_id`
- `primary_question`
- `summary_50`
- `summary_200`
- `source_inputs`
- `entry_surface`
- `section_handles`
- `direct_relations`
- `provenance_note`
- `non_identity_boundary`

The companion schema lives at:

- `schemas/federation-kag-export.schema.json`

The first compact example lives at:

- `examples/federation_kag_export.example.json`

## Bounded KAG surface families

The first useful federation-facing families are:

### 1. Federation spine

A repo-and-object entry spine that points to the smallest current entry surfaces
and object surfaces without claiming that the federation already ships
source-owned KAG exports everywhere.

### 2. Section or chunk maps

Derived section-level or chunk-level surfaces that keep retrieval targets
explicit while keeping the authoritative source intact.

### 3. Context packs

Bounded packs for query modes such as:

- `local_search`
- `global_search`
- `drift_search`

### 4. One-hop edge and axis hints

Derived relation, counterpart, or axis-oriented hints that stay bounded and do
not claim graph sovereignty.

## Model-size packaging

Federation KAG surfaces should remain budget-aware:

- `tiny`
  - top entry objects only
  - short summaries
  - one-hop only
- `standard`
  - more direct relation and handle visibility
- `deep`
  - richer axis, provenance, and tension surfaces

The packaging rule exists to help small models enter the system without forcing
every consumer to read the full doctrinal stack first.

## What this contract does not do

This wave does not:

- widen the live spine or routing contour by default
- claim a finished federation export loop
- move routing, canon ownership, memory truth, or proof into `aoa-kag`
- treat a derived spine as a replacement for authored source meaning

## Current landing posture

The first landing in `aoa-kag` is:

- contract-first
- schema-backed
- generator-backed
- manifest-driven donor activation with a two-repo live pilot in practice

`aoa-memo` now also publishes one source-owned bridge-bearing export as a
registry-visible donor.
That publication proves the contract can cross the memo boundary without yet
widening the live `federation_spine` or downstream routing ABI.
The memo-owned `docs/MEMORY_READINESS_BOUNDARY.md` note now provides the
stronger owner boundary for future durable-consequence, retention, recall, and
live-ledger pressure. KAG readiness may reference it for regrounding, but not
as proof that KAG owns scar normalization, retention guarantees, live
memory-ledger behavior, or routing activation.

The pilot pack is documented in `docs/FEDERATION_SPINE.md`.
It now consumes real source-owned tiny `generated/kag_export.min.json` exports
from `aoa-techniques` and `Tree-of-Sophia` while keeping the wider federation
claim explicitly bounded.
