# Recurrence Regrounding

This document records the recurrence-law landing for `aoa-kag`.

At the KAG layer, recurrence means one narrow thing:
when a derived surface starts sounding stronger than the sources or owner
contracts that feed it, `aoa-kag` should reground the caller instead of
widening the derived answer.

The concrete KAG recovery move for that law is
`return_regrounding_pack`.

## Purpose

`aoa-kag` already exposes bounded derived surfaces for:

- federation entry
- retrieval-axis context
- reasoning handoff
- cross-source projection

Those surfaces are useful because they guide a caller back toward stronger
source-owned or owner-owned surfaces.

The recurrence regrounding rule makes that posture explicit:

- when provenance weakens
- when non-identity boundaries blur
- when a derived surface is treated as authored truth
- when a caller reaches an owner boundary that belongs elsewhere

In those moments, `aoa-kag` should return one bounded regrounding pack rather
than a wider synthetic answer.

## Core rule

`aoa-kag` may reground a caller toward stronger source or owner surfaces.

It must not use recurrence or return as a pretext to become:

- routing owner
- memory owner
- proof owner
- canon author
- hidden graph sovereign

At this layer, recurrence means guidance back to stronger refs, not a second
canon.

## What counts as regrounding here

A KAG regrounding surface should help a caller answer:

- which stronger source-owned export or authored surface should be inspected
  next
- which derived surface is still safe to keep in view
- which fields must survive the return
- which ownership or non-identity boundary forbids further derived expansion

## Current regrounding modes

### `source_export_reentry`

Use this mode when a caller needs the strongest current federation entry back to
source-owned export capsules before wider derived synthesis resumes.

### `bridge_axis_reentry`

Use this mode when retrieval drift appears inside the ToS bridge path and the
caller needs explicit source, lineage, conflict, practice, or memo-linked
handles again.

### `projection_boundary_reentry`

Use this mode when a cross-source projection is being mistaken for identity,
ontology merger, counterpart activation, or graph expansion.

### `handoff_guardrail_reentry`

Use this mode when runtime-to-KAG handoff begins to overreach into routing,
memory truth, memory readiness, proof, or canon authorship.

### `owner_boundary_reentry`

Use this mode when a caller reaches writeback, memory commitment, or
canon-facing mutation. It also applies when future scar, retention, or live
memory-ledger pressure appears and the stronger answer belongs in
`aoa-memo`.

The KAG layer may prepare guidance, but it must stop at the owner boundary and
point back to the stronger owner contract.

## Proposed pack

The concrete landing for this posture is one new generated pack:

- `schemas/return-regrounding-pack-manifest.schema.json`
- `schemas/return-regrounding-pack.schema.json`
- `manifests/return_regrounding_pack.json`
- `examples/return_regrounding_pack.example.json`
- `generated/return_regrounding_pack.json`
- `generated/return_regrounding_pack.min.json`

The pack is intentionally narrow.

It does not invent new graph semantics.
It only names the strongest current re-entry surfaces and the fields that must
survive return.

## What this wave does not do

This wave does not:

- claim that every derived surface needs a return mode
- move generic recurrence ownership into `aoa-kag`
- replace source-owned exports with KAG-authored summaries
- activate `AOA-K-0008`
- turn regrounding into routing policy
- turn regrounding into memory writeback
- turn memory readiness into KAG-owned scar, retention, or live-ledger
  proof
- turn regrounding into canon mutation

## Compact rule

When the derived layer starts sounding stronger than the sources that feed it,
`aoa-kag` should lead the caller back toward stronger source or owner refs.
