# Decision Records Index

This directory is the durable decision surface for `aoa-kag`.

Use it when a future contributor needs the rationale for a derived-substrate
boundary, source-ref posture, generated-pack route, manifest policy, validator
guard, maturity stop-rule, quarantine posture, bridge handoff, or regrounding
seam.

Ordinary implementation notes, generated output, runtime logs, private
evidence, proof verdicts, source-authored meaning, and one-off planning thoughts
route to their owning surfaces instead.

## Operating Card

| Field | Route |
| --- | --- |
| role | durable KAG decision rationale entrypoint and index chooser |
| input | changed KAG boundary, source-ref posture, generated-pack policy, manifest route, validation guard, owner wait state, bridge handoff, quarantine, or regrounding pressure |
| output | canonical decision note, generated lookup indexes, and route back to the owning KAG or source-owner surface |
| owner | `docs/decisions/AGENTS.md` for lane law; decision notes for rationale; generated indexes for lookup only |
| next route | owning generated/schema/example/script/test surface first, then nearest route card, `README.md`, `ROADMAP.md`, generated lookup indexes, or the affected source owner |
| validation | `python scripts/generate_decision_indexes.py --check` and `python scripts/validate_decision_records.py`, plus the owning validator for the changed surface |

## Authority

Decision notes explain why a KAG route was chosen.

They are weaker than the source surface they describe:

- generated KAG outputs stay in `generated/`;
- source-controlled inputs stay in `manifests/`;
- schema contracts stay in `schemas/`;
- example contracts stay in `examples/`;
- build and validation behavior stays in `scripts/`;
- regression proof stays in `tests/`;
- KAG direction stays in `README.md`, `ROADMAP.md`, and current model docs;
- source repositories keep stronger truth for authored technique, skill, eval,
  memory, role, playbook, routing, center, runtime, and Tree of Sophia meaning.

Generated decision indexes are weaker than the decision notes. They exist to
make lookup cheaper for agents, not to carry decision rationale.

## Index Shape

Each decision owns:

- a canonical `Decision ID: AOA-KAG-D-####`;
- a full canonical-ID filename, for example `AOA-KAG-D-0001-*.md`;
- an `## Index Metadata` block naming original date, surface classes, KAG
  surfaces, source lanes, guard families, and posture.

The lookup indexes under [indexes](indexes/README.md) are generated from that
metadata:

- [Decisions by canonical ID and number](indexes/by-number.md)
- [Decisions by date](indexes/by-date.md)
- [Decisions by surface class](indexes/by-surface.md)
- [Decisions by KAG surface](indexes/by-kag-surface.md)
- [Decisions by source lane](indexes/by-source-lane.md)
- [Decisions by validation or guard family](indexes/by-guard.md)

Regenerate the read models after decision metadata changes:

```bash
python scripts/generate_decision_indexes.py
```

Check generated parity before closeout:

```bash
python scripts/generate_decision_indexes.py --check
```

## Lookup Route

Do not hand-maintain a "latest decision" roster in this README. That list drifts
as soon as a new decision lands.

Use the generated indexes instead:

- [by number](indexes/by-number.md) for the complete canonical ledger;
- [by date](indexes/by-date.md) for recent landings;
- [by surface](indexes/by-surface.md), [by KAG surface](indexes/by-kag-surface.md),
  and [by source lane](indexes/by-source-lane.md) for route-pressure lookup;
- [by guard](indexes/by-guard.md) for validation, owner-boundary,
  generated-output, source-authority, maturity, quarantine, or regrounding
  pressure.

## Addressing

Full canonical-ID decision paths are the active source files:

- `docs/decisions/AOA-KAG-D-0001-*.md`
- `docs/decisions/AOA-KAG-D-0002-*.md`
- `docs/decisions/AOA-KAG-D-####-*.md`

Canonical IDs remain stable handles. Previous path names belong to git, PR, or
release history, not to a compatibility lookup layer.

## Naming

Use the full canonical decision ID as the filename prefix:

`AOA-KAG-D-0001-short-decision-slug.md`

Prefer short titles that name the KAG route, not the whole debate.

## Template

Start from [TEMPLATE.md](TEMPLATE.md) for new decisions. Keep notes concise, but
include enough context, options, rationale, consequences, source surfaces, and
validation for a future agent to avoid repeating the same route question.
