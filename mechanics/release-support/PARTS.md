# Release Support Parts

This file is the active map for KAG release-support part pressure.

## What a part means here

A part is a bounded release route with claim, artifact identity, validation,
rollback or return posture, and owner evidence boundaries.

## Candidate part pressure

| Candidate part | Use when | Current route |
| --- | --- | --- |
| `release-lane` | release command authority or workflow posture changes. | `config/validation_lanes.json`, `scripts/release_check.py`, workflow tests. |
| `artifact-identity` | generated release artifacts need identity and drift checks. | root KAG registry artifact identity, `docs/artifact-bundles/kag_registry.bundle.json`, generated parity checks. |
| `release-contour` | public release posture or roadmap contour changes. | `README.md`, `ROADMAP.md`, `docs/RELEASING.md`, release tests. |

## Active part routes

| Active part | Owns | Validation |
| --- | --- | --- |
| `release-lane` | command-authority delegation and release entrypoint posture | `parts/release-lane/VALIDATION.md` |

`artifact-identity` remains root generated/read-model posture for now because
the current artifact bundle covers the root public KAG registry readmodel rather
than a package-local payload. `release-contour` remains root public docs posture
until it has a distinct payload contract.
