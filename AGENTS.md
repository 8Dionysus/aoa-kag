# AGENTS.md

Root route card for `aoa-kag`.

## Purpose

`aoa-kag` is the derived knowledge substrate layer of AoA.
It stores provenance-aware, source-first derived structures and graph-ready or retrieval-oriented projections that support downstream consumers without replacing authored meaning in source repositories.

## Owner lane

This repository owns:

- derived substrate structure and KAG-layer metadata
- provenance-aware lifted surfaces, normalized packs, manifests, schemas, examples, and generated outputs
- bridge, consumer, reasoning-handoff, and regrounding seams when defined here

It does not own:

- authored technique, skill, eval, memo, role, playbook, routing, or Tree of Sophia meaning
- framework-specific application code that belongs elsewhere
- source-replacing world-model sprawl

## Start here

1. `README.md`
2. `ROADMAP.md`
3. `CHARTER.md`
4. `docs/KAG_MODEL.md`
5. `docs/BOUNDARIES.md`
6. `docs/SOURCE_POLICY.md`
7. the target source, registry, pack, generated output, or capsule
8. `docs/AGENTS_ROOT_REFERENCE.md` for preserved full root branches


## AGENTS stack law

- Start with this root card, then follow the nearest nested `AGENTS.md` for every touched path.
- Root guidance owns repository identity, owner boundaries, route choice, and the shortest honest verification path.
- Nested guidance owns local contracts, local risk, exact files, and local checks.
- Authored source surfaces own meaning. Generated, exported, compact, derived, runtime, and adapter surfaces summarize, transport, or support meaning.
- Self-agency, recurrence, quest, progression, checkpoint, or growth language must stay bounded, reviewable, evidence-linked, and reversible.
- Report what changed, what was verified, what was not verified, and where the next agent should resume.

## Route away when

- canonical authored meaning must change in the source repository
- the task is routing, memory, eval, role, or playbook doctrine
- graph-ready wording starts to replace provenance or source authority

## Verify

Default read-only integrity pass:

```bash
python scripts/validate_kag.py
python scripts/validate_nested_agents.py
python -m unittest discover -s tests -p 'test_*.py'
```

If registries, packs, or generated KAG surfaces change, regenerate them and rerun the same pass. Use release checks from `docs/AGENTS_ROOT_REFERENCE.md` when preparing release parity.
For release-prep parity, also run `python scripts/release_check.py` and confirm `git status -sb`.

## Report

State which derived surfaces changed, whether semantics or metadata changed, whether provenance, bridge, handoff, or regrounding posture changed, and what validation ran.

## Full reference

`docs/AGENTS_ROOT_REFERENCE.md` preserves the former detailed root guidance, including branch docs, hard boundaries, and release-prep posture.
