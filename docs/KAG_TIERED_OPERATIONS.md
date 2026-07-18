# Tiered KAG Operations

This runbook covers deterministic build, verification, offline transfer,
degradation, and rollback for one owner family. It does not grant artifact or
runtime authority to `aoa-kag`.

## Preconditions

- Use a clean owner checkout or an isolated worktree.
- Resolve an explicit durable history/base ref.
- Store large CAS objects and packs under the owner-approved
  `/srv/abyss-machine` artifact route, not the system root.
- Keep the artifact root outside the source repository.

Bind `KAG_ARTIFACT_ROOT` to the owner-approved
`/srv/abyss-machine/storage/artifacts/kag/OWNER` route before invoking any
builder. Executable command sequences remain owned by
`config/validation_lanes.json` and
`docs/validation/COMMAND_AUTHORITY.md`; this runbook describes their required
arguments and effects without creating a second command authority.

## Build A Shadow Release

Use the authoritative `scripts/generate_repo_local_kag_index.py` route in
tiered write mode. Supply the repository root, artifact root, and the same
explicit durable `BASE` for source history, event history, and budget
comparison.

Shadow mode keeps cold Git copies while publishing their immutable CAS
objects. A repeated build of the same source snapshot must preserve corpus and
distribution digests and report object reuse rather than new objects.

For the OS-wide proof, invoke
`scripts/run_repo_local_kag_rollout.py --phase shadow` with explicit output,
CAS, and `abyss-machine` roots plus an `OWNER=PATH` artifact binding for every
already-v4 provider. The command requires 24 clean exact commits, signs each
inner family identity, admits each outer bundle through the host-managed trust
plane, proves offline and failure scenarios, signs the 24-owner composition,
and writes one schema-checked evidence packet outside Git.

## Prepare Externalization

Use `scripts/prepare_repo_local_kag_externalization.py` only against explicit
isolated owner worktrees. The five-owner canary invocation uses
`--canary-only` and binds owners in the normative order. The command writes the
externalized v4 control surface and CAS objects, verifies that cold current-tree
shards are absent, and emits a preparation receipt whose head remains
`pending-owner-commit`.

Commit and validate each owner after preparation. Only then run the OS-wide
publication route again so signed releases bind the exact commit that contains
the new surface. A preparation receipt is not a release or a consumer
admission.

## Owner Fast Check

Run the same authoritative route twice in check mode: once as a full owner
build and once with incremental mode enabled. Both checks use the identical
repository, artifact, history, event-history, and budget-base coordinates.

An intentional generated-delta exceedance needs one exact receipt:

For an intentional exceedance, invoke the tiered write route with the
write-receipt option and a non-empty owner reason while retaining the exact
budget base.

The receipt is bound to exact base, head family digest, bytes, and files. It is
not reusable and cannot raise a standing budget.

## Full Audit Snapshot Packet

The generated/full-audit lane creates one run-scoped verified coverage packet
outside the repository. Its cache key binds every owner to the exact Git index
tree plus the coverage builder digest, schema epoch, canonicalization epoch,
and distribution epoch. The first coverage rebuild reads all pinned owners and
writes the packet; later generators and validators in the same lane reuse it.
Compatibility canary runs use the same packet scope. A full committed-state
validation happens before regeneration; exact builder checks and the final
drift snapshot close the lane without a second traversal of immutable owners.

If an owner snapshot, builder, or epoch changes while the lane is running, the
packet is rejected and the audit must restart. The packet is deleted when the
lane exits and is never a committed readmodel or a substitute for owner truth.

## Validate Without Shadow Git

Run the authoritative release validator, family validator, and query reader
against the same repository and artifact root. Disable shadow Git for the
family validation and query; select the required bounded query mode and query
text explicitly.

The query result must report `complete`, the corpus and distribution digests,
and a route count that shows cold objects came from `local_cas` rather than
`shadow_git`.

## Federation And Retrieval From Externalized Owners

Federation and retrieval-plan builders accept repeated
`--owner-artifact-root OWNER=PATH` bindings. Use `--no-shadow-git` in release,
offline, and externalization proof lanes so every selected owner must be
complete through its explicit CAS rather than an obsolete cold Git copy.

The resulting canonical input records carry corpus and distribution identities
separately. Distribution coordinates participate in the delivery/bundle
identity, but are excluded from the logical retrieval projection digest.
Therefore relocating or repacking an unchanged corpus does not invalidate
exact, vector, or graph content.

## Exact V2 Compatibility

Use `scripts/assemble_repo_local_kag_family.py` with the repository, verified
artifact root, shadow Git disabled, and an explicit empty output directory.

The output contains exactly the seven source, artifact, anchor, entity, event,
assertion, and relation views whose digests are pinned by the corpus manifest.

## Offline Export And Import

Export through `scripts/export_repo_local_kag_bundle.py` into an explicit empty
bundle destination. Import that bundle through
`scripts/import_repo_local_kag_bundle.py` into an explicit local CAS. The
import command uses the `--bundle-root` argument defined by its CLI contract.

For `manually-verified`, `release-ready`, `published`, `superseded`, or
`revoked` exports, pass an exact owner commit through `--source-ref` and the
durable owner-validation coordinate through `--verification-receipt`. The
export normalizes the commit to `commit:<hex>`, binds it into the immutable
release identity, and preserves the corpus and distribution digests. The
committed Git manifest deliberately retains the non-recursive
`git-index-source-tree` snapshot marker; embedding the commit that contains
that manifest would make the generated surface immediately self-stale.

Import validates the bundle identity, all linked manifests, the lifecycle
release identity, every CAS object, every pack digest, and every declared pack
range before writing to the target CAS.

After disconnecting remote artifact access, validate and query against
`IMPORTED_CAS` with `--no-shadow-git`. The imported family must be byte-exact
and complete. A clone without the bundle follows the builder route pinned by
the source snapshot and must deterministically reproduce the same corpus.

## Outage And Corruption

- Missing cold objects produce `artifact_required` or
  `artifact_unavailable`, never `complete`.
- A digest mismatch rejects the object and reports `digest_mismatch`.
- A revoked release is not admitted even if every object is present.
- A denied trust domain reports `access_denied`.
- Large hydration is performed by the observable materializer route, never
  hidden inside one MCP request.

## Rollback

1. Stop promotion of the failing distribution locator.
2. Select the last-good owner release or OS composition by digest.
3. Re-admit its signature, owner, source ref, schema/ABI, revocation, and
   access state.
4. Rebuild only affected runtime projections.
5. Verify a CAS-only query and the five MCP operations.
6. Preserve the failed candidate and receipts for diagnosis.

The corpus identity need not change when only a bad locator or pack is rolled
back. During migration an owner may temporarily return to verified Git-full
mode. Git history is never rewritten.

## Retention And GC

Only unreachable objects may be collected. Published, pinned, current, and
last-good manifests are roots. Every deletion produces a receipt, and at least
one independent copy of each published family remains available for rollback.
