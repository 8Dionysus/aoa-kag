# Recurrence Parts

This file is the active map for KAG recurrence part pressure.

No part directories are active yet.

## What a part means here

A part is a bounded return mechanism with a named drift symptom, source refs,
owner refs, allowed derived output, and validation. It should not become a
hidden scheduler or memory layer.

## Candidate part pressure

| Candidate part | Use when | Current route |
| --- | --- | --- |
| `return-regrounding` | generated KAG consumers need a safe return to stronger refs. | `manifests/return_regrounding_pack.json`, generated return pack, schema, examples, docs, and tests. |
| `recurrence-projection-inputs` | recurrence hints must stay owner-routed. | `docs/RECURRENCE_PROJECTION_INPUTS.md` and related generated inputs. |
| `retrieval-drift-reentry` | retrieval-axis or cross-source projection drifts toward source replacement. | regrounding examples, projection health receipts, and source-first docs. |

Do not create `parts/<part>/` until moving the owning artifacts would make the
return path safer and easier to validate.
