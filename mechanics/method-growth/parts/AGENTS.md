# AGENTS.md

## Applies to

This card applies to `mechanics/method-growth/parts/` and every Method-growth
part below it.

## Role

Method-growth parts own active KAG-side pattern-growth contract packets when
lineage, promotion, owner downlink, or retirement payloads are clearer beside
their operation owner than in root docs, schemas, examples, or tests.

## Read before editing

Read root `AGENTS.md`, `mechanics/AGENTS.md`,
`mechanics/method-growth/AGENTS.md`, `mechanics/method-growth/PARTS.md`,
`mechanics/method-growth/PROVENANCE.md`, this card, and the target part
`README.md`, `CONTRACT.md`, and `VALIDATION.md`.

## Boundaries

- KAG method-growth packets remain derived candidate or handoff surfaces, not
  owner adoption, proof verdict, ToS canon, memory truth, or route execution.
- Part-local schemas and examples are contract packets for the owning part.
- Do not reactivate `seed` or `wave` names in active paths or payload keys.
- Former root paths belong in `mechanics/method-growth/legacy/` accounting.

## Validation

Run the target part test named in `VALIDATION.md`, then:

```bash
python scripts/validate_mechanics_skeleton.py
python scripts/run_tests.py
```

## Closeout

Report the part, moved contract packets, validation commands, whether legacy
accounting changed, skipped checks, and the next owner route.
