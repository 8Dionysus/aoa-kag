# Changelog

All notable changes to `aoa-kag` will be documented in this file.

The format is intentionally simple and human-first.
Tracking starts with the community-docs baseline for this repository.

## [Unreleased]

### Summary

- the current post-`v0.4.0` line activates the first repo-local KAG provider
  foundation and keeps the published `v0.4.0` release memory aligned with the
  reconstructed release evidence
- the local `/kag` layer is now a source-home contract surface for portable
  records and MCP-facing access shape, while live graph, vector, embedding,
  index, runtime, and cache state remain outside Git

### Added

- Add the generated repo-local entity, artifact, and event indexes shared by
  every provider, plus the optional owner-domain index catalog contract.
- Activate the first repo-local KAG provider foundation under `kag/`, including
  provider records, readiness indexes, MCP-facing projection shape, validation
  receipts, and the local KAG subtree protocol.
- Add the local KAG subtree schema, example packet, readiness matrix, validator
  coverage, and `AOA-KAG-D-0010` decision record for the provider activation
  line.

### Changed

- Expand the owner-callable repo-local KAG action from source-index parity to
  atomic source/entity/artifact/event index-family parity.
- Align the release workflow dependency pins with the merged
  `Tree-of-Sophia/kag/` and `aoa-techniques/kag/` provider homes so
  `aoa-kag` validates against the current source-owned provider surfaces.
- Reconcile the published `v0.4.0` changelog and GitHub Release notes against
  the actual tag range instead of the older narrow release-prep summary.

### Validation

- the repository release lane in `docs/validation/COMMAND_AUTHORITY.md`
- GitHub `Repo Validation` for the landed local KAG provider and changelog
  closeout PRs

## [0.4.0] - 2026-06-26

### Summary

- `v0.4.0` closes the post-`v0.2.2` release-prep span: 31 first-parent
  commits, 908 changed tracked paths, PRs through `#109`, 13 active mechanics
  packages, 28 functioning parts, 9 decision records, and 57 local
  `AGENTS.md` route cards
- the largest changed surfaces were `mechanics/` (421 paths), `.agents/`
  portable agent and skill exports (238), `scripts/` (110), `docs/` (48),
  `tests/` (22), `generated/` (20), `quests/` (10), and `evals/` (6), matching
  the intended repository-shaping release rather than an unrelated code-only
  bump
- this release hardens `aoa-kag` from a growing derived-substrate pilot into a
  release-ready KAG topology with mechanics, validators, scripts, tests,
  generation, command authority, design routes, local eval pressure, decision
  rationale, and root-doc routes separated by owner function
- the KAG layer remains bounded: generated graph-ready and retrieval-ready
  surfaces are source-linked derived read models, not source truth, proof,
  routing, memory truth, runtime state, or a full graph engine
- release evidence now includes stronger KAG registry artifact identity,
  local-source-home and eval-route preflight, decision-lane modeling, and a
  compact public README front door

### Reconciliation Basis

- This dated release section was reconstructed from
  first-parent commit history, changed-path name-status evidence, merged PR
  metadata, the tagged release commit, decision records, current route cards,
  validation topology, and the published GitHub Release rather than from
  changelog prose alone.
- Future `Unreleased` entries should record stable route, owner, and
  validation changes without live commit totals, changed-path totals, or PR
  ranges; dated release sections own exact reconciliation.
- The release-prep commit itself changed version, changelog, roadmap,
  release-route, and roadmap-parity surfaces only; the release section below
  records the accumulated landed topology it published.

### Final Route Sweep

- Root entry surfaces now route first reading, authority boundary, design,
  agent-surface design, mechanics, local `/kag`, model boundary, decisions,
  manifests, generated surfaces, schemas/examples, validators, agent
  companions, eval pressure, and future direction to their owning local
  surfaces.
- `README.md`, `AGENTS.md`, `CHARTER.md`, `DESIGN.md`,
  `DESIGN.AGENTS.md`, `ROADMAP.md`, `docs/README.md`, `docs/RELEASING.md`,
  and validation docs now stay compact and route-oriented instead of carrying
  detailed package inventories or duplicated command blocks.
- Mechanics now live under `mechanics/` as repeatable KAG operation topology
  with package route cards, parts, provenance, validation, and part-local test
  coverage.
- Generated outputs stay derived companions; manifests, schemas, examples,
  builders, validators, tests, and generated-source owners now name the local
  surface that owns their claim.
- The local eval port under `evals/` captures KAG-local proof pressure while
  verdict, scoring, regression, and proof doctrine remain in `aoa-evals`.

### Derived-Substrate Boundary

- `aoa-kag` owns derived KAG metadata, source-linked projection posture,
  bridge and handoff surfaces, federation and regrounding seams, artifact
  identity checks, and framework-neutral local `/kag` protocol contracts.
- Source repositories still own authored meaning; `aoa-evals` owns proof
  verdicts; `aoa-memo` owns durable memory truth; `aoa-routing` owns routing
  policy; `aoa-agents` owns role meaning; `aoa-playbooks` owns scenario
  composition; `aoa-skills` owns executable skill workflow; `aoa-techniques`
  owns reusable practice; `Tree-of-Sophia` owns authored knowledge architecture.

### Added

- Add repo-local route cards across root districts, including `.agents/`,
  `.github/`, `config/`, `docs/`, `evals/`, `generated/`, `manifests/`,
  `mechanics/`, `quests/`, `schemas/`, `scripts/`, and `tests/`.
- Add `DESIGN.md` and `DESIGN.AGENTS.md` so the public design surface and
  agent-facing design route are explicit.
- Add the portable AoA agent/skill foundation under `.agents/skills/` and the
  `.agents/spark/` route for Codex Spark session surfaces.
- Add a local eval port with `evals/PORT.yaml`, local intake/suite/report
  homes, and source-home eval routes.
- Add the modeled decision lane with canonical `AOA-KAG-D-*` records,
  generated decision indexes, and decision-record validation.
- Add mechanics package homes, `PARTS.md`, `PROVENANCE.md`, part contracts,
  package-local validators, package-local tests, and active legacy accounting
  for the KAG mechanics split.
- Add Questbook source-store topology under `quests/kag/` with captured, done,
  and reanchor lanes.
- Add validation lane manifests, script inventory, validator inventory, test
  inventory, nested/semantic AGENTS validators, mechanics skeleton validation,
  command-authority validation, and repo-validation workflow coverage.
- Add KAG registry artifact bundle verification through
  `scripts/validate_abyss_machine_kag_registry_bundle.py` and artifact-bundle
  docs.

### Changed

- Refactor KAG mechanics topology into package/part homes with part-local
  contracts, validation routes, and script/test coverage.
- Move previously flat root mechanics material into owner-shaped mechanics
  packages while preserving historical accounting in package-local legacy
  surfaces.
- Split repo validators into owner modules for expected contracts, manifests,
  generated projection parity, examples, and orchestration while preserving
  `scripts/validate_kag.py` as the lane entrypoint.
- Harden script and test topology with machine-readable inventories, route
  cards, part-local script discovery, and source-fast coverage for active
  mechanics scripts.
- Refactor KAG generation implementation into `scripts/generation/` domain
  modules while preserving `scripts/kag_generation.py` as the compatibility
  facade and `scripts/generate_kag.py` as the generated-output entrypoint.
- Promote KAG registry artifact trust gates and registry evidence routes so
  generated/read-model payloads keep explicit artifact identity and source
  ownership.
- Add canonical decision-lane modeling and source-home eval routes so decision,
  eval, and KAG-home surfaces are checked by local topology tests.
- Update optional `aoa-memo` source-owned export readiness so the memo KAG donor
  bridge is expected from the reviewed corpus bundle rather than the bridge
  teaching fixture.
- Clarify the memo donor export consumer boundary: `aoa-kag` reads reviewed
  `aoa-memo` object ids, provenance, lifecycle, and generated read models as a
  registry-visible donor route, not graph truth, proof, routing authority, or a
  memory write path.
- Centralize validation command authority so route cards and public docs point
  to lane owners instead of carrying duplicated command blocks.
- Rework the root README as a compact front door that routes detailed
  inventories to `docs/`, `mechanics/`, manifests, generated companions, local
  route cards, and release authority.
- Refresh shared AoA skill links, self-diagnose and memory-route surfaces,
  memo KAG bridge routes, eval catalog path guards, AGENTS topology, roadmap
  parity, and contributor/release docs against the current OS Abyss route law.

### Moved Or Retired

- Move active KAG mechanics material from flat root-adjacent surfaces into
  owner-shaped mechanics packages and functioning parts, with package-local
  `PROVENANCE.md` and `legacy/` bridges preserving historical accounting.
- Move the Codex Spark lane from root `Spark/` posture into `.agents/spark/`
  so agent-session material follows the agent companion lane.
- Retire command duplication from narrative docs; executable validation routes
  now live in `AGENTS.md`, nearest route cards, validation docs, release docs,
  lane manifests, and owning part `VALIDATION.md` surfaces.

### Validation

- the repository release lane in `docs/validation/COMMAND_AUTHORITY.md`
- GitHub `Repo Validation` on release PR `#109`
- Release command authority was checked through
  `docs/validation/COMMAND_AUTHORITY.md`, `config/validation_lanes.json`, and
  the `docs/RELEASING.md` release route

### Notes

- this dated section is the canonical `v0.4.0` release contour; it records the
  accumulated repository-shaping work published by tag `v0.4.0`, not only the
  final release-prep commit
- this release does not widen KAG ownership, activate a full graph engine, or
  turn generated/read-model payloads into source truth
- detailed source movement remains discoverable through mechanics
  `PROVENANCE.md`, package-local `legacy/`, decision records, validation
  inventories, and generated-source owners; this changelog records the release
  contour rather than a full file inventory

## [0.2.2] - 2026-04-23

### Summary

- this patch lands Agon KAG promotion candidates, Sophian packet surfaces,
  KAG-to-ToS threshold boundaries, and KAG-to-owner signals while keeping KAG
  subordinate to source-owned meaning
- recurrence projection input contracts, post-release pattern candidates,
  federation pattern harvest, pattern adoption dossiers, retirement/downlink
  surfaces, and wave3 KAG candidate contracts are added beside wave2/wave3
  hardening
- `aoa-kag` remains the provenance-aware derived substrate layer rather than a
  source-authoritative graph, runtime service, or proof owner

### Added

- Agon KAG promotion candidate registry, Sophian KAG packet registry,
  KAG-to-ToS threshold boundaries, KAG-to-owner signals, and promotion
  evidence bundle surfaces
- recurrence projection input contracts, post-release pattern candidate seam,
  federation pattern harvest, KAG pattern nodes, adoption dossiers, downlinks,
  retirement decisions, and ToS dossier bridge surfaces
- wave3 KAG candidate contract surfaces and generated recurrence manifests

### Changed

- Agon KAG review follow-ups, recurrence projection contracts,
  source/proof boundary wording, and wave2/wave3 KAG contract hardening were
  tightened

### Validation

- Release validation used the release lane in
  `docs/validation/COMMAND_AUTHORITY.md`.

### Notes

- this patch is a bounded derived-substrate release; source repositories still
  own authored meaning and proof repositories still own verdict posture

## [0.2.1] - 2026-04-19

### Summary

- this patch adds chaos-wave regrounding and stronger maturity governance
  across the derived KAG layer
- memo-readiness regrounding, release posture, and roadmap/README boundaries
  are tightened without widening source ownership
- `aoa-kag` remains provenance-aware derived structure rather than a
  source-authoritative repository

### Added

- manifest-backed KAG maturity governance surface covering stability tiers, owner wait states, proof expectations, and the current stop-rule for new `AOA-K-*` growth
- chaos wave 1 regrounding surfaces for current retrieval and return-pressure
  scenarios

### Changed

- tightened README and roadmap posture so the current pause threshold is explicit: maintain and prove the existing surface set while neighboring owner layers mature
- memo-readiness regrounding, release posture, and CI/protection surfaces are
  aligned with the current KAG maintenance line

### Validation

- Release validation used the release lane in
  `docs/validation/COMMAND_AUTHORITY.md`.

### Notes

- this patch makes the current maintenance-and-proof stop rule explicit while
  keeping KAG subordinate to source-owning repositories

## [0.2.0] - 2026-04-10

### Summary

- this release adds federation export owner slices, ToS-adjunct and regrounding surfaces, and a project-foundation/via-negativa refresh for the derived KAG layer
- generation and validation contracts are aligned with the current pinned donor inputs and refreshed technique-lift contour
- `aoa-kag` remains provenance-aware derived structure rather than a source-authoritative repository

### Validation

- Release validation used the release lane in
  `docs/validation/COMMAND_AUTHORITY.md`.

### Notes

- detailed manifest, generated-pack, documentation, and validation-surface coverage for this release remains enumerated below under `Added`, `Changed`, and `Included in this release`

### Added

- federation export registry owner slice and stronger source-owned federation
  spine review surfaces
- bounded ToS adjunct and third-wave stress/regrounding surfaces together with
  refreshed technique-lift coverage
- via negativa KAG checklist and repo-local project-foundation skill install

### Changed

- aligned KAG generation and validation contracts with the current pinned donor
  inputs and public techniques contour
- clarified validation routes and AGENTS guidance around next-wave
  regrounding posture and source-first entry paths

### Included in this release

- KAG pack and doctrine refreshes across `manifests/`, `generated/`, `docs/`,
  `examples/`, and `schemas/`, including ToS adjunct posture, federation
  export owner slices, stress and regrounding surfaces, and refreshed
  technique-lift coverage
- contributor and validation surfaces under `.agents/`, `.github/`, `AGENTS.md`,
  `README.md`, `CONTRIBUTING.md`, `scripts/`, and `tests/`, including
  project-foundation rollout, source-first verify-route clarity, and pinned
  donor alignment

## [0.1.0] - 2026-04-01

First public baseline release of `aoa-kag` as the derived knowledge substrate layer in the AoA public surface.

This changelog entry uses the release-prep merge date.

### Summary

- first public baseline release of `aoa-kag` as the provenance-aware derived substrate layer for AoA
- the public baseline now includes a manifest-driven registry, technique lift pack, ToS-derived chunk and route packs, reasoning-handoff and return-regrounding packs, federation spine surfaces, counterpart review surfaces, and a tiny consumer bundle
- this release keeps source ownership explicit by treating `aoa-kag` as derived structure rather than authored authority

### Added

- community-docs baseline established for this repository
- `CHANGELOG.md`, `CODE_OF_CONDUCT.md`, and `SECURITY.md`
- manifest-driven KAG generation via `manifests/kag_registry.json`, `manifests/technique_lift_pack.json`, and `scripts/generate_kag.py`
- first generated technique lift pack for `AOA-K-0001` through `AOA-K-0004`
- validation coverage for generated outputs and technique lift pack drift
- federation KAG readiness doctrine and `federation-kag-export` schema/example
- experimental `federation_spine` manifest, generated outputs, and validator coverage for `AOA-K-0009`
- source-owned export dependency contract via `mechanics/boundary-bridge/parts/source-owned-export/manifests/source_owned_export_dependencies.json`
- `docs/CONSUMER_GUIDE.md` and `scripts/release_check.py`
- stdlib `unittest` coverage for helper functions, builder parity, dependency failures, and projection pairing failures
- `mechanics/boundary-bridge/parts/counterpart-edge/docs/counterpart-consumer-contract.md`, `mechanics/boundary-bridge/parts/counterpart-edge/schemas/counterpart-consumer-contract.schema.json`, and `mechanics/boundary-bridge/parts/counterpart-edge/examples/counterpart_consumer_contract.example.json`
- `mechanics/boundary-bridge/parts/tiny-consumer-bundle/manifests/tiny_consumer_bundle.json`, `mechanics/boundary-bridge/parts/tiny-consumer-bundle/generated/tiny_consumer_bundle.json`, and `mechanics/boundary-bridge/parts/tiny-consumer-bundle/generated/tiny_consumer_bundle.min.json`
- `mechanics/audit/parts/exposure-review/docs/counterpart-federation-exposure-review.md`, `mechanics/audit/parts/exposure-review/manifests/counterpart_federation_exposure_review.json`, and generated review outputs

### Changed

- `AOA-K-0009` now covers a two-repo experimental spine pilot for `aoa-techniques` and `Tree-of-Sophia`
- `mechanics/boundary-bridge/parts/federation-spine/generated/federation_spine.json` and `mechanics/boundary-bridge/parts/federation-spine/generated/federation_spine.min.json` now publish the current source-owned ToS tiny-entry seam beside the existing `aoa-techniques` donor surfaces
- federation spine doctrine and public entry docs now describe the two-donor pilot as already consumable downstream while it remains experimental and non-authoritative
- `mechanics/boundary-bridge/parts/cross-source-projection/manifests/cross_source_node_projection.json` now declares explicit `projection_pairings` instead of leaving the current pilot pairing implicit in generator code
- reasoning handoff doctrine, example, and generated pack now name the counterpart consumer contract explicitly instead of leaving the first `counterpart_refs` consumer implicit
- counterpart consumer contract and tiny consumer bundle now carry an explicit federation exposure review ref while `AOA-K-0008` remains planned
- counterpart activation gates now treat federation exposure as review-closed for the planned posture rather than leaving it implicit
- ToS tiny-entry route consumption now accepts `bounded_hop` as the primary hop field and keeps `lineage_or_context_hop` as a compatibility alias during the current transition window

### Included in this release

- manifest-driven KAG registry and pack inputs under `manifests/`
- generated lift, retrieval, reasoning, recurrence, federation, counterpart-review, and consumer outputs under `generated/`
- source-aware validation and generation helpers under `scripts/release_check.py`, `scripts/generate_kag.py`, and `scripts/validate_kag.py`

### Validation

- Release validation used the release lane in
  `docs/validation/COMMAND_AUTHORITY.md`.

### Notes

- this release remains a repository release of derived substrate contracts and generated packs rather than a graph engine, runtime service, or source-authority layer
