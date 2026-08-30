# AOA-KAG-D-0046 Budget Receipt Producer Closure And Source Epoch

## Index Metadata

- Decision ID: AOA-KAG-D-0046
- Original date: 2026-08-24
- Surface classes: schema contract, validation guard, generated budget receipt
- KAG surfaces: repo-local family budget receipt, producer closure, source epoch
- Source lanes: aoa-kag, provider repositories, owner-family validation
- Guard families: content identity, source provenance, path confinement, fail-closed budget admission
- Posture: superseded

`AOA-KAG-D-0047` supersedes the runtime and receipt-I/O portions of this
record. The source-epoch and candidate-seal boundaries remain historical
context; current producer admission requires concrete runtime-input binding
and descriptor-pinned receipt publication.

## Context

The first identity-bound v2 receipt closed the obvious candidate replay gap but
its producer identity was a seven-file allowlist. The generator and validator
actually imported more local helpers, schema surfaces, action environment, and
dependency contracts. The receipt builder also combined a Git-index source
snapshot with a worktree candidate seal, and its receipt-prefix exclusion was
checked before `lstat`, allowing a symlink or parent substitution at the exact
receipt path.

## Decision

Keep the top-level `aoa-repo-local-kag-budget-receipt-v2` contract and advance
its nested candidate and producer identities to v2. The producer identity is
the content-addressed closure described by the reviewed
`config/repo-local-kag-budget-producer.json`: AST-replayed local Python import
closure, admitted schema inputs, composite action, action inputs, environment
contract, and exact dependency versions. A newly imported local helper that is
not in the reviewed closure fails closed rather than being silently omitted.

Generation captures one clean source epoch before the immutable owner snapshot;
receipt construction and validation recompute that same epoch. Staged,
unstaged, or non-ignored untracked source drift is rejected. Generated family
and receipt controls remain outside the source epoch, while the candidate seal
excludes only the exact digest-named receipt object.

The exact receipt object and every parent component are checked with `lstat` as
in-root regular filesystem objects. Reads reject symlinks, writes create only
regular directories and use `O_NOFOLLOW`, and a receipt path must equal the
candidate identity's exact excluded object.

## Options Considered

- Extend the seven-file producer allowlist: rejected because it leaves future
  local imports, validator modules, schemas, and environment contracts outside
  the admitted closure.
- Bind the producer commit or candidate tree: rejected because the self-owner
  receipt would reintroduce a publication fixed point.
- Accept the Git index and worktree as separate epochs: rejected because a
  partially staged source candidate can be measured and sealed from different
  bytes.
- Exclude the whole receipt directory: rejected because it hides non-target
  receipt objects and bypasses exact path confinement.
- Use the reviewed manifest, one clean source epoch, and exact `lstat` receipt
  confinement: chosen because each boundary is deterministic, replayable, and
  preserves the self-owner fixed-point escape.

## Consequences

- Old nested-identity receipts fail closed and must be regenerated.
- Changing an imported helper, admitted schema, action input, environment
  contract, dependency declaration, source epoch, or receipt path rejects the
  receipt.
- Receipt publication changes neither the source epoch nor the candidate seal.
- Focused replay, dirty/staged epoch, symlink confinement, source-fast,
  owner-family, generated, and release checks remain separate evidence claims;
  hosted audit, merge, deployment, runtime, and human acceptance remain open
  until their own owners provide evidence.

## Source Surfaces

- `config/repo-local-kag-budget-producer.json`
- `schemas/repo-local-kag-budget-producer-manifest.schema.json`
- `schemas/repo-local-kag-budget-receipt.schema.json`
- `scripts/repo_local/portable_family.py`
- `scripts/generate_repo_local_kag_index.py`
- `.github/actions/repo-local-kag-index/action.yml`
- `tests/test_repo_local_kag_repository_indexes.py`

## Validation

Validate the manifest and receipt schemas, run the focused identity/epoch/path
replay tests, then run source-fast, the owner-family DAG, generated checks, and
the proportionate release checks. Record hosted PR checks independently; local
proof does not establish merge, downstream regeneration, admission, or runtime
acceptance.
