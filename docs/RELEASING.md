# Releasing `aoa-kag`

`aoa-kag` is released as a bounded derived knowledge substrate that stays subordinate to source-owned meaning.

See also:

- [README](../README.md)
- [CHANGELOG](../CHANGELOG.md)

## Recommended release flow

1. Keep the release bounded to derived KAG surfaces and bridge contracts.
2. Update `CHANGELOG.md` in the `Summary / Validation / Notes` shape.
3. Before push, use the isolated landing-preparation entry documented in
   `docs/validation/COMMAND_AUTHORITY.md`. It converges the root KAG SCC through
   staged temporary state and preserves the caller's Git index. Its receipt is
   preparation evidence only and never replaces a validation lane.
4. Run the repo-level verifier through the release entry in
   `docs/validation/COMMAND_AUTHORITY.md`. The active release command sequence
   lives in `config/validation_lanes.json`; `release_check.py` is the
   entrypoint and worktree stabilizer. It includes source-fast, generated
   parity, and the OS Abyss KAG registry ABI/SBOM-lite/SLSA bundle validator.
   The GitHub workflow has a separate CI-only continuation: it may omit the
   duplicate source-fast invocation only when the preceding job's exact
   same-run receipt fully matches; otherwise it falls back to this complete
   release sequence.
5. Run federation preflight:
   - `aoa release audit /srv/AbyssOS --phase preflight --repo aoa-kag --strict --json`
6. Publish only through `aoa release publish`.
