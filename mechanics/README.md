# KAG Mechanics

`mechanics/` is the dispatcher for repeatable KAG operation pressure.

Use this atlas when the work is about an operation around the derived
substrate: source lift, manifest-to-generated parity, federation readiness,
local `/kag` source-home and protocol pressure, retrieval return, graph projection,
quarantine, regrounding, or proof handoff.

Use `docs/` for KAG model and boundary explanation, `manifests/` for
source-authored lift controls, `generated/` for derived outputs, `schemas/` for
payload contracts, `scripts/` for repo-wide builders and validators, and
`evals/` for KAG-local proof pressure before `aoa-evals` accepts it.

## Route

1. Choose the current owner surface before choosing a mechanic.
2. Read [mechanics AGENTS](AGENTS.md) and [mechanics topology](topology.json).
3. If an active package exists, read its `AGENTS.md`, `README.md`, `PARTS.md`,
   `PROVENANCE.md`, and nearest part route.
4. Follow the stronger source surface named by the route.
5. Run the focused mechanics skeleton validator for root changes and the
   package validator when package payload exists.

## Root Contract

Root `mechanics/` owns only:

- `README.md` for human route selection;
- `AGENTS.md` for mechanics-tree edit law;
- `topology.json` for the active package map and root-file contract.

Do not add root rosters, prep reports, migration ledgers, backlogs, templates,
notes, `_meta/`, scratch, or root `legacy/` holding areas. Active operation
detail belongs in the owning package or part. Durable rationale belongs in
`docs/decisions/`. Former-path accounting belongs in package `PROVENANCE.md`
and package-local `legacy/` only after an active route exists.

## Current Contour

`aoa-kag` now carries KAG-local homes for the common center mechanics from
`Agents-of-Abyss`. These packages are route homes, not imported center
doctrine. They name how KAG participates in each mechanic while keeping source,
proof, memory, routing, runtime, playbook, skill, technique, and ToS authority
with stronger owners.

The current repository still has stronger active artifact homes:

| Pressure | Current owner route |
| --- | --- |
| KAG model, source policy, and boundary posture | `DESIGN.md`, `docs/KAG_MODEL.md`, `docs/BOUNDARIES.md`, `docs/SOURCE_POLICY.md` |
| source-authored lift controls | `manifests/` |
| generated KAG outputs and compact read models | `generated/` |
| schema and example contracts | `schemas/` and `examples/` |
| builders, validators, and decision-index helpers | `scripts/` |
| KAG-local proof intake before central adoption | `evals/` |
| local `/kag` subtree source-home preflight | `kag/README.md`, `kag/source_home.manifest.json`, `kag/LOCAL_SUBTREE_PROTOCOL.md`, `docs/decisions/AOA-KAG-D-0004-federated-local-kag-preflight.md` |

## Common Mechanics Map

These package homes mirror the common center mechanics as KAG-local route
cards:

| Package | KAG-local route |
| --- | --- |
| `agon` | candidate-only Agon KAG promotion and Sophian threshold packet routes |
| `antifragility` | projection health, quarantine, and source-first recovery under stress |
| `audit` | proof expectation refs, evidence visibility, and exposure review routing |
| `boundary-bridge` | source-owned export, ToS, memo, counterpart, federation, and cross-source projection bridges |
| `checkpoint` | reasoning handoff and owner-return packet posture |
| `distillation` | source lifts, ToS chunk maps, and route pack formation |
| `experience` | adoption, governance, service, office, and release pattern contracts |
| `growth-cycle` | owner wait states, maturity gates, and surface-growth stop-rules |
| `method-growth` | pattern candidate lineage, promotion dossiers, owner downlinks, and retirement routes |
| `questbook` | KAG-local durable obligations, quest source posture, and dispatch/catalog projections |
| `recurrence` | return regrounding and recurrence projection back to stronger refs |
| `release-support` | release contour, artifact identity, and generated parity support |
| `rpg` | adjunct readable progression vocabulary without hidden ontology |

`titan` is intentionally not a KAG-local package in this pass. It is present in
some sibling mechanics, but KAG currently routes Titan pressure to stronger
role, runtime, memory, proof, and routing owners.

## KAG-Only Pressure

No KAG-only mechanic package is active yet.

The real KAG-only pressure is the future local `/kag` subtree source-home and protocol:
repo-local indexes, graph nodes, graph edges, projections, freshness, and
composition rules. The source-home preflight now lives in `kag/`, but mechanics
still does not own a KAG-only package or part until the protocol has schemas,
examples, payload classes, stop-lines, and validation routes.

## Package Growth Rule

A new non-center `mechanics/<slug>/` package should appear only when it has:

- repeatable KAG operation pressure;
- source surfaces and payload classes;
- owner split and stop-lines;
- local validation;
- a reason it cannot remain in `docs/`, `manifests/`, `generated/`, `schemas/`,
  `scripts/`, `tests/`, or `evals/`;
- package route surfaces in `AGENTS.md`, `README.md`, `PARTS.md`, and
  `PROVENANCE.md`.

Use package `ROADMAP.md` only when package-local future pressure exists. Do not
create package roadmaps, legacy folders, or part directories for symmetry.

Common-center packages may exist as route homes before part-local artifacts
move. Their `PARTS.md` files own candidate part pressure and must either keep
the no-active-parts stop-line or name the active part routes already listed in
`mechanics/topology.json`.

## Package Card Standard

Each future package `README.md` should be an agent-operable local card. It
should let a reader answer when to use the mechanic, what `aoa-kag` owns, which
stronger owners keep final truth, what may enter, what may leave, what must not
be claimed, and where to go next.

Use these headings in package READMEs:

| Heading | Purpose |
| --- | --- |
| `## Mechanic card` | compact package status and entry posture |
| `### Trigger` | when the local mechanic applies |
| `### Local owns` | what `aoa-kag` may author here |
| `### Stronger owner split` | sibling owners that keep stronger truth |
| `### Inputs` | material that may enter this mechanic |
| `### Outputs` | material that may leave without becoming source truth |
| `### Must not claim` | stop-lines that keep the package below stronger owners |
| `### Next route` | the next active surface, provenance bridge, or owner route |

Validation commands belong in the nearest `AGENTS.md`, not in the package
card.

## Placement

- Source-owned meaning stays in the source repository.
- KAG model and boundary explanation stay under `docs/`.
- Manifest-driven source controls stay under `manifests/`.
- Root generated read models stay under `generated/`.
- Root schemas and examples stay in `schemas/` and `examples/` while they are
  repo-wide contracts.
- Root scripts stay in `scripts/` when they are repo-wide validators, builders,
  release gates, or public compatibility entrypoints.
- Mechanic-owned docs, schemas, examples, config, manifests, generated
  companions, scripts, and focused tests may move under
  `mechanics/<package>/parts/<part>/` only after the package has a local
  contract and validation route.

## Parts Rule

`parts` are functioning sub-mechanics. They are the nearest owner for a real
slice of operation when that slice has:

- a stable purpose and payload class;
- a local owner split and stop-lines;
- `README.md`, `CONTRACT.md`, and `VALIDATION.md` or an equivalent nearest
  route card;
- focused validation;
- artifacts that are clearer inside the part than in root KAG districts.

Do not create `parts/` as a parking lot for future work. A package may list
candidate part pressure in `PARTS.md` without creating directories.

## Validation

For mechanics root changes, run:

```bash
python scripts/validate_mechanics_skeleton.py
python scripts/validate_nested_agents.py
```

For release-facing changes, also run:

```bash
python scripts/release_check.py
```
