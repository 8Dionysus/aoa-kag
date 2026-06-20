# Antifragility Parts

This file is the active map for KAG antifragility parts.

## What a part means here

A part is a bounded degraded-mode or recovery route with a symptom class,
source refs, allowed KAG output, stop-lines, and validation.

## Active parts

| Part | Use when | Current route |
| --- | --- | --- |
| `projection-health` | a generated projection needs health or source-first stress posture. | active: `parts/projection-health/` |
| `projection-quarantine` | a KAG surface must pause or isolate overclaim. | active: `parts/projection-quarantine/` |
| `retrieval-outage-regrounding` | retrieval weakens and consumers need source-first return. | active: `parts/retrieval-outage-regrounding/` |

Do not create `parts/<part>/` until moving the owning artifacts would reduce
stress-route ambiguity and add focused validation.
