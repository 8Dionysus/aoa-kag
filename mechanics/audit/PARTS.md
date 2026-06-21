# Audit Parts

This file is the active map for KAG audit part pressure.

## What a part means here

A part is a bounded evidence-visibility route with source refs, risk posture,
proof owner, allowed output, and validation.

## Candidate part pressure

| Candidate part | Use when | Current route |
| --- | --- | --- |
| `proof-expectation-refs` | KAG surfaces need explicit proof lanes without owning verdicts. | `mechanics/audit/parts/proof-expectation-refs/docs/kag-proof-expectations.md`, `mechanics/growth-cycle/parts/surface-growth-stop-rule/generated/kag_maturity_governance*.json`, tests. |
| `owner-evidence-route` | source-owned exports need evidence or owner freshness review. | source-owned dependency docs, federation readiness docs, validators. |
| `exposure-review` | counterpart or federation exposure must stay reviewed but inactive. | counterpart federation exposure review docs, manifests, generated output, tests. |

## Active part routes

| Active part | Owns | Validation |
| --- | --- | --- |
| `proof-expectation-refs` | proof expectation refs and proof-owner stop-lines without verdict ownership | `parts/proof-expectation-refs/VALIDATION.md` |
| `exposure-review` | counterpart federation exposure review and planned-only counterpart posture | `parts/exposure-review/VALIDATION.md` |

`owner-evidence-route` remains candidate pressure. Current source-owned export
freshness and donor ingress checks are owned by
`mechanics/boundary-bridge/parts/source-owned-export/` until a separate audit
evidence payload exists.
