# Counterpart Edge Contracts

This document records the current third-wave counterpart-edge posture at the KAG layer.

It complements [BRIDGE_CONTRACTS](BRIDGE_CONTRACTS.md).
Bridge retrieval surfaces return bounded context.
Counterpart-edge surfaces project bounded concept-to-operation bridges.

## Core rule

A counterpart edge is a derived bridge, not an identity claim.

It may help readers and downstream tools orient between:

- ToS conceptual origin
- AoA operational meaning
- bounded derived projections in `aoa-kag`

It may not replace any of those authored homes.

## Mapping entry shape

Each counterpart mapping should make these fields explicit:

- `mapping_id`
- `concept_ref`
- `operational_ref`
- `counterpart_mode`
- `evidence_note`
- `non_identity_note`
- optional `supporting_refs`

## Counterpart modes

Use this shared vocabulary only:

- `analogy`
- `support`
- `tension`
- `calibration`

These modes describe the bridge.
They do not rename the concept or operational surface itself.

## Source ownership

The ownership chain for counterpart edges stays explicit:

- `Tree-of-Sophia` owns conceptual origin
- source AoA repositories own operational meaning
- `aoa-kag` owns the derived edge projection

If a mapping cannot point back to those stronger sources, it is not ready for a public KAG surface.

## Example posture

The current public example surface for this contract is:

- `examples/counterpart_edge_view.example.json`

It is intentionally compact and remains `planned` in the KAG registry.
That planned posture is deliberate:

- no downstream consumer contract depends on this surface yet
- federation exposure is still deferred
- the current example is meant to preserve bounded bridge grammar before promotion, not to imply an active public graph layer

## Activation gates

`AOA-K-0008` remains blocked until all of these conditions are true:

- the current `AOA-K-0006` projection pairing law is manifest-driven and validator-backed
- the current external source-owned exports are covered by an explicit dependency contract
- a dedicated downstream consumer contract for counterpart edges exists as a later wave artifact
- federation exposure for counterpart edges is explicitly reviewed rather than inferred from retrieval or projection surfaces

## Anti-goals

Avoid using counterpart-edge views as:

- philosophical proof
- graph-sovereign replacements for authored meaning
- mandatory pairings for every ToS concept
- hidden doctrine imports from operational repos back into ToS
