# Audit Parts

This file is the active map for KAG audit part pressure.

No part directories are active yet.

## What a part means here

A part is a bounded evidence-visibility route with source refs, risk posture,
proof owner, allowed output, and validation.

## Candidate part pressure

| Candidate part | Use when | Current route |
| --- | --- | --- |
| `proof-expectation-refs` | KAG surfaces need explicit proof lanes without owning verdicts. | `docs/KAG_PROOF_EXPECTATIONS.md`, generated maturity pack, tests. |
| `owner-evidence-route` | source-owned exports need evidence or owner freshness review. | source-owned dependency docs, federation readiness docs, validators. |
| `exposure-review` | counterpart or federation exposure must stay reviewed but inactive. | counterpart federation exposure review docs, manifests, generated output, tests. |

Do not create `parts/<part>/` until moving the owning artifacts would make
audit ownership clearer.
