# Checkpoint Parts

`mechanics/checkpoint/parts/` holds active KAG-local checkpoint sub-mechanics.

Use this home for functioning handoff or return routes with local contracts and
validation. Source docs, manifests, schemas, examples, and generated read
models may stay in their root homes while part-local validation owns the
operation contract around them.

## Active parts

| Part | Route |
| --- | --- |
| `reasoning-handoff` | validates reasoning handoff guardrails, counterpart contract refs, and owner-state stop-lines for generated handoff packs |
