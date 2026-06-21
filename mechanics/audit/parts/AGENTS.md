# Audit Parts Agents

## Applies to

This card applies to `mechanics/audit/parts/` and all active audit part
descendants.

## Role

Audit parts own bounded KAG evidence-visibility, proof-ref, and exposure-review
routes while leaving verdicts and owner acceptance with stronger owners.

## Read before editing

Read the package `AGENTS.md`, `README.md`, `PARTS.md`, `PROVENANCE.md`, and the
nearest part `CONTRACT.md`.

## Boundaries

Do not turn audit refs into proof verdicts, owner acceptance, source
remediation, runtime evidence, or activation authority.

## Validation

Run the nearest part tests and then the mechanics skeleton validator. Generated
parity still runs through the repo-wide generated lane.

## Closeout

Name the audit route touched, stronger owner preserved, focused tests run, and
whether generated parity or release checks were needed.
