# Growth Cycle Parts

This file is the active map for KAG growth-cycle part pressure.

No part directories are active yet.

## What a part means here

A part is a bounded growth route with status vocabulary, owner waits, proof
gaps, stop-lines, and validation.

## Candidate part pressure

| Candidate part | Use when | Current route |
| --- | --- | --- |
| `owner-wait-state` | KAG surfaces wait on stronger owner exports or proof. | owner wait docs, maturity manifest, generated pack, tests. |
| `surface-growth-stop-rule` | new `AOA-K-*` growth must stay paused or justified. | maturity governance docs, decision D-0001, roadmap, generated pack. |

Do not create `parts/<part>/` until moving the owning artifacts would make
growth posture clearer.
