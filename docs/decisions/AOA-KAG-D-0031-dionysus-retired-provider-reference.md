# AOA-KAG-D-0031 Dionysus Retired Provider Reference

## Index Metadata

- Decision ID: AOA-KAG-D-0031
- Original date: 2026-08-01
- Surface classes: kag/source-home, manifest, provider registry, validation guard
- KAG surfaces: local KAG readiness matrix, provider map, provider checkout set
- Source lanes: aoa-kag, Dionysus
- Guard families: source-owned authority, retirement, provider readiness, fail-closed admission
- Posture: accepted

## Context

`AOA-KAG-D-0012` classified `Dionysus` as provider-ready while the repository
published a seed-garden `kag/` packet. The source owner later archived that
surface and isolated the former repository from active OS paths. The KAG
provider registry still pinned the obsolete pre-retirement shape.

## Decision

Remove `Dionysus` from the active provider checkout registry and keep its
readiness row as `retired_reference`. Preserve bounded historical
source-return coordinates, but do not require a live provider home or expose it
as an active MCP provider.

This decision supersedes only the Dionysus provider-ready claim in
`AOA-KAG-D-0012`.

## Options Considered

- Restore the seed provider packet: rejected because the source owner retired
  it.
- Continue pinning the historical provider: rejected because it makes stale
  source appear current.
- Retain a historical reference without a checkout: chosen because it
  preserves provenance without reviving authority or runtime scope.

## Rationale

Retirement in the source owner is stronger than convenience in a derived KAG
provider map. Historical edges may remain discoverable, but they cannot be
used as current provider readiness.

## Consequences

- Full provider validation no longer expects `Dionysus/kag/`.
- Generated provider maps retain the repository only under
  `remaining_routes` as `retired_reference`.
- Re-activation requires a new owner-published source surface and a new
  explicit KAG admission decision.

## Source Surfaces

- `manifests/local_kag_readiness.json`
- `manifests/provider_registry.json`
- `kag/source_home.manifest.json`
- `kag/README.md`
- `kag/LOCAL_SUBTREE_PROTOCOL.md`
- `scripts/validators/local_kag_subtree.py`
- `tests/test_kag_generation.py`
- `Dionysus/README.md`

## Validation

Regenerate the KAG and decision read models, then run the focused local KAG
tests, source-fast lane, generated lane, full OS-wide validator, and release
check.
