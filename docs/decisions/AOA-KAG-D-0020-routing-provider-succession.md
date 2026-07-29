# Routing Provider Succession

## Index Metadata

- Decision ID: AOA-KAG-D-0020
- Original date: 2026-07-27
- Surface classes: provider registry, readiness matrix, CI checkout, owner route, generated readmodel
- KAG surfaces: provider map, historical source return, routing owner boundary
- Source lanes: aoa-kag, aoa-sdk, aoa-routing
- Guard families: source-owned authority, provider lifecycle, consumer-zero, historical provenance, generated parity
- Posture: accepted

## Context

The routing control plane and canonical `aoa-routing` artifact producer have
moved into `aoa-sdk`, while the stable `aoa-routing` layer name remains a
compatibility surface. `aoa-kag` still treated the predecessor repository as a
live provider: its registry pinned a checkout, both CI workflows cloned it,
and the readiness matrix reported it as `provider_ready`.

That posture imposed an unnecessary checkout and incorrectly returned current
routing authority to the predecessor. Removing the row entirely would erase
the explicit route for historical KAG records and pre-succession source refs.

## Decision

Remove `aoa-routing` from the active provider registry and CI checkout graph.
Keep one readiness row with `provider_status: retired_reference`; it preserves
pre-succession source handles and returns current routing control-plane work to
the SDK-owned consumer contract.

The active provider registry remains the exact set of `provider_ready` rows.
The wider readiness matrix may also carry explicit non-provider lifecycle rows,
including `retired_reference`. Generated provider maps expose those rows only
through `remaining_routes`, never through provider records, validation roots,
or checkout coordinates.

## Options Considered

- Keep the predecessor as a pinned provider: preserves old behavior but retains
  an active checkout dependency and false ownership.
- Delete all predecessor references: reaches checkout-zero but loses bounded
  provenance and source-return intent.
- Separate active-provider coordinates from an explicit retired reference:
  removes the dependency while preserving history and current owner routing.

## Rationale

KAG is a derived substrate, so it should retain provenance without turning
historical material into a live dependency. `aoa-sdk` now owns current routing
control-plane behavior; `aoa-routing` remains meaningful as a stable ABI name
and predecessor history, not as a provider root.

The split also keeps archive authority outside KAG. `retired_reference` is a
provider-lifecycle state only: it does not assert that the GitHub repository is
archived, that rollback material can be removed, or that the compatibility
window has closed.

## Consequences

- KAG validation and canary workflows no longer clone `aoa-routing`.
- Current routing owner returns target `aoa-sdk`.
- Historical routing refs remain visible and explicitly weaker than current
  SDK contracts.
- Provider-map status counts cover both active providers and remaining routes.
- Landing must publish the SDK-owned contract before or with this consumer
  change; a standalone consumer landing against an unavailable SDK ref is not
  valid.
- Repository archival still requires ecosystem-wide consumer-zero evidence,
  compatibility-window closure, and separate operator approval.

## Source Surfaces

- `manifests/provider_registry.json`
- `manifests/local_kag_readiness.json`
- `schemas/local-kag-subtree.schema.json`
- `.github/workflows/repo-validation.yml`
- `.github/workflows/compatibility-canary.yml`
- `scripts/provider_registry.py`
- `scripts/validators/provider_registry.py`
- `scripts/validators/local_kag_subtree.py`
- `scripts/generation/provider_map.py`
- `scripts/validators/projection/registry.py`
- `generated/local_kag_provider_map.json`
- `kag/source_home.manifest.json`
- `kag/LOCAL_SUBTREE_PROTOCOL.md`

## Validation

Regenerate decision indexes, provider maps, and the repo-local KAG family.
Then run provider-registry tests, KAG generation and validation tests, the
source-fast lane, generated drift checks, and the release gate without any
`AOA_ROUTING_ROOT` or predecessor checkout.
