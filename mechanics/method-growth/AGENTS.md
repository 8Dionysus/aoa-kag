# AGENTS.md

## Applies to

This card applies to `mechanics/method-growth/` and all descendants.

## Role

`mechanics/method-growth/` is the KAG-local route for pattern candidate
lineage, promotion dossiers, owner downlinks, and retirement or pruning of
derived patterns.

## Read before editing

Read root `AGENTS.md`, `DESIGN.md`, `mechanics/AGENTS.md`,
`mechanics/README.md`, this package `README.md`, `PARTS.md`, and
`PROVENANCE.md`. Then read the pattern, promotion, downlink, or retirement
surface being changed.

## Boundaries

- KAG candidates do not become methods by themselves.
- `aoa-playbooks`, `aoa-techniques`, and `aoa-skills` own stronger method,
  technique, or skill truth.
- Owner repositories accept local adoption.
- Only the parts listed in `PARTS.md` and `mechanics/topology.json` are active.
  Additional part directories need a part-local method-growth contract and
  validator first.

## Validation

Run `python scripts/validate_mechanics_skeleton.py`.
If pattern candidate surfaces move, run the target part validation route and
release checks.

## Closeout

Name the method-growth route changed, stronger owner preserved, checks run,
skipped checks, and next owner route.
