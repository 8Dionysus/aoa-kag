# Questbook Parts

This file is the active map for KAG Questbook parts.

## What a part means here

A part is a bounded questbook sub-route with a source contract, owner split,
allowed generated views, and validation. It should not become a second
roadmap, backlog, or private notes area.

## Active parts

| Part | Owns | Current route |
| --- | --- | --- |
| `quest-store` | focused validation for KAG-local quest source shape, public index posture, and quest catalog/dispatch example alignment | `mechanics/questbook/parts/quest-store/` |

## Candidate part pressure

| Candidate part | Use when | Current route |
| --- | --- | --- |
| `public-index` | root quest frontier or obligation summary changes. | `QUESTBOOK.md` and `parts/quest-store/docs/questbook-kag-integration.md`. |
| `quest-store` | KAG-local quest objects change. | active part route in `mechanics/questbook/parts/quest-store/`. |
| `quest-dispatch` | generated examples or dispatch posture changes. | part-local quest catalog and dispatch examples, schemas, validators, and tests. |

Do not create additional `parts/<part>/` until moving quest artifacts would
make the source, generated view, and validation boundaries clearer than the
active quest-store route.
