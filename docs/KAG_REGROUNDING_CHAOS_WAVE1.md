# KAG Regrounding Chaos Wave 1

This wave lands the `aoa-chaos-wave1` retrieval-outage honesty family in
`aoa-kag`.

It uses the projection-health and regrounding adjuncts already owned here.
It does not invent a new runtime substrate, a routing surface, or eval truth.

## Why it matters

Retrieval outage honesty is not only a runtime concern.
When a derived substrate is stale, quarantined, or missing, consumers need a
source-first posture and a bounded regrounding path.

## What to preserve

- KAG owns projection-health truth
- KAG owns regrounding truth
- routing may point to those surfaces, but not invent them
- playbooks may compose around them, but not replace them

## This landing

The generic seed family is mapped onto the real neighboring surfaces that
matter in the current repository contour:

- `examples/projection_health_receipt.retrieval-outage-honesty.example.json`
- `examples/regrounding_ticket.retrieval-outage-honesty.example.json`
- `generated/return_regrounding_pack.min.json`
- `generated/reasoning_handoff_pack.min.json`

That mapping is intentional.
`aoa-kag` already owns the return and handoff adjuncts that can honestly narrow
consumer posture while pointing callers back toward stronger playbook and eval
surfaces.

## Boundary note

The example family is still cross-repo in meaning, but the landed refs stay
inside the current visible KAG neighborhood:

- `aoa-playbooks` owns the runtime-chaos lane and re-entry gate
- `aoa-evals` owns trace-bridge and proof doctrine
- `aoa-kag` owns the projection-health receipt and regrounding ticket

This wave therefore makes source-first recovery more legible without pretending
that KAG now owns runtime repair or verdict logic.
