# Experience Parts

This file is the active map for KAG experience part pressure.

## What a part means here

A part is a bounded experience-derived route with source refs, owner adoption
boundary, allowed KAG output, and validation.

## Candidate part pressure

| Part | Use when | Current route |
| --- | --- | --- |
| `governance-precedent` | experience governance creates derived precedent candidates. | active: `parts/governance-precedent/` |
| `office-service-patterns` | office or service patterns become KAG candidates. | active: `parts/office-service-patterns/` |
| `release-patterns` | release and installation experience become candidate substrate. | active: `parts/release-patterns/` |

Pattern adoption, owner downlink, promotion dossier, lineage, and retirement
packets route through `mechanics/method-growth/parts/`.

Do not create additional `parts/<part>/` directories until moving the owning
artifacts would clarify the owner boundary and add focused validation.
