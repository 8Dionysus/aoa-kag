# Changelog

All notable changes to `aoa-kag` will be documented in this file.

The format is intentionally simple and human-first.
Tracking starts with the community-docs baseline for this repository.

## [Unreleased]

## [0.2.0] - 2026-04-10

### Added

- federation export registry owner slice and stronger source-owned federation
  spine review surfaces
- bounded ToS adjunct and third-wave stress/regrounding surfaces together with
  refreshed technique-lift coverage
- via negativa KAG checklist and repo-local project-foundation skill install

### Changed

- aligned KAG generation and validation contracts with the current pinned donor
  inputs and public techniques contour
- clarified validation routes and AGENTS guidance around next-wave
  regrounding posture and source-first entry paths

## [0.1.0] - 2026-04-01

First public baseline release of `aoa-kag` as the derived knowledge substrate layer in the AoA public surface.

This changelog entry uses the release-prep merge date.

### Summary

- first public baseline release of `aoa-kag` as the provenance-aware derived substrate layer for AoA
- the public baseline now includes a manifest-driven registry, technique lift pack, ToS-derived chunk and route packs, reasoning-handoff and return-regrounding packs, federation spine surfaces, counterpart review surfaces, and a tiny consumer bundle
- this release keeps source ownership explicit by treating `aoa-kag` as derived structure rather than authored authority

### Added

- community-docs baseline established for this repository
- `CHANGELOG.md`, `CODE_OF_CONDUCT.md`, and `SECURITY.md`
- manifest-driven KAG generation via `manifests/kag_registry.json`, `manifests/technique_lift_pack.json`, and `scripts/generate_kag.py`
- first generated technique lift pack for `AOA-K-0001` through `AOA-K-0004`
- validation coverage for generated outputs and technique lift pack drift
- federation KAG readiness doctrine and `federation-kag-export` schema/example
- experimental `federation_spine` manifest, generated outputs, and validator coverage for `AOA-K-0009`
- source-owned export dependency contract via `manifests/source_owned_export_dependencies.json`
- `docs/CONSUMER_GUIDE.md` and `scripts/release_check.py`
- stdlib `unittest` coverage for helper functions, builder parity, dependency failures, and projection pairing failures
- `docs/COUNTERPART_CONSUMER_CONTRACT.md`, `schemas/counterpart-consumer-contract.schema.json`, and `examples/counterpart_consumer_contract.example.json`
- `manifests/tiny_consumer_bundle.json`, `generated/tiny_consumer_bundle.json`, and `generated/tiny_consumer_bundle.min.json`
- `docs/COUNTERPART_FEDERATION_EXPOSURE_REVIEW.md`, `manifests/counterpart_federation_exposure_review.json`, and generated review outputs

### Changed

- `AOA-K-0009` now covers a two-repo experimental spine pilot for `aoa-techniques` and `Tree-of-Sophia`
- `generated/federation_spine.json` and `generated/federation_spine.min.json` now publish the current source-owned ToS tiny-entry seam beside the existing `aoa-techniques` donor surfaces
- federation spine doctrine and public entry docs now describe the two-donor pilot as already consumable downstream while it remains experimental and non-authoritative
- `manifests/cross_source_node_projection.json` now declares explicit `projection_pairings` instead of leaving the current pilot pairing implicit in generator code
- reasoning handoff doctrine, example, and generated pack now name the counterpart consumer contract explicitly instead of leaving the first `counterpart_refs` consumer implicit
- counterpart consumer contract and tiny consumer bundle now carry an explicit federation exposure review ref while `AOA-K-0008` remains planned
- counterpart activation gates now treat federation exposure as review-closed for the planned posture rather than leaving it implicit
- ToS tiny-entry route consumption now accepts `bounded_hop` as the primary hop field and keeps `lineage_or_context_hop` as a compatibility alias during the current transition window

### Included in this release

- manifest-driven KAG registry and pack inputs under `manifests/`
- generated lift, retrieval, reasoning, recurrence, federation, counterpart-review, and consumer outputs under `generated/`
- source-aware validation and generation helpers under `scripts/release_check.py`, `scripts/generate_kag.py`, and `scripts/validate_kag.py`

### Validation

- `python scripts/release_check.py`

### Notes

- this release remains a repository release of derived substrate contracts and generated packs rather than a graph engine, runtime service, or source-authority layer
