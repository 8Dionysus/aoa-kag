# KAG Maturity Hardening

## Index Metadata

- Decision ID: AOA-KAG-D-0001
- Original date: 2026-04-13
- Surface classes: docs/governance, generated/maturity, manifests, validation
- KAG surfaces: maturity governance, owner wait states, proof expectations, stop-rule
- Source lanes: aoa-kag, Tree-of-Sophia, aoa-memo, aoa-evals, aoa-playbooks, aoa-agents, aoa-routing
- Guard families: source-owned authority, maturity stop-rule, owner wait state, quarantine and re-entry
- Posture: accepted

## Context

`aoa-kag` had grown beyond bootstrap and was publishing multiple bounded
derived families, live donor activation posture, reasoning handoff seams, and
regrounding surfaces.

That growth created a new risk: the repository could keep widening even when
the next real dependency belonged in another owner repo.

## Decision

`aoa-kag` will harden around one maturity-governance rule:

- donor onboarding must be manifest-driven;
- every live surface must carry an explicit stability tier;
- every live surface must have re-entry and quarantine posture;
- owner wait states must be named explicitly;
- proof expectations must be named explicitly;
- new `AOA-K-*` surfaces must pass a stop-rule before landing.

## Options Considered

- Keep widening KAG surfaces whenever useful derived structure appears.
- Move maturity and wait-state language into a neighboring source or proof repo.
- Keep the governance rule in `aoa-kag`, while making it explicitly weaker than
  source ownership and proof ownership.

## Rationale

This path was chosen because it lets `aoa-kag` become strong enough to stop.

Without that rule, the repo would keep absorbing pressure that properly belongs
to:

- `Tree-of-Sophia` for source-authored growth;
- `aoa-memo` for memory readiness;
- `aoa-evals` for bounded proof;
- `aoa-playbooks` for scenario composition;
- `aoa-agents` for role and runtime posture;
- `aoa-routing` for navigation activation.

## Consequences

Good consequences:

- KAG growth becomes easier to review;
- downstream consumers get clearer stability signals;
- stress and drift can narrow posture honestly;
- neighboring owner repos keep their stronger authority.

Tradeoffs:

- new KAG surfaces will land more slowly;
- some future growth will wait on owner-side exports or proof bundles;
- more governance data must stay aligned with manifests and validators.

## Source Surfaces

This decision is carried by:

- `docs/KAG_MATURITY_GOVERNANCE.md`
- `docs/KAG_OWNER_WAIT_STATES.md`
- `docs/KAG_PROOF_EXPECTATIONS.md`
- `generated/kag_maturity_governance.min.json`

Those docs define the living rule. This note explains why the rule exists.

## Validation

Run:

```bash
python scripts/generate_decision_indexes.py --check
python scripts/validate_decision_records.py
python scripts/validate_kag.py
```
