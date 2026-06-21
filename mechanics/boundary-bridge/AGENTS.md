# AGENTS.md

## Applies to

This card applies to `mechanics/boundary-bridge/` and all descendants.

## Role

`mechanics/boundary-bridge/` is the KAG-local route for bridge pressure between
source-owned exports, ToS surfaces, memo bridge faces, counterpart edges, and
derived projections.

## Read before editing

Read root `AGENTS.md`, `DESIGN.md`, `mechanics/AGENTS.md`,
`mechanics/README.md`, this package `README.md`, `PARTS.md`, and `PROVENANCE.md`.
Then read the source, manifest, generated, schema, or owner surface named by
the bridge.

## Boundaries

- Bridge outputs do not transfer source authority.
- KAG projections do not become ToS, memo, routing, proof, or runtime truth.
- Counterpart and cross-source surfaces stay non-identity surfaces.
- Active part directories must stay listed in `mechanics/topology.json` and keep
  a part-local bridge contract, validator, and focused tests.

## Validation

Run `python scripts/validate_mechanics_skeleton.py`.
If bridge-generated surfaces move, run the relevant KAG generator, validator,
focused tests, and release gate.
For the active source-owned export part, run
`python mechanics/boundary-bridge/parts/source-owned-export/scripts/validate_source_owned_export.py`.

## Closeout

Name the bridge route changed, source owners preserved, generated refresh
status, checks run, skipped checks, and the next owner route.
