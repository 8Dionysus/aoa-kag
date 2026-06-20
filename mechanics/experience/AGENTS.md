# AGENTS.md

## Applies to

This card applies to `mechanics/experience/` and all descendants.

## Role

`mechanics/experience/` is the KAG-local route for experience-derived
governance, service, office, release, installation, and pattern pressure that
KAG can represent without owning lived operation.

## Read before editing

Read root `AGENTS.md`, `DESIGN.md`, `mechanics/AGENTS.md`,
`mechanics/README.md`, this package `README.md`, `PARTS.md`, and
`PROVENANCE.md`. Then read the experience doc, schema, example, or test being
changed.

## Boundaries

- KAG represents experience-derived patterns; it does not own lived experience.
- Owner repositories accept or reject adoption.
- `aoa-evals` owns certification proof.
- Only the parts listed in `PARTS.md` and `mechanics/topology.json` are active.
  Additional part directories need a part-local experience contract and
  validator first.

## Validation

Run `python scripts/validate_mechanics_skeleton.py`.
If experience contracts move, run their focused tests and the release gate.
When changing an active part payload, run that part's `VALIDATION.md`.

## Closeout

Name the experience route changed, owner adoption boundary preserved, checks
run, skipped checks, and next owner route.
