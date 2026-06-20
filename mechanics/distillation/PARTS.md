# Distillation Parts

This file is the active map for KAG distillation part pressure.

No part directories are active yet.

## What a part means here

A part is a bounded lift route with source refs, projection scope, generated
outputs, stop-lines, and validation.

## Candidate part pressure

| Candidate part | Use when | Current route |
| --- | --- | --- |
| `technique-lift` | technique source sections become derived KAG lift packs. | technique lift manifest, generated pack, docs, schemas, tests. |
| `tos-text-chunk-map` | ToS source text receives bounded chunk mapping. | ToS text chunk manifest, generated pack, docs, schemas, tests. |
| `tos-route-lift` | ToS route-local surfaces become KAG route or retrieval packs. | ToS route manifests, generated packs, schemas, docs, tests. |

Do not create `parts/<part>/` until moving the owning artifacts would improve
source-link clarity.
