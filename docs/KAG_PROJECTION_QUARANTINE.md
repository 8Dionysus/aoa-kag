# KAG PROJECTION QUARANTINE

## Goal

Make quarantine a bounded honesty mechanism for derived surfaces that are currently unsafe to expand.

Quarantine should reduce confusion, not create mystery.

## When to quarantine

A projection or pack is a quarantine candidate when one or more of the following are true:

- donor dependencies are missing or obviously stale
- validators fail in a way that changes consumer meaning
- cross-source joins look plausible but cannot be re-grounded
- a safer source-first fallback exists and should be preferred

## What quarantine means

Quarantine should do all of the following:

- preserve donor and projection identifiers
- preserve evidence refs
- publish source-fallback refs
- narrow consumer posture
- open or reference a regrounding ticket

Quarantine should not:

- delete provenance
- rewrite source-owned meaning
- pretend the surface is healthy
- silently disappear without review

## How to leave quarantine

A quarantined surface should leave quarantine only when:

1. the regrounding work is explicit
2. the relevant generators or validators pass
3. consumer posture can be widened with cited evidence
4. a reviewer posture, where needed, is satisfied

## Relationship to neighboring surfaces

- routing may choose to route around a quarantined surface
- playbooks may hold or resume recurring routes based on quarantine state
- agents may hand off toward a steward or reviewer when quarantine blocks their lane

## Acceptance shape

A healthy wave-3 landing would make it possible to point to:

- one documented quarantine rule set
- one projection-health receipt that enters quarantine or source-first mode
- one regrounding ticket that explains how the surface becomes usable again
