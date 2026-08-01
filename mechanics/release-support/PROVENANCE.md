# Release Support Provenance

Start from this package's `README.md` and `PARTS.md`. Use provenance when a
release-support route needs validation or public claim trace.

## Center source

- `Agents-of-Abyss/mechanics/release-support/README.md`
- `Agents-of-Abyss/mechanics/release-support/PARTS.md`

## KAG source surfaces

- `docs/RELEASING.md`
- `docs/artifact-bundles/kag_registry.bundle.json`
- `config/validation_lanes.json`
- `scripts/release_check.py`
- `scripts/ci_release_check.py`
- `scripts/source_fast_handoff.py`
- `scripts/validate_abyss_machine_kag_registry_bundle.py`
- `ROADMAP.md`
- `README.md`
- generated parity and release workflow tests.

## Active part provenance

- `mechanics/release-support/parts/release-lane/` owns focused validation for
  release lane posture, command-authority delegation, and release entrypoint
  non-duplication.
- `config/validation_lanes.json` remains root-owned command authority.
- `scripts/release_check.py` remains a root public release entrypoint.
- `scripts/ci_release_check.py` remains a root CI-only continuation entrypoint;
  it cannot omit source-fast without exact same-run receipt acceptance and
  otherwise returns to the public full release entrypoint.
- The KAG registry artifact bundle remains root-owned release input because its
  subject is the root public registry readmodel: `generated/kag_registry*.json`,
  `manifests/kag_registry.json`, and `schemas/kag-registry.schema.json`.
  Move future package-local payload bundles into their owning part instead.

No package-local `legacy/` route is active yet.
