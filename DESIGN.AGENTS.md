# aoa-kag Agent Surface Design

## Role

`DESIGN.AGENTS.md` describes the desired form of agent-facing guidance within
`aoa-kag`.

It is not an `AGENTS.md` card, prompt library, policy bundle, KAG model,
charter, roadmap, schema, validator, generated index, or decision record.

It answers one question:

What shape should agent-facing surfaces take so agents can change the KAG
substrate without losing source ownership, provenance, generated boundaries,
validation, or return routes?

## Design Thesis

`aoa-kag` should not give agents one giant instruction wall.

It should give them a navigable route mesh:

- a root card that names repository identity, owner boundaries, route choice,
  validation posture, and closeout;
- local cards for durable districts such as `docs/`, `docs/decisions/`,
  `kag/`, `mechanics/`, `manifests/`, `generated/`, `schemas/`, `examples/`,
  `scripts/`, `tests/`, `config/`, `evals/`, `.agents/`, `Spark/`, and
  `.github/`;
- source surfaces that keep KAG model, source policy, manifests, schemas,
  builders, and tests stronger than route prose;
- generated cards that protect derived read models from hand edits;
- validation surfaces that make provenance, schema, parity, maturity, and
  overclaim guards checkable;
- closeout contracts that let the next agent resume without archaeology.

Agent guidance is useful when it routes to the nearest owner surface and stops
before stealing authority from that surface.

The root names the KAG road system.
The nearest card narrows the lane.
The manifest or model surface owns the local contract.
The builder carries derived outputs.
The validator tests the claim.
The closeout returns stronger meaning to its owner.

## Design as Appearance

Agent guidance should appear as a readable KAG route network.

A healthy `aoa-kag` agent-facing layer has:

- a clear root `AGENTS.md` that begins with the canonical route-card shape;
- local `AGENTS.md` cards in durable editable districts;
- explicit owner boundaries for docs, decisions, local KAG protocol, manifests,
  generated outputs, mechanics, schemas, examples, scripts, tests, config, eval
  intake, companion lanes, and GitHub surfaces;
- named validation routes near the work;
- negative boundaries that prevent source-authority drift;
- generated companions that help navigation without becoming source truth;
- closeout expectations for changed surfaces, generated refresh, checks,
  skipped checks, remaining risk, and next owner route.

A low-context agent should be able to answer: where am I, what owns this, what
must I read, what must I not claim, how do I verify, and where do I hand off?

## Design as Anatomy

The agent-facing layer has several different surface classes.

### Root card

The root `AGENTS.md` owns repository identity, owner boundaries, reading order,
route modes, broad validation posture, decision review, GitHub landing route,
and closeout expectations.

It should route to local truth. It should not contain every KAG pack, manifest,
schema, script, or generated-surface rule.

### Local cards

Local `AGENTS.md` cards own directory-specific risk, source surfaces, stop
lines, and local validation.

They narrow the root card. They do not overturn it.

### Model and policy surfaces

`DESIGN.md`, `CHARTER.md`, `docs/KAG_MODEL.md`, `docs/BOUNDARIES.md`, and
`docs/SOURCE_POLICY.md` own the KAG layer's system form, authority boundary,
conceptual model, owner boundaries, and source-first posture.

Agent cards should route to those surfaces instead of restating the whole KAG
model.

### Manifest cards

`manifests/AGENTS.md` protects source-authored control surfaces for KAG packs.
It should keep the split between manifest intent, donor source refs, output
refs, generated payloads, and docs visible.

### Mechanic cards

`mechanics/AGENTS.md` and `mechanics/README.md` route repeatable KAG operation
pressure without becoming source truth, generated-output authority, or future
local `/kag` protocol by implication.

Mechanic packages should appear only when repeatable operation pressure has an
owner split, payload class, stop-line, and validation route.

### KAG source-home cards

`kag/AGENTS.md`, `kag/README.md`, and `kag/source_home.manifest.json` route the
local-subtree source-home preflight. They should name active source families,
future record classes, runtime-state exclusions, rollout stop-lines, and sibling
handoff rules without becoming generated payload authority or sibling
repository templates.

### Generated cards

`generated/AGENTS.md` protects derived read models. It should name the builder
or source input before any edit route and must say when a file is not
hand-authored.

### Schema, example, script, and test cards

`schemas/`, `examples/`, `scripts/`, and `tests/` cards protect payload
contracts, public-safe examples, deterministic builders, validators, and
regression checks.

They should name the smallest useful proof for the changed surface.

### Decision and eval-port cards

Decision records preserve why a KAG route moved. The `evals/` port captures
KAG-local proof pressure before central proof adoption.

Neither is a substitute for changing the active source surface when active
meaning has changed.

## Design as Operation

A safe agent move in `aoa-kag` follows this route before content mutation:

1. Read the root card.
2. Read `DESIGN.md` when repository shape, source authority, federation
   posture, or KAG system form changes.
3. Read this file when agent-facing route law, local cards, reading order,
   validation posture, or closeout shape changes.
4. Read the nearest nested `AGENTS.md` for every touched path.
5. Read the source model, manifest, schema, builder, test, decision, generated
   source, or owner surface that owns the claim.
6. Make the smallest change that preserves source ownership and provenance.
7. Regenerate derived outputs from source when a source-backed generated layer
   moved.
8. Run the narrowest relevant validation first, then broader gates when the
   change is root-facing, route-facing, generated, structural, release-facing,
   or cross-owner.
9. Close out with changed surfaces, generated refresh result, checks run,
   checks skipped, remaining risk, decision-review result, and next owner
   route.

Agency becomes stronger when it can stop, explain itself, and hand off cleanly.

## Design as Authority

Agent guidance in `aoa-kag` may:

- route work;
- name local risks;
- name owner surfaces;
- require reading order;
- require validation;
- set closeout shape;
- prevent unsafe source-authority claims.

It must not:

- override source-authored meaning in neighboring repositories or Tree of
  Sophia;
- override KAG model docs, manifests, schemas, builders, validators, tests, or
  decision records;
- treat generated files as authored truth;
- hand-edit generated surfaces as source truth;
- claim proof, memory, routing, role, playbook, skill, technique, stats, or
  runtime authority;
- claim live graph, index, embedding, or retrieval state unless the runtime
  owner proves it;
- convert `kag/` protocol preflight into sibling directory templates before
  schemas, examples, and validation exist;
- hide semantic changes under "docs-only", "metadata-only", or formatting
  language.

The agent layer is route law. It is not the KAG substrate, proof system, memory
layer, routing engine, runtime graph, or framework adapter.

## Operational Map Shape

Prefer route cards that answer:

| Field | Meaning |
| --- | --- |
| role | what this surface does |
| input | what enters here |
| output | what leaves here |
| owner | which surface owns truth |
| next route | where to go next |
| tools | what to run or inspect |
| validation | how to prove the route held |

When a boundary is needed, state the positive route that handles the pressure.

## Canonical Card Shape

Durable `AGENTS.md` cards that adopt the canonical shape should begin from this
form:

```markdown
# AGENTS.md

## Applies to

## Role

## Read before editing

## Boundaries

## Validation

## Closeout
```

`Applies to` names scope.
`Role` names what the lane is for.
`Read before editing` gives the minimum route.
`Boundaries` prevents authority drift.
`Validation` turns action into checkable work.
`Closeout` preserves handoff memory.

Optional sections may be added when they sharpen the route: `Purpose`, `Owner
lane`, `Route modes`, `Source surfaces`, `Generated surfaces`, `Decision
review`, `Post-change route review`, `Historical reference`, or local
equivalents.

Optional sections should sharpen the route. They should not decorate it into
fog.

## Migration Posture

`aoa-kag` already has local `AGENTS.md` cards from earlier packs. Some use the
older `Guidance for ...` shape, while newer ports such as `evals/` already use
the canonical card shape.

Do not rewrite local cards only for symmetry. Move a card toward the canonical
shape when its owner route, validation contract, or local risk actually changes,
and update the validator that protects that route in the same change.

The target steady state is a source-routed mesh, not background churn.

## Validation Direction

Executable commands live in root `AGENTS.md` and nearest local cards. This
design surface names what validation should prove:

- source-owned authority remains visible;
- local cards route to the nearest owner surface;
- generated outputs remain reproducible from manifests, docs, builders, or
  source inputs;
- schema and example contracts stay aligned;
- decision indexes are current when decision metadata moves;
- KAG-local eval intake does not claim central proof verdicts;
- local `/kag` protocol pressure routes through `kag/` and remains behind its
  sibling rollout stop-line until schemas, examples, and validation exist.

## Relationship to Other Surfaces

`README.md` introduces the repository.
`CHARTER.md` names the repository authority boundary.
`DESIGN.md` names the KAG system form.
`AGENTS.md` routes agent work in the repository.
Nested `AGENTS.md` cards narrow local work.
`docs/KAG_MODEL.md`, `docs/BOUNDARIES.md`, and `docs/SOURCE_POLICY.md` own the
model, owner boundaries, and source-first posture.
`docs/decisions/` preserves durable KAG route rationale.
`kag/` holds the local-subtree protocol preflight.
`mechanics/` routes repeatable KAG operation topology.
`manifests/` owns source-authored lift controls.
`generated/` remains derived.
`scripts/` and `tests/` keep builders and guards checkable.

`DESIGN.AGENTS.md` holds the design form of the agent-facing layer.

It tells humans and agents what kind of agent guidance they are preserving
when they add, move, split, validate, generate, or port `AGENTS.md` surfaces.

## Use by Agents

Agents should consult this file when a change alters:

- the shape of any `AGENTS.md` card;
- root-to-local precedence;
- route modes or reading order;
- validation authority;
- generated or exported agent-facing companions;
- closeout requirements;
- local card placement;
- mechanics root or package posture;
- cross-repository owner routing;
- future local `/kag` route posture.

This file does not override local owner truth. It tells agents what kind of
agent-facing form they are preserving.

## Landing Rule

When this design changes, review whether the following surfaces also need to
move:

- root `AGENTS.md`;
- affected nested `AGENTS.md` cards;
- `kag/` protocol cards when local-subtree posture moved;
- `README.md` or docs maps;
- `DESIGN.md`;
- validators for root design, local cards, generated freshness, and release
  checks;
- mechanics root or package validators when operation topology changed;
- generated companions when a source-backed machine capsule changed;
- `CHANGELOG.md` and `docs/decisions/` when root or route-law meaning changed.

Only update a surface when its meaning actually moved. The design is a compass,
not a broom.
