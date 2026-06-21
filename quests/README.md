# Quest Source Records

`quests/` is the source quest record district for `aoa-kag` obligations that
should survive the current diff.

It is not a private scratchpad and not a second roadmap. Direction belongs in
[`ROADMAP.md`](../ROADMAP.md). Human open-obligation visibility belongs in
[`QUESTBOOK.md`](../QUESTBOOK.md). Questbook operation law starts in
[`mechanics/questbook`](../mechanics/questbook/README.md).

Quest sources live in lane-first lifecycle directories:

```text
quests/<lane>/<state>/<quest-file>
```

Top-level `AOA-KAG-Q-*` aliases are intentionally absent. Route directly to the
source file under its lane and lifecycle state.

## Lanes

| Lane | Use |
| --- | --- |
| [`kag/`](kag/README.md) | KAG-local derived-substrate obligations, export gaps, bridge/regrounding follow-through, and bounded projection pilots. |

## Lifecycle States

Each lane may contain:

| State | Use |
| --- | --- |
| `captured/` | Public-safe obligation exists, but route shaping is not complete. |
| `triaged/` | Route-bearing obligation with enough shape to split, promote, or close. |
| `ready/` | Next owner action is clear and bounded. |
| `active/` | Currently being advanced by an owner route. |
| `blocked/` | Waiting on a named dependency or owner decision. |
| `reanchor/` | Old route no longer matches; choose a new owner, band, or evidence path. |
| `done/` | Landed with enough public evidence to leave the active index. |
| `dropped/` | Intentionally closed without landing, with a visible reason. |

## Source And Readers

- `quests/<lane>/<state>/*.yaml` are source quest records.
- `QUESTBOOK.md` is the compact public index for open KAG obligations.
- `mechanics/questbook/parts/quest-store/examples/quest_catalog.min.example.json`
  and `quest_dispatch.min.example.json` are reviewable example readers.

The example readers derive from source quest records. They do not author quest
meaning and they are not runtime authority.
