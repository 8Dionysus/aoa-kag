# Questbook Parts

This file is the active map for KAG Questbook part pressure.

No part directories are active yet.

## What a part means here

A part is a bounded questbook sub-route with a source contract, owner split,
allowed generated views, and validation. It should not become a second
roadmap, backlog, or private notes area.

## Candidate part pressure

| Candidate part | Use when | Current route |
| --- | --- | --- |
| `public-index` | root quest frontier or obligation summary changes. | `QUESTBOOK.md` and `docs/QUESTBOOK_KAG_INTEGRATION.md`. |
| `quest-store` | KAG-local quest objects change. | `quests/`, quest schemas, and `scripts/validate_kag.py`. |
| `quest-dispatch` | generated examples or dispatch posture changes. | quest catalog and dispatch examples, schemas, validators, and tests. |

Do not create `parts/<part>/` until moving quest artifacts would make the
source, generated view, and validation boundaries clearer.
