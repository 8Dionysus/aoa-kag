# Quest Store Contract

The quest-store part keeps KAG-local Questbook records reviewable without
turning mechanics into the quest source.

It requires:

- `QUESTBOOK.md` to remain the public index for active KAG obligations;
- `quests/<lane>/<state>/*.yaml` to remain schema-backed source records for
  local derived substrate work;
- quest catalog and dispatch examples to stay aligned with lane/state quest
  source records;
- quest integration docs to keep source-owner meaning outside KAG;
- closed quests to stay out of the public active index.

It forbids:

- private scratch notes in quest source surfaces;
- generated examples acting as source truth;
- owner acceptance or proof closure claims without stronger owner evidence;
- active legacy `seed`, `wave`, `stub`, or `landing` naming in part-owned
  paths or payload keys.
