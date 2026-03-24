# Changelog

All notable changes to `aoa-kag` will be documented in this file.

The format is intentionally simple and human-first.
Tracking starts with the community-docs baseline for this repository.

## [Unreleased]

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

### Changed

- `AOA-K-0009` now covers a two-repo experimental spine pilot for `aoa-techniques` and `Tree-of-Sophia`
- `generated/federation_spine.json` and `generated/federation_spine.min.json` now publish the current source-owned ToS tiny-entry seam beside the existing `aoa-techniques` donor surfaces
- federation spine doctrine and public entry docs now describe the two-donor pilot as already consumable downstream while it remains experimental and non-authoritative
- `manifests/cross_source_node_projection.json` now declares explicit `projection_pairings` instead of leaving the current pilot pairing implicit in generator code
- reasoning handoff doctrine, example, and generated pack now name the counterpart consumer contract explicitly instead of leaving the first `counterpart_refs` consumer implicit
