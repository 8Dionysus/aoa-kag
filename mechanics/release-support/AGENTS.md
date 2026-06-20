# AGENTS.md

## Applies to

This card applies to `mechanics/release-support/` and all descendants.

## Role

`mechanics/release-support/` is the KAG-local route for release contour,
artifact identity, generated parity, and public support posture around bounded
KAG releases.

## Read before editing

Read root `AGENTS.md`, `DESIGN.md`, `mechanics/AGENTS.md`,
`mechanics/README.md`, this package `README.md`, `PARTS.md`, and
`PROVENANCE.md`. Then read the release, lane, generated, or public claim
surface being changed.

## Boundaries

- Release support does not widen source authority.
- Generated parity does not become source truth.
- Public claims need current validation and owner evidence.
- No part directory is active until a part-local release-support contract and validator exist.

## Validation

Run `python scripts/validate_mechanics_skeleton.py`.
For release-facing changes, run `python scripts/release_check.py`.

## Closeout

Name release-support surfaces changed, generated parity status, checks run,
skipped checks, and next owner route.
