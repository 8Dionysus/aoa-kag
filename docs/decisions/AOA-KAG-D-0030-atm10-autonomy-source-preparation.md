# AOA-KAG-D-0030 ATM10 Autonomy Source Preparation

## Index Metadata

- Decision ID: AOA-KAG-D-0030
- Original date: 2026-08-01
- Surface classes: kag/source-home, manifest, provider registry, validation guard
- KAG surfaces: local KAG readiness matrix, provider map, provider checkout set
- Source lanes: aoa-kag, ATM10-Agent
- Guard families: source-owned authority, owner autonomy, provider readiness, fail-closed admission
- Posture: accepted

## Context

`AOA-KAG-D-0012` classified `ATM10-Agent` as a direct provider while its
repository published a top-level `kag/` packet. The accepted ATM10 autonomy
boundary at `ATM10-D-0003` later removed that packet and made sibling
repositories, shared validators, and hidden OS state non-requirements for the
standalone product. Keeping the old provider pin made KAG validate a historical
ATM10 shape instead of the current owner boundary.

## Decision

Reclassify `ATM10-Agent` from `provider_ready` to `source_preparation` and
remove it from the KAG provider checkout registry. Preserve explicit candidate
source surfaces and owner-return routes, but do not require or synthesize a
top-level provider packet.

This decision supersedes only the ATM10 provider-ready claim in
`AOA-KAG-D-0012`; the remaining direct provider classifications stay active.

## Options Considered

- Restore the deleted ATM10 provider packet: rejected because KAG cannot
  override the stronger source-owner autonomy decision.
- Keep the historical pinned provider: rejected because it hides current
  owner drift behind a stale checkout.
- Move ATM10 to source preparation: chosen because it preserves discovery and
  an explicit future handoff without imposing a sibling dependency.

## Rationale

KAG is a derived substrate. It may index an owner-published optional handoff,
but it cannot make its own provider convenience stronger than the source
repository's clone, build, test, run, and release boundary.

## Consequences

- Full OS-wide provider validation no longer expects `ATM10-Agent/kag/`.
- Generated provider maps expose ATM10 under `remaining_routes` with
  `source_preparation` status.
- KAG admission fails closed if ATM10 is promoted again without a committed,
  optional owner-published provider home and an updated registry decision.
- ATM10 product KAG remains source-owned inside the application and is not
  removed or reinterpreted by this decision.

## Source Surfaces

- `manifests/local_kag_readiness.json`
- `manifests/provider_registry.json`
- `kag/source_home.manifest.json`
- `kag/README.md`
- `kag/LOCAL_SUBTREE_PROTOCOL.md`
- `scripts/validators/local_kag_subtree.py`
- `tests/test_validate_kag.py`
- `tests/test_kag_generation.py`
- `ATM10-Agent/docs/decisions/ATM10-D-0003-autonomous-modular-monolith.md`
- `ATM10-Agent/docs/autonomy/README.md`

## Validation

Regenerate the KAG and decision read models, then run the focused local KAG
tests, source-fast lane, generated lane, full OS-wide validator, and release
check.
