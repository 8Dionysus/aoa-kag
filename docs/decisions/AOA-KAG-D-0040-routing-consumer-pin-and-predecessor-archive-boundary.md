# AOA-KAG-D-0040 Routing Consumer Pin And Predecessor Archive Boundary

## Index Metadata

- Decision ID: AOA-KAG-D-0040
- Original date: 2026-08-21
- Surface classes: provider registry, consumer contract, historical provenance, archive boundary
- KAG surfaces: routing owner boundary, remaining routes, source-return handles
- Source lanes: aoa-kag, aoa-sdk, aoa-routing
- Guard families: source-owned authority, consumer pin, retirement, historical provenance, archive approval
- Posture: accepted

## Context

`AOA-KAG-D-0020` removed `aoa-routing` from the active provider checkout set
and retained its readiness row as `retired_reference`. The old provider pin is
still present in the historical tiered-family evidence, so its meaning must be
explicit: it is a provenance coordinate, not an instruction to restore a
checkout or a claim that the GitHub repository has been archived.

## Decision

For the current KAG consumer route, pin `aoa-sdk` at
`459231bc69f39ca0e16e30849bc8e5237068e950` in
`manifests/provider_registry.json`. The admitted consumer contract is
`aoa-sdk/mechanics/boundary-bridge/parts/consumed-surface-posture-gate/docs/routing-consumer-contract.md`;
it identifies `aoa-sdk` as the canonical routing producer while preserving
`aoa-routing` as a compatibility namespace and historical identity.

Classify `aoa-routing@cde31e568e49c5a50afbd89071cf72abd9733d99` as the last
historical KAG provider pin, retained only by
`docs/validation/kag_tiered_baseline.evidence.json` as a bounded
`source_ref`. It must not reappear as an active provider registry entry, CI
checkout, `AOA_ROUTING_ROOT`, or current consumer source.

This decision records KAG's consumer pin and provenance posture. It does not
declare the `aoa-routing` GitHub repository archived, remove its rollback or
compatibility material, or grant KAG archive authority. Those actions require
the predecessor owner and an ecosystem-wide consumer-zero review.

## Options Considered

- Keep the old pin as a provider: rejected because a historical source ref
  would become a live dependency and obscure the SDK ownership transition.
- Delete every old routing ref: rejected because it would erase bounded
  provenance for the generated family and historical source-return readers.
- Record the exact SDK consumer pin and retain the old ref only as provenance:
  chosen because it separates current consumption, historical identity, and
  archive authority.

## Consequences

- Current KAG validation follows the exact SDK pin and its consumer contract.
- The predecessor remains visible only in `remaining_routes` and bounded
  historical evidence.
- Any change to the SDK consumer pin or any attempt to reactivate the
  predecessor requires a fresh owner-reviewed decision and regenerated
  derived evidence.
- Archive completion remains outside `aoa-kag`; no archive claim is inferred
  from `retired_reference` or checkout-zero.

## Source Surfaces

- `manifests/provider_registry.json`
- `manifests/local_kag_readiness.json`
- `.github/workflows/repo-validation.yml`
- `docs/validation/kag_tiered_baseline.evidence.json`
- `docs/decisions/AOA-KAG-D-0020-routing-provider-succession.md`
- `aoa-sdk/mechanics/boundary-bridge/parts/consumed-surface-posture-gate/docs/routing-consumer-contract.md`

## Validation

Validate decision records and regenerated decision indexes, verify the active
provider registry has no `aoa-routing` checkout, and run the KAG source-fast
and owner-family gates with the exact SDK consumer pin.
