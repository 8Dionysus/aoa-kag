# RPG Parts

This file is the active map for KAG RPG part pressure.

No part directories are active yet.

## What a part means here

A part is a bounded adjunct vocabulary route with canonical ids, owner refs,
allowed labels, stop-lines, and validation.

## Candidate part pressure

No active KAG-specific RPG part pressure is present yet.

If future quest or consumer surfaces need a vocabulary overlay, prove first
that canonical KAG ids and source refs remain stronger than the readable layer.

Current surfaces such as `QUESTBOOK.md`,
`mechanics/questbook/parts/quest-store/docs/questbook-kag-integration.md`,
and `docs/CONSUMER_GUIDE.md` do not define an RPG vocabulary overlay; they are
questbook/docs-owned routing surfaces. That is why this package remains
`no_active_part_dirs` in `mechanics/topology.json`.

Do not create `parts/<part>/` until a real vocabulary route needs its own
contract and validation.
