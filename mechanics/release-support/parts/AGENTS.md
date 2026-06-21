# Release Support Parts Agents

## Applies to

This card applies to `mechanics/release-support/parts/` and all active release
support part descendants.

## Role

Release-support parts own bounded release posture contracts while keeping
command authority in the repo-wide validation lane manifest.

## Read before editing

Read the package `AGENTS.md`, `README.md`, `PARTS.md`, `PROVENANCE.md`, and the
nearest part `CONTRACT.md`.

## Boundaries

Do not move full command authority out of `config/validation_lanes.json`.
Public entrypoints under `scripts/` stay repo-wide compatibility surfaces.

## Validation

Run the nearest part tests, the mechanics skeleton validator, and the release
lane when release behavior changes.

## Closeout

Name the release-support route touched, command authority preserved, focused
tests run, and whether release checks were run.
