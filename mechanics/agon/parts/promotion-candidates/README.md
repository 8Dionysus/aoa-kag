# Promotion Candidates

This part owns the KAG-side promotion-candidate registry for Agon-derived pattern
families.

## Role

It accepts reviewed candidate shapes into a non-authoritative KAG registry and
keeps the path back to stronger owner review visible.

## Inputs

- `config/promotion-candidate-registry.source.json`
- root schemas for `agon-kag-candidate`
- root examples for Agon candidate payload shape
- owner review, memo evidence, eval alignment, and recurrence support refs

## Outputs

- `generated/agon_kag_promotion_candidate_registry.min.json`
- focused validation output from this part's validator and test

## Stop-lines

This part does not promote candidates, write canon, mutate rank or trust, create
arena runtime effects, accept proof verdicts, or replace owner source truth.

## Next route

Use [CONTRACT](CONTRACT.md) for payload rules, [VALIDATION](VALIDATION.md) for
checks, and [Agon provenance](../../PROVENANCE.md) for former root path
accounting.
