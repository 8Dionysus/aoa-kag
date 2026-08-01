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
| `lane_executor`, `lane_loader`, `release_entrypoint`, `test_runner` | lane, release, and test execution |
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

`scripts/generate_repo_local_kag_index.py` builds the content-addressed
source/structure/history corpus and deterministic
source/artifact/anchor/entity/event/assertion/relation compatibility family
from the current repository's source, document, mechanics, command, schema,
generated, and receipt surfaces. It also enforces shard, tracked-byte, and
generated-delta budgets. When an owner publishes the common skill-home manifest, the
builder also preserves canonical skill source versus generated host projection
provenance instead of inferring authority from `.agents/skills/` placement, and
rebuilds declared projections during incremental migration so old authority
claims cannot survive an unchanged copied blob.
The builder's owner-source reader captures one strict staged Git-index epoch,
batch-loads unique blobs, and shares immutable path/mode/object/byte maps across
source and structural builders. Missing or malformed Git state fails closed;
the filesystem fallback is only for a non-Git source root.

`scripts/validate_repo_local_kag_family.py` validates any owner repository's
portable or legacy family against the common schemas, identities, anchors,
evidence, budgets, compatibility digests, and relation integrity contract.

`scripts/assemble_repo_local_kag_family.py` reconstructs the exact seven-file
v2 compatibility view in a caller-selected artifact directory.

`scripts/query_repo_local_kag.py` validates that family and exposes exact,
BM25, graph, and hybrid retrieval. `scripts/repo_local/query.py` also provides
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
The validator and coverage builder may share only a process-local, run-scoped
portable-family validation token bound to the resolved owner root and exact
family digest. It suppresses one duplicate schema traversal after provider-home
success; shard digest checks, rebuilt-family equality, owner ordering, and the
final input-identity recheck remain blocking. Decoded portable-family caching
is bounded to one sequential owner.

The repo-local builders support `--check` for parity without writing files.

`scripts/run_part_local_checks.py` discovers active
`mechanics/<package>/parts/<part>/scripts/build_*.py` and `validate_*.py`
surfaces, runs builders with `--check`, and runs validators directly from the
`source-fast` lane.

`scripts/sync_provider_checkouts.py` materializes pinned provider roots from
`manifests/provider_registry.json` under `.deps/` and can run a command with the
same provider-root environment used by repository validation.

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
