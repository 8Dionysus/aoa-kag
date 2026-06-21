# Agon Parts

This file is the active map for Agon KAG part pressure.

## What a part means here

A part is a bounded sub-mechanic with a clear KAG payload class, owner split,
stop-lines, and local validation. It is not a topic folder and not a place to
hide root scripts.

When a part becomes active, it should own:

- `README.md` for entry;
- `CONTRACT.md` for allowed outputs and stop-lines;
- `VALIDATION.md` or nearest `AGENTS.md` validation route;
- only the schemas, examples, config, generated companions, scripts, or tests
  that belong inside that part boundary.

## Candidate part pressure

| Part | Use when | Active route |
| --- | --- | --- |
| `promotion-candidates` | Agon-derived pattern families ask for KAG candidate review. | `parts/promotion-candidates/README.md`, `CONTRACT.md`, `VALIDATION.md`; part-local config, manifests, scripts, docs, generated registry, schemas, examples, and tests. |
| `sophian-threshold-packets` | Agon KAG candidates ask whether a Sophian review packet is possible. | `parts/sophian-threshold-packets/README.md`, `CONTRACT.md`, `VALIDATION.md`; part-local config, manifests, scripts, docs, generated registry, schemas, examples, and tests. |

Do not create additional `parts/<part>/` directories until the new slice has a
local contract, validation route, and artifacts that are clearer inside the
part than in root KAG districts.
