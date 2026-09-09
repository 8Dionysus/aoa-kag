# Quest Store Validation

Use root `VALIDATION.md`, `docs/validation/COMMAND_AUTHORITY.md`, and the nearest `AGENTS.md` for task-conditional validation routes.

The root `scripts/validate_kag.py` route delegates quest-store validation here
so existing release lanes keep working while questbook mechanics owns the
focused contract.

Focused validator: `python mechanics/questbook/parts/quest-store/scripts/validate_quest_store.py`.
