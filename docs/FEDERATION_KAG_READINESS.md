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
- keep source-owned exports distinct from the derived KAG layer

## Source-owned export rule

The intended long-term posture is:

- source repositories publish their own bounded `kag_export.min.json`
- `aoa-kag` consumes those exports into derived substrate surfaces
- downstream consumers read the derived layer as a guide to source, not as a
  new author of meaning

This contract is public now even though no neighboring repository publishes the
export yet.

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

- activate cross-repo source-owned exports
- claim a finished federation export loop
- move routing, canon ownership, memory truth, or proof into `aoa-kag`
- treat a derived spine as a replacement for authored source meaning

## Current landing posture

The first landing in `aoa-kag` is:

- contract-first
- schema-backed
- generator-backed
- two-repo pilot in practice

The pilot pack is documented in `docs/FEDERATION_SPINE.md`.
It now consumes real source-owned tiny `generated/kag_export.min.json` exports
from `aoa-techniques` and `Tree-of-Sophia` while keeping the wider federation
claim explicitly bounded.
