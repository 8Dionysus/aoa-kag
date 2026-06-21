# Quest Source Store And Spark Lane Placement

## Index Metadata

- Decision ID: AOA-KAG-D-0008
- Original date: 2026-06-21
- Surface classes: questbook/source-store, agent-lane, root route, validation guard, docs/decisions
- KAG surfaces: quest source records, Questbook mechanic, Codex Spark fast-loop lane, agent-facing route mesh
- Source lanes: aoa-kag, Agents-of-Abyss, Tree-of-Sophia, aoa-memo, aoa-evals, aoa-techniques, aoa-routing
- Guard families: source-owned authority, lane-state topology, generated-reader boundary, agent-lane placement, Spark done-or-handoff, no-root-Spark
- Posture: accepted

## Context

The mechanics refactor moved Questbook schemas, examples, validation, and tests
into `mechanics/questbook/parts/quest-store/`, but the active quest source
records still lived as flat files under `quests/AOA-KAG-Q-*.yaml`. That shape
validated locally, but it did not match the mature repo-family source-store
pattern where `quests/` is a lane-first lifecycle district and mechanics owns
the operation law around it.

At the same time, `aoa-kag` still had root `Spark/` as a fast-loop lane for
GPT-5.3-Codex-Spark sessions. Refactored sibling repos such as
`Tree-of-Sophia`, `Agents-of-Abyss`, `aoa-techniques`, `aoa-memo`, and
`aoa-evals` place maintained Spark guidance under `.agents/spark/` so root
topology stays reserved for source, generated, mechanics, config, docs,
validation, and public surfaces.

The web calibration for Codex Spark also supports a bounded lane rather than a
new root organ: OpenAI describes GPT-5.3-Codex-Spark as a research-preview,
real-time, lightweight coding model optimized for targeted edits and
interactive work, while OpenAI Codex guidance treats `AGENTS.md` as durable
repository guidance loaded by the agent.

## Decision

`aoa-kag` will keep durable quest source records in a lane/state source-store:

```text
quests/kag/<state>/AOA-KAG-Q-####.yaml
```

`QUESTBOOK.md` remains the public human index. `quests/` owns source-record
placement. `mechanics/questbook/parts/quest-store/` owns schemas, examples,
validator, and focused tests for the Questbook operation contract.

`aoa-kag` will move root `Spark/` into:

```text
.agents/spark/
```

`.agents/AGENTS.md` owns agent companion lane placement. `.agents/spark/AGENTS.md`
owns the local GPT-5.3-Codex-Spark fast-loop posture. `.agents/spark/SWARM.md`
is used only when a Spark swarm is explicitly requested.

No full Spark scenario registry is introduced in this slice. The current KAG
pressure needs a narrow fast-loop route card and swarm recipe, not registered
scenario payloads, handoff/result schemas, or extra Spark-local scripts.

## Options Considered

- Keep flat `quests/*.yaml` and root `Spark/`: smallest diff, but it preserves
  two active topology shapes already superseded by mature sibling repos.
- Move quests into mechanics: would make validation local, but would put source
  quest records inside an operation package and confuse source-store ownership.
- Use lane/state `quests/kag/<state>/` and `.agents/spark/`: matches the
  source-store and agent-lane patterns while keeping mechanics and source
  records separate.
- Add a full Spark scenario registry now: useful when repeated Spark scenarios
  exist, but premature for the current `aoa-kag` Spark pressure.

## Rationale

Quest source records should be durable public source objects, not mechanics
payloads and not a flat root bucket. The lane/state layout lets path, YAML
state, `QUESTBOOK.md`, and quest-store examples reinforce the same lifecycle
claim.

Spark is a model-facing companion lane. It helps fast sessions stay bounded,
source-first, and interruptible, but it does not own KAG meaning or generated
truth. Placing it under `.agents/` keeps the root tree focused on repository
organs and makes Spark guidance follow the same agent-lane topology used by
the mature sibling repos.

## Consequences

Good consequences:

- flat active `quests/AOA-KAG-Q-*.yaml` source paths are gone;
- quest examples now point at real lane/state source paths;
- the quest-store validator checks path shape, state-directory parity, and
  absence of root quest aliases;
- root `Spark/` is gone as an active lane;
- `.agents/` now owns companion lane placement and `.agents/spark/` owns Spark
  fast-loop posture.

Tradeoffs:

- source path strings changed in quest catalog and dispatch examples;
- future quest state changes must move files between state directories;
- future Spark scenario registry work remains intentionally deferred until
  repeated KAG-specific Spark scenarios justify it.

Future contributors must not infer that `.agents/spark/` is a mechanics
package, generated read model, proof surface, or runtime route.

## Source Surfaces

- `AGENTS.md`
- `DESIGN.md`
- `DESIGN.AGENTS.md`
- `QUESTBOOK.md`
- `quests/AGENTS.md`
- `quests/README.md`
- `quests/kag/AGENTS.md`
- `quests/kag/README.md`
- `mechanics/questbook/README.md`
- `mechanics/questbook/PARTS.md`
- `mechanics/questbook/PROVENANCE.md`
- `mechanics/questbook/parts/quest-store/CONTRACT.md`
- `mechanics/questbook/parts/quest-store/scripts/validate_quest_store.py`
- `.agents/AGENTS.md`
- `.agents/spark/AGENTS.md`
- `.agents/spark/SWARM.md`
- OpenAI, `Introducing GPT-5.3-Codex-Spark`:
  https://openai.com/index/introducing-gpt-5-3-codex-spark/
- OpenAI Developers, `Codex best practices`:
  https://developers.openai.com/codex/learn/best-practices

## Validation

Run:

```bash
python mechanics/questbook/parts/quest-store/scripts/validate_quest_store.py
python -m unittest discover -s mechanics/questbook/parts/quest-store/tests -p 'test_*.py'
python scripts/validate_nested_agents.py
python scripts/validate_semantic_agents.py
python -m unittest tests.test_nested_agents_docs tests.test_validate_semantic_agents
python scripts/generate_decision_indexes.py
python scripts/generate_decision_indexes.py --check
python scripts/validate_decision_records.py
```

Use `python scripts/ci_gate.py --mode source-fast` when the route-facing change
is ready for closeout.
