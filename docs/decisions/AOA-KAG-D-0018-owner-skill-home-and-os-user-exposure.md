# Owner Skill Home And OS User Exposure

## Index Metadata

- Decision ID: AOA-KAG-D-0018
- Original date: 2026-07-18
- Surface classes: owner skill, agent companion, schema contract, validation guard, OS user exposure
- KAG surfaces: callable KAG procedure, source return, capability retrieval, user-profile exposure
- Source lanes: aoa-kag, aoa-skills home-port contract, abyss-stack MCP access plane, OS user profile
- Guard families: source-owned authority, no duplicate projection, full-contract executability, degraded route, manual behavior
- Posture: accepted

## Context

The repository carried 25 broad skill packages under `.agents/skills/`.
Those packages were exported generic procedures rather than an
`aoa-kag`-owned capability and competed with the global skill catalog without
teaching the live five-operation KAG access plane. They also made repository
placement look like skill ownership.

Manual use of the live MCP established a different owner need: one short
front door must route retrieval, relation, and bounded research; preserve
owner source return and cumulative degradation; respect live tool bounds;
follow supersession; reject raw-session questions; and refuse to advertise an
incomplete or unavailable capability as executable.

## Decision

`skills/aoa-kag/` is the canonical home for one admitted `aoa-kag` bundle.
Retrieve, relate, and research remain internal semantic modes. Discover,
search, read, traverse, and explain remain MCP operations rather than separate
skills. The bundle has no runtime dependency on `aoa-techniques`.

`skills/port.manifest.json` uses home-port v2 to expose the owner bundle
through the OS user `os-user-default` profile. The repository does not keep a
same-name `.agents/skills/aoa-kag` copy. KAG may locate and return the canonical
procedure, but a graph row or partial snapshot never replaces that procedure:
executable posture requires the complete owner contract, selected conditional
procedure, current owner source, and available live binding.

Raw prompts, traces, rubrics, and task-local DAGs remain session evidence.
Only generalized procedure and bounded manual-case labels belong in the owner
bundle.

## Options Considered

- Keep the 25 exported packages in `.agents/skills/`: preserves duplicate
  repository visibility but does not create a KAG-owned capability and
  increases routing interference.
- Add one skill for each MCP operation: mirrors tool names but multiplies
  triggers around one semantic capability and obscures task-level modes.
- Admit one owner bundle with three conditional modes and OS user exposure:
  gives global discoverability, one canonical source, and progressive
  disclosure while keeping tool operations in the MCP layer.

## Rationale

The owner bundle is a procedural capability rather than another document
index. One front door is sufficient to attract the agent to KAG functionality;
conditional mode references carry the full procedure only when selected.
Home-port v2 preserves global discoverability without a competing repo copy.

Full-contract gating prevents the skill graph from manufacturing
executability. Cumulative degradation and owner-return rules preserve the
derived-substrate boundary observed in manual use. Keeping trial artifacts in
the session avoids turning one run into owner truth.

## Consequences

- A new Codex session can discover one globally exposed KAG capability.
- `aoa-kag` has one canonical owner procedure instead of 25 unrelated local
  copies.
- The five MCP tools remain live operations and may evolve without forcing
  five skill identities.
- KAG retrieval can support task-local composition, but the caller must read
  canonical owner procedures and build the actual DAG in the session.
- Manual trials support admission and reveal failure modes; structural checks
  prove packaging and index invariants only, not behavioral superiority.
- Federation and the OS user profile must be refreshed after the owner change
  lands. A stale snapshot or stale installed link is not current owner parity.

## Source Surfaces

- `AGENTS.md`
- `DESIGN.md`
- `DESIGN.AGENTS.md`
- `skills/AGENTS.md`
- `skills/README.md`
- `skills/port.manifest.json`
- `skills/aoa-kag/SKILL.md`
- `skills/aoa-kag/references/contract.yaml`
- `kag/LOCAL_SUBTREE_PROTOCOL.md`
- `schemas/repo-local-kag-index.schema.json`
- `scripts/generate_repo_local_kag_index.py`
- `tests/test_repo_local_kag_index.py`
- `aoa-skills:schemas/skill-home-port.schema.json`
- `abyss-stack:mcp/services/aoa-kag-mcp/`

## Validation

Admission rests first on manual isolated, negative, source-return,
cross-owner, degraded-route, supersession, bounded-refinement, traversal, and
live-bound scenarios against the five-tool MCP.

Structural support is checked separately with `quick_validate.py`, the shared
`aoa-skills` home-port validator, focused existing repo-index tests, semantic
agent-route validation, generated parity, source-fast, and release-facing
lanes. Green structural checks do not prove skill usefulness.
