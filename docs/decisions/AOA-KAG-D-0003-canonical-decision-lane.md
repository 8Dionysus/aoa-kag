# Canonical Decision Lane

## Index Metadata

- Decision ID: AOA-KAG-D-0003
- Original date: 2026-06-04
- Surface classes: docs/decisions, scripts/validation, tests/decision-indexes
- KAG surfaces: decision lane, generated indexes, derived-substrate boundary
- Source lanes: aoa-kag, sibling decision lanes
- Guard families: canonical ID, generated index parity, source-owned authority, derived-substrate boundary
- Posture: accepted

## Context

`aoa-kag` already had decision notes, but they used date-slug filenames and no
generated lookup contract. That made the lane useful for humans but weaker than
the refactored sibling pattern: future agents could not cheaply validate
canonical IDs, index freshness, or lookup dimensions.

KAG also has a local naming pressure: public derived payloads use `AOA-K-*`, but
repo-local work quests use `AOA-KAG-Q-*`. Decision records therefore need the
repo-local organ namespace, not the generated-payload namespace.

## Decision

`aoa-kag` will carry durable rationale as canonical `AOA-KAG-D-####` decision
records with generated indexes under `docs/decisions/indexes/`.

The lane indexes surface classes, KAG surfaces, source lanes, guard families,
date, posture, and canonical path. It does not preserve retired date-slug paths
as active compatibility surfaces; those paths remain in git and PR history.

## Options Considered

- Keep date-slug decision files and manually maintain `docs/decisions/README.md`.
- Rename decisions without generated indexes or validation.
- Adopt the sibling generated-index pattern with a KAG-local namespace and KAG
  metadata dimensions.

## Rationale

The generated-index pattern gives `aoa-kag` the same durable lookup posture as
the refactored sibling repos while preserving local truth: KAG decisions are
about derived-substrate boundaries, source refs, generated packs, manifests,
validators, maturity, quarantine, and regrounding.

Using `AOA-KAG-D` keeps decisions separate from generated `AOA-K-*` payloads and
aligned with existing `AOA-KAG-Q` quest IDs.

## Consequences

Good consequences:

- decision lookup is generated, deterministic, and cheap for agents;
- decision IDs become stable handles for future rationale and supersession;
- validators can catch stale indexes, bad metadata, wrong prefixes, and path
  drift;
- source repositories still own authored meaning and KAG remains derived.

Tradeoffs:

- new decision records need metadata discipline;
- old date-slug paths are no longer active source files;
- generated indexes must be refreshed when decision metadata changes.

## Source Surfaces

- `docs/decisions/AGENTS.md`
- `docs/decisions/README.md`
- `docs/decisions/indexes/index_contract.yaml`
- `scripts/generate_decision_indexes.py`
- `scripts/validate_decision_records.py`
- `tests/test_decision_indexes.py`

## Validation

Run:

```bash
python scripts/generate_decision_indexes.py
python scripts/generate_decision_indexes.py --check
python scripts/validate_decision_records.py
python -m unittest tests.test_decision_indexes
```
