# Reasoning Handoff Validation

Use root `VALIDATION.md`, `docs/validation/COMMAND_AUTHORITY.md`, and the nearest `AGENTS.md` for
task-conditional focused and repo-wide validation routes.

The repo-wide generated lane still checks full handoff-pack parity through the
part-local generated outputs. This part owns the focused checkpoint operation
contract around handoff guardrails, counterpart contract refs, and owner-state
stop-lines.

Focused validator: `python mechanics/checkpoint/parts/reasoning-handoff/scripts/validate_reasoning_handoff.py`.
