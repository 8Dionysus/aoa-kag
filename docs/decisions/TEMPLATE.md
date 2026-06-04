# AOA-KAG-D-#### Short Decision Title

## Index Metadata

- Decision ID: AOA-KAG-D-####
- Original date: YYYY-MM-DD
- Surface classes: docs/model
- KAG surfaces: derived substrate
- Source lanes: none
- Guard families: source-owned authority
- Posture: proposed

## Context

What KAG pressure made the decision necessary?

Name the generated, manifest, schema, example, script, test, docs, or upstream
source-owner surfaces that shaped the choice.

## Decision

State the chosen route in one or two paragraphs.

## Options Considered

- Option A:
- Option B:
- Option C:

## Rationale

Explain why this route fits `aoa-kag` as a provenance-aware derived substrate
where source repositories own authored meaning.

## Consequences

Name what becomes easier, what remains constrained, and what future contributors
must not infer from this decision.

## Source Surfaces

- `AGENTS.md`
- `README.md`
- `ROADMAP.md`
- `docs/KAG_MODEL.md`
- `docs/BOUNDARIES.md`
- `docs/SOURCE_POLICY.md`

## Validation

Run:

```bash
python scripts/generate_decision_indexes.py
python scripts/generate_decision_indexes.py --check
python scripts/validate_decision_records.py
```

Also run the validator for the owning surface the decision describes.
