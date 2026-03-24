# Counterpart Consumer Contract

This document defines the first explicit downstream consumer contract for
`counterpart_refs` in `aoa-kag`.

It does not activate `AOA-K-0008`.
It keeps `AOA-K-0008` planned while making the first bounded consumer seam
reviewable.

## Core rule

`counterpart_refs` may be returned by the reasoning handoff seam only as
contract-or-example refs.

They may point to bounded counterpart contract surfaces.
They may not imply that a generated counterpart payload already exists.

## Current binding

The current binding is:

- `surface_id`: `AOA-K-0008`
- `surface_status`: `planned`
- `consumer_surface_type`: `reasoning_handoff_guardrail`
- `allowed_return_field`: `counterpart_refs`

This keeps the first named consumer of counterpart material inside the existing
reasoning handoff guardrail rather than moving it into routing or federation.

## Required counterpart contract refs

This consumer contract must stay tied to the current counterpart surfaces:

- `docs/COUNTERPART_EDGE_CONTRACTS.md`
- `schemas/counterpart-edge-surface.schema.json`
- `examples/counterpart_edge_view.example.json`

## Allowed return posture

When `counterpart_refs` are returned in the current wave, they may point only to
contract-or-example surfaces such as:

- `docs/COUNTERPART_CONSUMER_CONTRACT.md`
- `examples/counterpart_consumer_contract.example.json`
- `docs/COUNTERPART_EDGE_CONTRACTS.md`
- `examples/counterpart_edge_view.example.json`

This keeps the seam reference-driven and bounded.

## Forbidden interpretations

Do not read this contract as:

- identity proof
- routing authority
- graph-sovereign activation
- silent federation exposure

## Non-goals

- no generated `AOA-K-0008` payload in this wave
- no counterpart ranking or scoring
- no hidden routing or scenario ownership
- no implicit federation exposure for counterpart material
