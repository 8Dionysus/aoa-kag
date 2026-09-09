# Releasing `aoa-kag`

`aoa-kag` is released as a bounded derived knowledge substrate that stays subordinate to source-owned meaning.

See also:

- [README](../README.md)
- [CHANGELOG](../CHANGELOG.md)

## Recommended release flow

1. Keep the release bounded to derived KAG surfaces and bridge contracts.
2. Update `CHANGELOG.md` in the `Summary / Validation / Notes` shape.
3. Start from the intended base branch after inventorying any dirty worktree;
   carry forward only the bounded change. Commit one reviewable unit whose
   message names the changed surface.
4. Before push, use the isolated landing-preparation entry documented in
   `docs/validation/COMMAND_AUTHORITY.md`. It converges the root KAG SCC through
   staged temporary state and preserves the caller's Git index. Its receipt is
   preparation evidence only and never replaces a validation lane.
5. Run the repo-level verifier through the release entry in
   `docs/validation/COMMAND_AUTHORITY.md`. The active release command sequence
   lives in `config/validation_lanes.json`; `release_check.py` is the
   entrypoint and worktree stabilizer. It includes source-fast, generated
   parity, and the OS Abyss KAG registry ABI/SBOM-lite/SLSA bundle validator.
   The GitHub workflow has a separate CI-only continuation: it may omit the
   duplicate source-fast invocation only when the preceding job's exact
   same-run receipt fully matches; otherwise it falls back to this complete
   release sequence.
6. Run federation preflight through the owner release route:
   - `aoa release audit /srv/AbyssOS --phase preflight --repo aoa-kag --strict --json`
7. Push only after local release evidence is recorded and open a pull request
   with changed surfaces, validation results, skipped checks, and remaining
   risk. Wait for `Repo Validation` and every required check; a skipped
   required proof is failure, not success. The stable summary accepts only
   verified source-fast, owner-family, and required full-audit evidence, or an
   explicit fail-closed `correctly-not-required` result for an owner-local
   change.
8. Merge through the observed repository-required method after all required
   checks are green (squash is the default when no other method is required).
   If GitHub status or merge authority cannot be observed, stop and report the
   blocker rather than inferring approval.
9. After landing, return to the default branch, synchronize only from the
   observed remote state, and confirm a clean worktree. Preparation is not
   proof; post-landing sync is not owner acceptance.

Publish only through `aoa release publish`.
