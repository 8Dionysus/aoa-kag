# Release Support Parts

This file is the active map for KAG release-support part pressure.

No part directories are active yet.

## What a part means here

A part is a bounded release route with claim, artifact identity, validation,
rollback or return posture, and owner evidence boundaries.

## Candidate part pressure

| Candidate part | Use when | Current route |
| --- | --- | --- |
| `release-lane` | release command authority or workflow posture changes. | `config/validation_lanes.json`, `scripts/release_check.py`, workflow tests. |
| `artifact-identity` | generated release artifacts need identity and drift checks. | federation spine artifact identity, generated parity checks. |
| `release-contour` | public release posture or roadmap contour changes. | `README.md`, `ROADMAP.md`, `docs/RELEASING.md`, release tests. |

Do not create `parts/<part>/` until moving the owning artifacts would clarify
release support and validation.
