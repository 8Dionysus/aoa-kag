# Releasing `aoa-kag`

`aoa-kag` is released as a bounded derived knowledge substrate that stays subordinate to source-owned meaning.

See also:

- [README](../README.md)
- [CHANGELOG](../CHANGELOG.md)

## Recommended release flow

1. Keep the release bounded to derived KAG surfaces and bridge contracts.
2. Update `CHANGELOG.md` in the `Summary / Validation / Notes` shape.
3. Run the repo-level verifier through the release entry in
   `docs/validation/COMMAND_AUTHORITY.md`. The active release command sequence
   lives in `config/validation_lanes.json`; `release_check.py` is the
   entrypoint and worktree stabilizer. It includes source-fast, generated
   parity, and the OS Abyss KAG registry ABI/SBOM-lite/SLSA bundle validator.
4. Run federation preflight:
   - `aoa release audit /srv/AbyssOS --phase preflight --repo aoa-kag --strict --json`
5. Publish only through `aoa release publish`.
