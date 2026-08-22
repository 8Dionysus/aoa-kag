# Script Topology

Scripts in `aoa-kag` provide lane execution, validation, generation, release
checks, and part-local contract tools.

The machine-readable script map is
`docs/validation/script_inventory.json`.

## Inventory Fields

- `path`
- `family`
- `organ_lane`
- `owner_surface`
- `source_truth`
- `reads`
- `writes`
- `side_effects`
- `validation_lane`
- `ci_inclusion`
- `test_target`
- `disposition`

## Families

| Family | Function |
| --- | --- |
| `source_validator` | source, route, decision, mechanics, and source-ref checks |
| `validator_entrypoint` | repo-wide validation CLI |
| `validator_adapter` | validator package import surface |
| `validator_generation_port` | KAG generation constants and payload builders |
| `validator_expected_contracts_facade` | expected contract data import surface |
| `validator_expected_contracts` | expected paths, allowed values, and payload contract data |
| `validator_shared` | shared validator helpers |
| `manifest_validator_facade` | manifest contract import surface |
| `manifest_validator` | manifest source-input and output contract checks |
| `validator_orchestrator_facade` | validate_kag orchestration import surface |
| `validator_orchestration` | validate_kag phase execution |
| `projection_builder` | generated/read-model writers and generation entrypoints |
| `projection_reader` | validated discovery, read, filter, and retrieval entrypoints |
| `projection_validator_facade` | generated/read-model parity import surface |
| `projection_validator` | generated/read-model parity checks |
| `example_validator_facade` | public example validator import surface |
| `example_validator` | public example payload checks |
| `decision_index_builder` | decision lookup index writer |
| `artifact_bundle_validator` | release artifact bundle check |
| `owner_evidence_issuer` | clean committed owner-source identity and bounded private overlay materialization |
| `owner_evidence_reviewer` | private runtime-capture validation and bounded owner-review receipt materialization |
| `owner_evidence_projector` | exact owner-review to runtime-evidence overlay projection without authority promotion |
| `owner_acceptance_issuer` | exact proof-bound owner acceptance receipt and overlay materialization without admission |
| `provider_checkout_tool` | pinned provider checkout materialization |
| `skill_local_contract_tool` | exported skill companion helper |
| `part_local_script_runner` | discovered part-local builder and validator checks |
| `lane_executor`, `lane_loader`, `release_entrypoint`, `test_runner` | lane, exact CI handoff, release, and test execution |
| `impact_router` | fail-closed changed-path routing and required-summary state evaluation |
| `validation_run_artifact` | run-scoped coverage packet, event receipt, and aggregate timing evidence |
| `script_route_card` | local route card |
| `projection_helper` | shared generation package modules and compatibility helpers |

## Function Groups

| Function Group | Families |
| --- | --- |
| command authority / lane runners | `lane_executor`, `lane_loader`, `impact_router`, `release_entrypoint`, `test_runner`, `part_local_script_runner`, `provider_checkout_tool`, `validation_run_artifact` |
| generation and retrieval | `projection_builder`, `projection_helper`, `projection_reader`, `decision_index_builder`, `validator_generation_port` |
| validators and owner evidence | `source_validator`, `validator_entrypoint`, `validator_adapter`, `validator_expected_contracts_facade`, `validator_expected_contracts`, `validator_shared`, `manifest_validator_facade`, `manifest_validator`, `validator_orchestrator_facade`, `validator_orchestration`, `projection_validator_facade`, `projection_validator`, `example_validator_facade`, `example_validator`, `owner_evidence_issuer`, `owner_evidence_reviewer`, `owner_evidence_projector`, `owner_acceptance_issuer` |
| topology and route inventory | `script_route_card` |
| release / artifact tooling | `artifact_bundle_validator` |
| skill companion helpers | `skill_local_contract_tool` |

## Root Scripts

Root `scripts/*.py` own repo-wide builders, validators, lane execution,
release checks, and test discovery.

`scripts/coverage_run.py` creates one temporary packet/receipt scope for a
validation run, shares it with nested lane processes, emits the aggregate
machine-readable timing receipt, appends a bounded copy to the GitHub step
summary when that surface is available, and deletes the temporary scope on
exit. Summary publication is telemetry-only and reports degradation without
changing a validation result.

`scripts/impact_routing.py` classifies a pull-request change set against the
versioned command-authority rules. Full-audit rules override owner-local
allow rules, and unknown or unprovable inputs route to full audit. Its summary
mode verifies the always-required source-fast and owner-family job and records
the OS-wide audit as either `verified` or `correctly-not-required`.

`scripts/source_fast_handoff.py` issues and verifies one strict, ephemeral
same-run receipt that binds the successful source-fast and owner-family job to
exact local, donor, command, builder, family, and GitHub workflow identities.
`scripts/ci_release_check.py` selects the CI-only release continuation only
after complete receipt recomputation; otherwise it executes the original full
release lane through `scripts/release_check.py`.

`scripts/prepare_landing.py` is the explicit pre-push preparation entrypoint.
It copies the caller's final tracked and untracked candidate into a detached
temporary worktree, stages only inside that worktree, and converges the atomic
coverage/generated-root/portable-family SCC through ordered Gauss-Seidel
regeneration. It verifies exact provider pins and final parity, emits a typed
receipt, and applies only the resulting generated patch when explicitly asked.
The apply route then restores the caller's exact Git index inside the already
validated isolated candidate and issues a final content seal only when the
actual caller result matches that proved content across bytes and portable
filesystem identity. Its `--verify-applied-seal` route then accepts the normal
post-apply staging step only when worktree and provider identity remain exact
and the staged tree equals the already proved fixed-point tree. This removes
the immediate duplicate zero-drift sweep in a real repair session without
persisting or reusing an owner-proof verdict.
Its preparation-only coverage step rebuilds self while admitting external rows
from the history seed only under unchanged canonical runtime, exact pins, owner
order, canonical roots, and matching portable-manifest identities. It neither
changes the caller's Git index, reuses an owner-proof verdict, nor grants
validation or landing authority.

`scripts/prepare_owner_landing.py` extends isolated preparation to every
provider repository without treating that repository as the root KAG SCC. It
copies the exact tracked, staged, unstaged, and untracked candidate into a
detached temporary worktree, regenerates only its portable family and optional
typed semantic-evidence budget receipt, then requires the common owner-family gate. Its
`--apply` route changes only allowed KAG worktree outputs and preserves the
caller's Git index.

`scripts/repo_local_kag_gate.py` owns the reusable owner-family component DAG.
Incremental parity is an early drift sentinel; after it passes, full parity,
the family contract, and compatibility assembly run with bounded fan-out. The
default is two workers, one is the sequential rollback, and every canonical
component remains blocking against one stable candidate identity.

`scripts/ci_preflight_dag.py` is a scheduling-only release preflight. It
overlaps the seed-only self-coverage sentinel with the already admitted bounded
provider checkout wave, cancels only the peer processes it launched when one
fails, and performs a generated sentinel after checkout fan-in. The canonical
release continuation remains unchanged and blocking; neither sentinel output
is admitted as owner proof or a landing verdict.
Its `--base-ref` remains the historical proof boundary. An optional
`--coverage-seed-ref` supplies only the exact candidate/default-head seed for
the preparation sentinels; runtime compatibility and ancestry are still
required, and the separate seed cannot alter provider checkout identity or the
downstream release commands. The seed is stored at
`generated/repo_local_kag_preparation_seed.json`; the self sentinel merges only
the rebuilt `aoa-kag` row into the authoritative coverage payload. Complete
external-row parity remains the responsibility of the unchanged OS-wide proof.
Its manual-dispatch `direct-control` route is an exact-head measurement and
rollback surface: it runs the same bounded checkout command without either
sentinel and still fans into the identical canonical release continuation.

`scripts/validate_kag.py` is the entrypoint. It exposes `local`, `os-wide`, and
`full` scopes while preserving `full` as the no-argument compatibility
behavior. The local scope never loads every provider family. The explicit
OS-wide scope validates provider-home completeness and complete coverage, and
coverage consumers reuse the run-scoped packet when a lane supplies one. The
implementation map lives in `docs/validation/validator_inventory.json`.

`scripts/validate_local_stats_port.py` delegates the KAG-local `stats/` port
to the pinned `aoa-stats` contract owner and does not reimplement its grammar.

`scripts/issue_kag_mcp_source_identity.py` binds one clean committed KAG
revision to the canonical source-index identity already owned by the portable
repository family. It writes a private content-addressed source receipt and a
private `abyss-stack` evidence-overlay fragment. It does not call MCP, inspect
runtime state, issue central proof, accept an owner result, admit an organ, or
prove rollback.

`scripts/review_kag_mcp_result.py` reads one private, content-addressed and
Ed25519-attested `abyss-stack` canary receipt and result artifact. It resolves
the one active stack capture signer from the committed
`config/runtime_capture_trust.json` at the exact reviewed source revision,
verifies both attestations, validates the exact `kag_discover` owner payload
against the KAG capability schema, assesses KAG source-index freshness, and
writes one distinct private SDK-shaped owner review. It does not call MCP,
accept the result, issue central proof, overwrite capture evidence, or alter
runtime state.

`scripts/project_kag_mcp_owner_review.py` revalidates one current KAG review
against the exact source-pinned SDK schema and its unchanged content-addressed
stack capture receipt. Only a still-live `grounded` plus `exact` review becomes
the stack-attributed endpoint plus KAG-owned grounded-canary and freshness
fields of a private stack overlay.
The projection preserves the stack receipt and KAG review as separate evidence
refs and cannot add central proof, acceptance, admission, or rollback claims.

`scripts/accept_kag_mcp_owner_contour.py` revalidates one private stack
observation against the current KAG source receipt, pinned owner review, exact
consumer-bound proof packet, and content-addressed `aoa-evals` proof record.
It accepts only the exact proved read contour and emits a short-lived private
owner receipt plus acceptance overlay. It cannot authorize registry admission,
change runtime state, grant higher effects, or claim rollback or cross-organ
benefit.

`scripts/validators/local_kag_subtree.py` separates the repo-local KAG subtree,
example, and readiness contract from the OS-wide provider-home family
completeness check while retaining a full compatibility composition.

`scripts/generate_kag.py` is the KAG generated-output entrypoint; its
`--check` mode compares generated/read-model parity without writing files.
`scripts/kag_generation.py` is the compatibility facade for existing imports.
The implementation modules live in `scripts/generation/`.

`scripts/generate_repo_local_kag_index.py` builds either the v3 portable family
or the v4 separated corpus/distribution family. The v4 route selects a
deterministic Git-hot bootstrap set, publishes complete cold shards and bounded
packs to a content-addressed artifact root, emits locators and release
contracts, and preserves the deterministic
source/artifact/anchor/entity/event/assertion/relation compatibility family
from the current repository's source, document, mechanics, command, schema,
generated, and receipt surfaces. It also enforces shard, tracked-byte, and
generated-delta budgets. When an owner publishes the common skill-home manifest, the
builder also preserves canonical skill source versus generated host projection
provenance instead of inferring authority from `.agents/skills/` placement, and
rebuilds declared projections during incremental migration so old authority
claims cannot survive an unchanged copied blob.
When an owner publishes the common capability-home manifest, the builder gives
all declared capability read models the same source-first treatment: generated
classification, exact builder and validator provenance, authored family
returns, and deterministic `derives_from` relations regardless of directory
placement.
The builder's owner-source reader captures one strict staged Git-index epoch,
batch-loads unique blobs, and shares immutable path/mode/object/byte maps across
source and structural builders. Missing or malformed Git state fails closed;
the filesystem fallback is only for a non-Git source root.

`scripts/validate_repo_local_kag_family.py` validates any owner repository's
portable or legacy family against the common schemas, identities, anchors,
evidence, budgets, compatibility digests, and relation integrity contract.

`scripts/assemble_repo_local_kag_family.py` reconstructs the exact seven-file
v2 compatibility view in a caller-selected directory from Git-hot shards and,
when required, a verified CAS without reading migration shadow copies.

`scripts/build_repo_local_kag_release.py` and
`scripts/validate_repo_local_kag_release.py` build/check the immutable complete
owner-family artifact release. The generated/release lanes omit a persistent
artifact root and therefore use one bounded transient root, preferring the
caller-provided validation parent, GitHub runner temp, or `TMPDIR` in that
order. The release builder resolves and forwards the same stable merge-base or
default-branch first-parent history boundary as the owner action before calling
the shared generator. It preserves an existing externalized placement unless
the operator explicitly selects `--retain-cold-in-git`, so generated lanes do
not repopulate cold shards accidentally.
`scripts/export_repo_local_kag_bundle.py` and
`scripts/import_repo_local_kag_bundle.py` provide byte-exact offline transfer.

`scripts/prepare_repo_local_kag_externalization.py` is the only central
operator route that may rewrite explicitly bound owner worktrees into the v4
externalized current-tree shape. It requires clean isolated worktrees, removes
only cold shard copies, publishes their objects to an explicit CAS, emits a
preparation receipt, and stops before commit-bound signing.

`scripts/run_repo_local_kag_rollout.py` is the non-mutating OS-wide publication
and evidence route. It binds all 24 clean owner commits, proves repeat
publication reuse, locator/pack independence, CAS-only dual-reader and v2
parity, offline export/import, outage honesty, corruption rejection, inner and
outer signatures, trust admission, and a signed OS composition. Its bounded
runtime packet validates against
`schemas/kag-tiered-rollout-evidence.schema.json`; neither packets nor host
trust state are committed.

`scripts/classify_repo_local_kag_impact.py` chooses owner-fast,
distribution-fast, incremental-federation, or full-24-owner validation from
changed paths. Its cache identity is owner, source snapshot, builder digest,
schema epoch, and canonicalization epoch. The incremental federation lane
executes release/distribution-manifest-only composition replacement and
affected relation, projection, and tiered-delivery tests without checking out
24 owner trees.

`scripts/query_repo_local_kag.py` validates that family and exposes exact,
BM25, graph, and hybrid retrieval. A v4 result also exposes corpus and
distribution identity, selected delivery routes, completeness, and explicit
degradation. `scripts/repo_local/query.py` also provides
addressed read, profile-aware filtering, and owner discovery for programmatic
consumers.

`scripts/build_repo_local_kag_federation.py` validates configured owner
families and emits an owner-qualified runtime graph projection. The federation
kernel resolves evidence-backed cross-repo references and supports multi-owner
exact, lexical, graph, and hybrid retrieval with access isolation.

`scripts/build_repo_local_kag_retrieval_plan.py` derives source-verified
retrieval documents and emits either a complete plan or a manifest-bound JSONL
bundle for streaming runtime materializers.

`scripts/generate_repo_local_kag_coverage.py` builds
`generated/repo_local_kag_coverage.json` and the minified companion from live
OS Abyss provider roots materialized from the pinned provider registry.
Within each owner scan it reuses the same captured source epoch for source-index
parity, logical-family reconstruction, counts, and profile derivation. Its
run-scoped receipt includes owner wall/CPU/RSS and source-reader process, file,
object, byte, and cache telemetry.
`scripts/coverage_run.py` also accepts additive typed timings from canonical
commands, provider-home proofs, and root repo-local index phases. These records
are observability only: publication degradation is visible but cannot alter the
blocking proof verdict. `docs/validation/CI_EVIDENCE_DAG.md` owns their
dependency-graph and comparison interpretation.

`scripts/validators/repo_local_kag_index.py` compiles a repository-family JSON
Schema once per byte-identical schema input inside a process. This reuses schema
parse/meta-validation only; payload validation and semantic relations remain
per-owner blocking work.
The validator and coverage builder may share only the current process-local,
run-scoped decoded portable family, bound to the resolved owner root and exact
family digest. Immediately after provider-home success, coverage builds one
canonical owner row, retains only that compact row and its timing, and releases
the decoded family before advancing. Shard digest checks, rebuilt-family
equality, exact complete owner ordering, schema validation, and the final
input-identity recheck remain blocking. Standalone coverage remains cold.

The repo-local builders support `--check` for parity without writing files.

`scripts/run_part_local_checks.py` discovers active
`mechanics/<package>/parts/<part>/scripts/build_*.py` and `validate_*.py`
surfaces, runs builders with `--check`, and runs validators directly from the
`source-fast` lane.

`scripts/sync_provider_checkouts.py` materializes exact, complete-history
provider roots from `manifests/provider_registry.json` under `.deps/`, supports
a bounded worker count, can leave secret-owned checkouts to their explicit
credential route, and can run a command with the same provider-root environment
used by repository validation. One worker is the sequential rollback posture.

## Generation Package

Generation implementation lives under:

```text
scripts/generation/
```

`scripts/generation/AGENTS.md` is the local route card. The package keeps
context, shared helpers, source-reference loading, domain builders, and output
writing separated while preserving the public compatibility surface exported by
`scripts/kag_generation.py`.

## Part-Local Scripts

Mechanic-owned scripts live under:

```text
mechanics/<package>/parts/<part>/scripts/
```

Part-local tests and `scripts/run_tests.py` cover active part scripts.

## Validation

Use `docs/validation/COMMAND_AUTHORITY.md` and the nearest `AGENTS.md` for executable validation commands.
