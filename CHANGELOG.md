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

### Changed

- `AOA-K-0009` now covers a two-repo experimental spine pilot for `aoa-techniques` and `Tree-of-Sophia`
- `generated/federation_spine.json` and `generated/federation_spine.min.json` now publish the current source-owned ToS tiny-entry seam beside the existing `aoa-techniques` donor surfaces
- federation spine doctrine and public entry docs now describe the downstream `aoa-routing` sync as a separate follow-up wave
