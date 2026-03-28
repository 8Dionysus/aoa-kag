# Counterpart Federation Exposure Review

This document records the current federation-exposure review for counterpart
material in `aoa-kag`.

It closes the last open activation gate for `AOA-K-0008` only at the current
`planned` posture.
It does not activate a generated counterpart payload.

## Core rule

Counterpart material may be reviewed for federation exposure without being
promoted into an active federation surface.

The current review keeps counterpart posture explicit, contract-backed, and
bounded.
It does not let reasoning handoff, the tiny consumer bundle, the federation
spine, or cross-source projection silently imply that `AOA-K-0008` is already
active.

## Current reviewed surfaces

The current review artifact covers:

- `generated/reasoning_handoff_pack.min.json`
- `generated/tiny_consumer_bundle.min.json`
- `generated/federation_spine.min.json`
- `generated/cross_source_node_projection.min.json`
- `docs/COUNTERPART_CONSUMER_CONTRACT.md`
- `examples/counterpart_consumer_contract.example.json`
- `docs/COUNTERPART_EDGE_CONTRACTS.md`
- `examples/counterpart_edge_view.example.json`

## Current reviewed postures

- `reasoning_handoff_pack` stays `contract_only_counterpart_refs`
- `tiny_consumer_bundle` stays `planned_contract_only`
- `federation_spine` stays `no_counterpart_exposure`
- `cross_source_node_projection` stays `counterpart_activation_forbidden`

The counterpart contract and example surfaces remain review inputs that define
the allowed bounded posture while `AOA-K-0008` is still `planned`.

## Review boundary

The current review artifact forbids:

- silent federation exposure
- generated counterpart payload inference
- routing ownership
- source replacement

Those bans apply even though the current gate is now review-closed for the
`planned` posture.

## Promotion note

This wave closes the federation-exposure review gate for `AOA-K-0008`.

It does not promote `AOA-K-0008` to `experimental`.
Any future promotion must happen in a separate activation wave with its own
generated surface and validation law.

## Regeneration posture

Use:

```bash
python scripts/release_check.py
```
