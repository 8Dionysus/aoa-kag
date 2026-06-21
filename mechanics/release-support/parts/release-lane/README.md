# Release Lane

This part owns the KAG-local release-support contract for release lane posture.

## Owner Route

- command authority: `config/validation_lanes.json`
- public entrypoint: `scripts/release_check.py`
- local part: `mechanics/release-support/parts/release-lane/`

## Stop-Line

The part may validate release posture. It does not become command storage,
GitHub release truth, public claim authority, or deployment state.
