# Quest Store

## Mechanic card

Status: active Questbook part for KAG-local quest source validation.

### Trigger

Use this part when `QUESTBOOK.md`, `quests/`, quest-store schemas, or
quest-store catalog and dispatch examples change.

### Local owns

The part owns the focused validator and tests that keep KAG-local quest source
records public-safe, owner-routed, schema-backed, and aligned with their
catalog/dispatch example views.

### Stronger owner split

`QUESTBOOK.md` and `quests/` remain the source records. This part's `schemas/`
directory owns quest-store payload contracts. This part's `examples/` directory
owns public-safe illustrative views. Owner repositories own acceptance, proof,
implementation, and closure.

### Inputs

Root quest index, lane/state quest YAML records, quest-store schemas,
quest-store catalog and dispatch examples, and the integration doc.

### Outputs

Validation result and source-route failure messages. No generated payload is
written by this part.

### Must not claim

Owner acceptance, proof closure, implementation activation, roadmap replacement,
private scratch authority, generated-view authority, or source truth outside
`aoa-kag`.

### Next route

Change the source record first, then run this part's validator. Use root
`scripts/validate_kag.py` only as the compatibility entrypoint for repo-wide
validation.
