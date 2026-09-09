# Prompt-Light Agent Routes And On-Demand Validation

## Index Metadata

- Decision ID: AOA-KAG-D-0049
- Original date: 2026-08-31
- Surface classes: agent lane, docs route, validation guard, public contract
- KAG surfaces: root route, local agent mesh, validation authority, source return
- Source lanes: aoa-kag, source-owner repositories
- Guard families: command authority, source-owned authority, generated-output parity, prompt visibility
- Posture: accepted prompt-light route law; no KAG source, runtime, proof, or release admission change

## Context

`AOA-KAG-D-0005` established `config/validation_lanes.json` as canonical
command storage and said route cards should name lane entrypoints instead of
duplicating command sequences. The current agent mesh does not fully realize
that choice. Of 58 tracked `AGENTS.md` cards, 56 contain fenced blocks. The root
card also carries the complete branch, pull-request, CI, merge, and post-merge
workflow, while 35 cards impose README-bearing reading inventories before the
touched claim is known.

This is especially costly in `aoa-kag`: source return, provenance, derived
authority, generated parity, and stronger-owner stop-lines must be inherited,
but a command catalog or human package overview is useful only after the
specific KAG surface is selected. Repetition makes prompt-visible guidance
larger without making the manifest, source record, builder, or validator more
authoritative.

The durable question is how to reduce inherited context without weakening
source-first KAG law or erasing the human routes that explain it.

## Decision

Keep root and nested `AGENTS.md` as prompt-light inherited semantic deltas. A
card may own its applicable scope, local role, conditional source and owner
routes, source-versus-derived and generated-versus-authored boundaries,
provenance and runtime claim limits, refusal and approval stop-lines, a
validation lane or on-demand validation link, and closeout expectations. It
must not duplicate runnable command sequences, a complete GitHub landing
procedure, a general package overview, or an unconditional README inventory.

Keep `config/validation_lanes.json` as machine command authority under
`AOA-KAG-D-0005`. Root `VALIDATION.md` becomes the on-demand human map for lane
entrypoints and focused checks. A local `VALIDATION.md` may own exact
surface-specific procedure only when no stronger manifest lane or named owner
procedure already owns it. Validators, tests, builders, and inventory surfaces
continue to prove their existing contracts; moving procedure does not weaken or
remove a blocking check.

Treat `README.md` as an on-demand human or public surface. It may explain
purpose, use, package topology, examples, provenance, compatibility, and source
return. It does not become inherited agent context or KAG source authority by
filename. An `AGENTS.md` may link a README when the current task needs that
human contract, but entering a subtree does not require the local README merely
because both files exist.

Keep the repository root README by default as the public entrypoint. This
decision does not authorize blanket deletion, rename, or consolidation of
nested README or AGENTS files. Each disposition requires owner-aware review of
unique human function, incoming links, source and generator relationships,
fixtures, compatibility callers, prompt cost, and validation.

Move the ordinary branch, PR, required-check, merge-method, and post-landing
sync procedure to `docs/RELEASING.md`. Root `AGENTS.md` keeps only the route,
the required evidence boundary, and the stop-line when GitHub status or merge
authority cannot be observed.

This decision supersedes only the placement in `AOA-KAG-D-0005` and current
agent-surface design that treats root or local `AGENTS.md` as executable command
homes. It preserves the validation-lane manifest, lane semantics, inventories,
runner entrypoints, source-owned authority, generated fixed-point gates, impact
routing, release checks, and every provenance, provider, proof, runtime, and
owner-return boundary.

## Options Considered

- Keep commands in the nearest `AGENTS.md` and use only a byte budget.
- Move commands and package explanation into README files.
- Keep inherited cards semantic, make exact procedure on-demand, preserve the
  manifest as machine authority, and retain README files according to their
  human or public function.
- Replace authored routes with generated KAG indexes alone.

## Rationale

The constraints that must arrive before action are source authority,
provenance, generated boundaries, local risk, stop-lines, and the route to
proof. Exact procedure becomes relevant only after those constraints select a
surface. Separating them makes prompt cost proportional to the touched lane
without changing the command source or validation verdict.

Putting commands in README would damage the public and human route. Relying on
generated indexes alone would make a derived KAG surface appear stronger than
authored owner guidance. The chosen split keeps the roles explicit: AGENTS
routes, README explains, owner source defines, VALIDATION exposes procedure,
the manifest executes lanes, and generated KAG views remain subordinate
projections.

## Consequences

- Inherited agent context becomes smaller while source-return and provenance
  stop-lines remain local and explicit.
- Human entrypoints, usage paths, source-home maps, and compatibility routes
  remain available without becoming mandatory prompt context.
- Existing validators that freeze command prose or README reading order in
  `AGENTS.md` must be corrected source-first and continue to guard the same
  substantive contract through the manifest or `VALIDATION.md`.
- An agent follows one explicit on-demand hop before running a focused check.
- Generated decision, agent-route, provider, and KAG read models change only
  through their source and canonical builders.
- A green source gate proves only its declared source contract. It does not
  prove live graph state, MCP deployment, proof, sibling-owner acceptance,
  artifact admission, external CI, review, or merge.

## Source Surfaces

- `AGENTS.md`
- `DESIGN.AGENTS.md`
- `README.md`
- `VALIDATION.md`
- `config/validation_lanes.json`
- `docs/validation/COMMAND_AUTHORITY.md`
- `docs/RELEASING.md`
- `scripts/validation_lanes.py`
- `scripts/ci_gate.py`
- `scripts/validate_nested_agents.py`

## Follow-up Route

Process every tracked README, AGENTS, and affected validation surface against
this role law. Preserve every unique source-return, provenance, derived/source,
generated/source, provider, runtime, proof, quarantine, and sibling-owner
stop-line. Rebuild derived views through their canonical builders, measure
mandatory-read and inherited-chain pressure, run the owner gates, and keep the
owner branch unmerged until the global AbyssOS corpus barrier permits the final
dependency-ordered merge wave.
