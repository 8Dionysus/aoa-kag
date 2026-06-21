# Recurrence Parts

This file is the active map for KAG recurrence part pressure.

## What a part means here

A part is a bounded return mechanism with a named drift symptom, source refs,
owner refs, allowed derived output, and validation. It should not become a
hidden scheduler or memory layer.

## Candidate part pressure

| Candidate part | Use when | Current route |
| --- | --- | --- |
| `return-regrounding` | generated KAG consumers need a safe return to stronger refs. | `mechanics/recurrence/parts/return-regrounding/manifests/return_regrounding_pack.json`, generated return pack, recurrence projection companion, schemas, examples, docs, and tests. |
| `recurrence-projection-inputs` | recurrence hints must stay owner-routed. | folded into `mechanics/recurrence/parts/return-regrounding/docs/recurrence-projection-inputs.md` until a separate part earns its own artifacts and validation. |
| `retrieval-drift-reentry` | retrieval-axis or cross-source projection drifts toward source replacement. | regrounding examples, projection health receipts, and source-first docs. |

## Active part routes

| Active part | Owns | Validation |
| --- | --- | --- |
| `return-regrounding` | focused return mode order, stronger-ref, memo readiness, and source-first return checks | `parts/return-regrounding/VALIDATION.md` |

Do not create another `parts/<part>/` until moving the owning artifacts would
make the return path safer and easier to validate than the current root doc,
manifest, generated, schema, example, or compatibility homes.
