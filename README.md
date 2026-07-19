# aoa-kag

`aoa-kag` is the derived knowledge substrate layer of the AoA ecosystem.

It makes graph-ready and retrieval-ready structures explicit without moving
authored meaning out of source repositories. A KAG surface here is a
source-linked lift, projection, manifest, schema, example, or generated read
model. It is not proof, routing, memory truth, runtime state, or a replacement
for authored source.

Use this README as the public front door. When work becomes authoritative,
model-level, generated, mechanic-local, local `/kag` protocol, release-facing,
or agent-facing, follow the linked owner surface instead of expanding this
page.

> Current release: `v0.5.0`. See [CHANGELOG](CHANGELOG.md) for release notes.

## What This Repository Does

| Function | Surface |
| --- | --- |
| Repository authority boundary | [CHARTER](CHARTER.md) |
| KAG-layer system form | [DESIGN](DESIGN.md) |
| Agent-facing route law | [AGENTS](AGENTS.md), then the nearest nested `AGENTS.md` |
| Callable KAG procedure and OS exposure | [skills](skills/README.md), [home-port manifest](skills/port.manifest.json) |
| KAG model, source policy, and owner boundaries | [KAG_MODEL](docs/KAG_MODEL.md), [BOUNDARIES](docs/BOUNDARIES.md), [SOURCE_POLICY](docs/SOURCE_POLICY.md) |
| Local `/kag` source-home preflight | [kag](kag/README.md), [source_home.manifest](kag/source_home.manifest.json), [LOCAL_SUBTREE_PROTOCOL](kag/LOCAL_SUBTREE_PROTOCOL.md) |
| Repo-local knowledge kernel | [kag indexes](kag/README.md), [tiered distribution](docs/KAG_TIERED_DISTRIBUTION.md), [corpus schema](schemas/repo-local-kag-corpus-manifest.schema.json), [distribution schema](schemas/repo-local-kag-distribution-manifest.schema.json), [coverage report](generated/repo_local_kag_coverage.min.json) |
| KAG-owned statistical questions and reference measurements | [stats](stats/README.md) |
| Repeatable KAG operation topology | [mechanics](mechanics/README.md), [mechanics topology](mechanics/topology.json) |
| Current consumer and bridge posture | [CONSUMER_GUIDE](docs/CONSUMER_GUIDE.md), [BRIDGE_CONTRACTS](docs/BRIDGE_CONTRACTS.md), [docs map](docs/README.md) |
| Manifest, generated, schema, and example surfaces | [manifests](manifests/AGENTS.md), [generated](generated/AGENTS.md), [schemas](schemas/AGENTS.md), [examples](examples/AGENTS.md) |
| Durable rationale, direction, and obligations | [decisions](docs/decisions/README.md), [ROADMAP](ROADMAP.md), [QUESTBOOK](QUESTBOOK.md), [quests](quests/README.md) |
| Validation command authority | [COMMAND_AUTHORITY](docs/validation/COMMAND_AUTHORITY.md), plus the nearest `AGENTS.md` |

This repository is strongest when it makes a derived surface easier to inspect,
validate, and return to its source owner. It is weakest when it pretends the
derived substrate is already a source canon, proof system, router, memory
ledger, runtime, or full graph platform.

## Start Here

Read only what matches the job.

| Need | Route |
| --- | --- |
| Shortest honest overview | this README -> [CHARTER](CHARTER.md) -> [DESIGN](DESIGN.md) -> [KAG_MODEL](docs/KAG_MODEL.md) |
| Decide whether a claim belongs here | [CHARTER](CHARTER.md) -> [BOUNDARIES](docs/BOUNDARIES.md) -> [SOURCE_POLICY](docs/SOURCE_POLICY.md) |
| Understand KAG surface classes | [KAG_MODEL](docs/KAG_MODEL.md) |
| Work on local `/kag` protocol posture | [kag](kag/README.md), then [kag/AGENTS](kag/AGENTS.md) |
| Work on repeatable KAG operations | [mechanics](mechanics/README.md), then [mechanics/AGENTS](mechanics/AGENTS.md) and the owning package card |
| Inspect the current consumer path | [CONSUMER_GUIDE](docs/CONSUMER_GUIDE.md), then the owner surfaces it names |
| Inspect detailed docs and surface maps | [docs](docs/README.md) |
| Change generated, manifest, schema, or example payloads | start with the nearest local `AGENTS.md` under `manifests/`, `generated/`, `schemas/`, `examples/`, `scripts/`, or the owning mechanic part |
| Validate or prepare release-facing work | [AGENTS](AGENTS.md), [COMMAND_AUTHORITY](docs/validation/COMMAND_AUTHORITY.md), and the nearest local `AGENTS.md` |
| Work as an agent | [AGENTS](AGENTS.md), then the nearest nested route card |

## KAG Check

Before adding, trusting, or publishing a KAG-layer claim, open the smallest
owner that can answer it.

| Question | Owner route |
| --- | --- |
| May `aoa-kag` claim this? | [CHARTER](CHARTER.md), then [BOUNDARIES](docs/BOUNDARIES.md) |
| What source owns the authored meaning? | [SOURCE_POLICY](docs/SOURCE_POLICY.md), then the source repository or corpus |
| What kind of KAG surface is this? | [KAG_MODEL](docs/KAG_MODEL.md) |
| Is this a source-home or future local `/kag` protocol question? | [kag](kag/README.md) and [LOCAL_SUBTREE_PROTOCOL](kag/LOCAL_SUBTREE_PROTOCOL.md) |
| Is this a repeatable operation around lift, projection, bridge, handoff, maturity, quarantine, or regrounding? | [mechanics](mechanics/README.md), then the owning package |
| Is this generated or compact? | source surface -> manifest or builder -> generated output -> validator |
| Is this proof, memory, routing, role, playbook, skill, technique, runtime, stats, or authored ToS truth? | route to `aoa-evals`, `aoa-memo`, `aoa-routing`, `aoa-agents`, `aoa-playbooks`, `aoa-skills`, `aoa-techniques`, `abyss-stack`, `aoa-stats`, or `Tree-of-Sophia` |
| Has provenance, non-identity, or owner return weakened? | [BRIDGE_CONTRACTS](docs/BRIDGE_CONTRACTS.md), [docs](docs/README.md), and the owning mechanic package |

## Current Contour

`aoa-kag` is in derived-substrate release hardening. The current public shape
includes a manifest-backed KAG registry, source-owned federation export
posture, bounded lift packs, ToS chunk and route packs, retrieval-axis packs,
reasoning handoff, return regrounding, maturity governance, tiny-consumer
support, counterpart review posture, and one bounded cross-source projection.
It also carries the repo-self kernel for artifacts, directories, anchors,
entities, Git events, assertions, relations, provenance, temporal/trust
profiles, ABI/sign posture, access, federation, retrieval projection, and
query coordinates. Its current canonical form separates a logical corpus
identity from a v4 tiered distribution identity. Git carries the deterministic
hot/bootstrap surface and delivery contracts; a content-addressed artifact
plane carries the complete cold family. The exact seven-file v2 form remains
an on-demand compatibility view. During migration, shadow copies remain in Git
until trust, offline, canary, and runtime proofs permit externalization.

That contour is not a claim that `aoa-kag` is a full graph engine. The layer
still pauses before widening new `AOA-K-*` families while neighboring owners
publish stronger source exports, contracts, or proof lanes. `AOA-K-0008`
remains contract-only in the current posture.

For `Tree-of-Sophia`, KAG use still starts from source-owned tiny-entry and
canonical-tree surfaces before any downstream `aoa-kag` adjunct. For
`aoa-memo`, durable-consequence, retention, and live-ledger pressure returns to
memo-owned readiness surfaces instead of becoming KAG graph authority.

Detailed shipped-surface inventories live in [ROADMAP](ROADMAP.md),
[docs](docs/README.md), [mechanics](mechanics/README.md), manifests,
generated companions, and decision records. The root README should not become
that inventory.

## Core Districts

| District | Use for |
| --- | --- |
| [kag](kag/README.md) | active repo-local KAG protocol, canonical index family, and provider packet |
| [docs](docs/README.md) | KAG model, boundaries, source policy, bridge contracts, consumer guide, validation topology, and decisions |
| [mechanics](mechanics/README.md) | repeatable KAG operation topology and package-local routes |
| [manifests](manifests/AGENTS.md) | source-authored lift controls and output refs |
| [generated](generated/AGENTS.md) | derived read models and compact payload companions |
| [schemas](schemas/AGENTS.md) and [examples](examples/AGENTS.md) | machine-checkable payload contracts and public-safe examples |
| [scripts](scripts/AGENTS.md) and [tests](tests/AGENTS.md) | builders, validators, decision-index helpers, and regression surfaces |
| [evals](evals/README.md) | KAG-local proof pressure before central `aoa-evals` adoption |
| [stats](stats/README.md) | owner-local statistical questions, measurement contracts, and evidence-linked reference packets |
| [skills](skills/README.md) | canonical callable KAG procedure, capability contract, and OS user exposure declaration |
| [quests](quests/README.md) | durable KAG obligations and source quest records |
| [.agents](.agents/AGENTS.md), [.github](.github/AGENTS.md), and [config](config/AGENTS.md) | companion agent lanes, GitHub platform support, and repo-local configuration |

Generated and compact surfaces route and transport meaning. Authored source
docs, manifests, schemas, builders, validators, tests, decision records, and
sibling owner repositories keep authority.

## Validation

Executable validation routes live in [AGENTS](AGENTS.md#validation),
[COMMAND_AUTHORITY](docs/validation/COMMAND_AUTHORITY.md), and the nearest
nested `AGENTS.md`.

Use this README to choose the route, not to run the route.

## Working Rule

Grow the substrate by making the next source-grounded knowledge route clearer.

Add manifests, generated companions, schemas, examples, mechanics, decisions,
tests, and local `/kag` protocol surfaces only where they preserve source
ownership, provenance, bounded graph or retrieval readiness, validation, and
return to stronger owners. When detail belongs to a source repository,
mechanic, generated companion, roadmap, changelog, quest, decision record,
docs map, or route card, route it there instead of making this README carry it.

## License

Apache-2.0
