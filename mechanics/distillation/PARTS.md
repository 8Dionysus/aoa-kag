# Distillation Parts

This file is the active map for KAG distillation part pressure.

## What a part means here

A part is a bounded lift route with source refs, projection scope, generated
outputs, stop-lines, and validation.

## Candidate part pressure

| Candidate part | Use when | Current route |
| --- | --- | --- |
| `technique-lift` | technique source sections become derived KAG lift packs. | technique lift manifest, generated pack, docs, schemas, tests. |
| `tos-text-chunk-map` | ToS source text receives bounded chunk mapping. | ToS text chunk manifest, generated pack, docs, schemas, tests. |
| `tos-route-lift` | ToS route-local surfaces become KAG route or retrieval packs. | ToS route manifests, generated packs, schemas, docs, tests. |

## Active part routes

| Active part | Owns | Validation |
| --- | --- | --- |
| `technique-lift` | AOA-K-0001 through AOA-K-0004 technique lift operation contract | `parts/technique-lift/VALIDATION.md` |
| `tos-text-chunk-map` | AOA-K-0005 ToS chunk-map operation contract | `parts/tos-text-chunk-map/VALIDATION.md` |
| `tos-route-lift` | AOA-K-0010 ToS route pack operation contract | `parts/tos-route-lift/VALIDATION.md` |

Retrieval-handle behavior for AOA-K-0007 and AOA-K-0011 is bridge ownership
and lives under `mechanics/boundary-bridge/parts/tos-retrieval-axis/`.
