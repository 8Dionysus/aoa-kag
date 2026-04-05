# Contributing to aoa-kag

Thank you for helping shape the AoA KAG layer.

This repository is the knowledge substrate layer of AoA.
Contributions here should improve the clarity, coherence, and usefulness of derived knowledge surfaces rather than turning this repository into a replacement source corpus or a framework-specific graph monolith.

## What belongs here

Good contributions include:
- KAG layer definitions
- lifted knowledge surface definitions
- provenance and source-linkage guidance
- bounded normalization guidance
- framework-neutral registry, schemas, and validation
- clearer boundaries between source truth, derived knowledge, proof, memory, and routing

## What usually does not belong here

Do not use this repository as the default home for:
- authored technique bundles
- authored skill bundles
- authored eval bundles
- memory objects
- routing surfaces
- infrastructure implementation details
- giant framework-specific codebases with no reusable substrate contract

If a change mainly defines authored meaning, bounded execution, or bounded proof, prefer the specialized neighboring repository first.

## Source-of-truth discipline

When contributing, preserve this rule:
- `aoa-kag` owns derived knowledge substrate meaning
- neighboring AoA repositories and ToS sources still own their own meaning

Examples:
- `aoa-techniques` owns practice meaning
- `aoa-skills` owns execution meaning
- `aoa-evals` owns proof meaning
- `aoa-memo` owns memory meaning
- `Tree-of-Sophia` owns authored knowledge-architecture content

## How to decide where a change belongs

Ask these questions in order:

1. Is this change mainly about a derived knowledge surface, normalized projection, provenance-aware lift, or graph/retrieval-ready substrate?
   - If yes, it may belong here.
2. Is this change mainly about authored source meaning?
   - If yes, it probably belongs in the source repository or corpus.
3. Is this change mainly about bounded proof?
   - If yes, it probably belongs in `aoa-evals`.
4. Is this change mainly about memory truth?
   - If yes, it probably belongs in `aoa-memo`.
5. Is this change mainly about dispatch across repos?
   - If yes, it probably belongs in `aoa-routing`.
6. Is this change mainly about one framework consumer rather than the substrate itself?
   - If yes, keep it downstream of the KAG layer if possible.

## Pull request shape

A strong pull request in this repository should explain:
- what KAG-layer surface changed
- why the change belongs in `aoa-kag`
- what authoritative sources feed the surface
- what was intentionally not absorbed into this repository

## Before opening a PR

Run the current read-only validation battery:

```bash
python scripts/validate_kag.py
python scripts/validate_nested_agents.py
python -m unittest discover -s tests -p 'test_*.py'
```

If your change touched generated KAG outputs, regenerate and revalidate them before opening the PR:

```bash
python scripts/generate_kag.py
python scripts/validate_kag.py
python scripts/validate_nested_agents.py
python -m unittest discover -s tests -p 'test_*.py'
```

For release-prep parity, use:

```bash
python scripts/release_check.py
git status -sb
```

## Style guidance

Prefer:
- source-first discipline over graph theater
- explicit provenance over opaque transformation
- reviewable derived surfaces over magical knowledge claims
- bounded readiness over premature platform ambition
