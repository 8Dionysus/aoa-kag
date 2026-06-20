# Method Growth Parts

This file is the active map for KAG method-growth part pressure.

## What a part means here

A part is a bounded pattern-growth route with lineage, owner, promotion,
retirement, stop-lines, and validation.

## Candidate part pressure

| Part | Use when | Current route |
| --- | --- | --- |
| `pattern-candidate-lineage` | repeated local signals become KAG pattern candidates. | active: `parts/pattern-candidate-lineage/` docs, schemas, examples, tests. |
| `promotion-dossier` | a KAG pattern asks for stronger review. | active: `parts/promotion-dossier/` docs, schemas, examples, tests. |
| `owner-downlink` | a KAG pattern routes toward owner-local adoption. | active: `parts/owner-downlink/` docs, schemas, examples, tests. |
| `retirement` | a pattern must be pruned, retired, or superseded. | active: `parts/retirement/` docs, schemas, examples, tests. |

Do not create additional `parts/<part>/` directories until moving the owning
artifacts would clarify lineage and owner routing.
