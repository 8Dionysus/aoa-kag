# AGENTS.md

## Applies to

This card applies to `quests/` and all descendants unless a nearer
`AGENTS.md` narrows the path.

## Role

`quests/` is the source quest record district for durable KAG-layer obligations.
It keeps `aoa-kag` follow-through public-safe, lane-first, and lifecycle-aware:

```text
quests/<lane>/<state>/<quest-file>
```

`QUESTBOOK.md` is the human open-obligation index. `mechanics/questbook/` owns
questbook operation law, schemas, examples, validators, and focused tests.

## Read before editing

Read root `AGENTS.md`, `QUESTBOOK.md`, `quests/README.md`, this card, the
nearest lane route, and `mechanics/questbook/parts/quest-store/README.md`
before changing quest records.

## Boundaries

- Do not put source quest records inside mechanics parts.
- Do not keep active source records as root `quests/AOA-KAG-Q-*.yaml` aliases.
- Do not store private scratch, raw transcripts, hidden graph state, secrets,
  source corpus bodies, or runtime evidence here.
- Do not use quests as a second roadmap or as proof of owner acceptance.
- Route proof to `aoa-evals`, memory truth to `aoa-memo`, routing authority to
  `aoa-routing`, and authored source meaning to the owning source repo.

## Validation

After changing quests or quest route docs, run:

```bash
python mechanics/questbook/parts/quest-store/scripts/validate_quest_store.py
python -m unittest discover -s mechanics/questbook/parts/quest-store/tests -p 'test_*.py'
python scripts/validate_kag.py
```

## Closeout

Report quest IDs changed, lane/state paths, whether `QUESTBOOK.md` changed,
whether quest catalog or dispatch examples changed, checks run, skipped checks,
and any stronger-owner acceptance still missing.
