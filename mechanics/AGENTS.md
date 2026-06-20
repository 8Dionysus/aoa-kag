# AGENTS.md

## Applies to

This card applies to `mechanics/` and every nested path until a nearer
`AGENTS.md` narrows the lane.

## Role

`mechanics/` is the KAG operation topology layer.

It routes repeatable operation pressure around the derived substrate without
turning mechanics into source truth, generated-output authority, proof verdict,
memory truth, routing policy, runtime implementation, or framework adapter.

## Read before editing

1. root `AGENTS.md`
2. `DESIGN.md`
3. `DESIGN.AGENTS.md`
4. `mechanics/README.md`
5. `mechanics/topology.json`
6. target package `AGENTS.md`, `README.md`, `PARTS.md`, and `PROVENANCE.md`
   when an active package is touched
7. target part `README.md` and validation route when a part exists
8. the stronger source, manifest, generated, schema, script, test, decision, or
   owner-repository surface named by the route

## Boundaries

- Mechanics are operations, not topic buckets.
- Root `mechanics/` has only `README.md`, `AGENTS.md`, and `topology.json`.
- Do not add root rosters, migration ledgers, backlogs, templates, notes,
  `_meta/`, scratch, or root `legacy/` holding surfaces.
- Common-center package directories are KAG-local route homes. They do not
  import center authority or move artifacts by themselves.
- Do not create non-center package directories until repeatable KAG operation
  pressure has source surfaces, payload classes, owner split, stop-lines, and
  local validation.
- Do not create part directories until a functioning sub-mechanic has a stable
  purpose, payload class, local contract, stop-lines, and validation.
- Do not move docs, manifests, generated outputs, schemas, examples, scripts,
  tests, or eval intake into mechanics just to mirror sibling repositories.
- Do not claim source-authored meaning, proof doctrine, memory truth, routing
  authority, role meaning, scenario composition, skill execution, technique
  canon, runtime state, or Tree of Sophia canon from this lane.
- Local `/kag` protocol pressure routes through `kag/`. It still stays out of
  mechanics packages and sibling repositories until schemas, examples, and
  validation activate the contract.

## Validation

For mechanics root changes, run:

```bash
python scripts/validate_mechanics_skeleton.py
python scripts/validate_nested_agents.py
```

For package-local payload changes, run the package or part validator named by
the nearest route card, then the repository release gate when the change is
release-facing.

## Closeout

Report which mechanics surface changed, whether any package or payload was
created, which stronger owner stayed stronger, which validator proved the
topology, any skipped checks, and the next owner route.
