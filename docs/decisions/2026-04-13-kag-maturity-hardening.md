# KAG Maturity Hardening Decision

## Context

`aoa-kag` has grown beyond bootstrap and now publishes multiple bounded derived
families, live donor activation posture, reasoning handoff seams, and
regrounding surfaces.

That growth creates a new risk:
the repository can keep widening even when the next real dependency belongs in
another owner repo.

## Decision

`aoa-kag` will harden around one maturity-governance rule:

- donor onboarding must be manifest-driven
- every live surface must carry an explicit stability tier
- every live surface must have re-entry and quarantine posture
- owner wait states must be named explicitly
- proof expectations must be named explicitly
- new `AOA-K-*` surfaces must pass a stop-rule before landing

## Why

This path was chosen because it lets `aoa-kag` become strong enough to stop.

Without that rule, the repo would keep absorbing pressure that properly belongs
to:

- `Tree-of-Sophia` for source-authored growth
- `aoa-memo` for memory readiness
- `aoa-evals` for bounded proof
- `aoa-playbooks` for scenario composition
- `aoa-agents` for role and runtime posture
- `aoa-routing` for navigation activation

## Consequences

Good consequences:

- KAG growth becomes easier to review
- downstream consumers get clearer stability signals
- stress and drift can narrow posture honestly
- neighboring owner repos keep their stronger authority

Tradeoffs:

- new KAG surfaces will land more slowly
- some future growth will wait on owner-side exports or proof bundles
- more governance data must stay aligned with manifests and validators

## Canonical placement

This decision is carried by:

- `docs/KAG_MATURITY_GOVERNANCE.md`
- `docs/KAG_OWNER_WAIT_STATES.md`
- `docs/KAG_PROOF_EXPECTATIONS.md`

Those docs define the living rule.
This note explains why the rule exists.
