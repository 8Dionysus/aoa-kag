# Capability Projection Owner Return

## Index Metadata

- Decision ID: AOA-KAG-D-0038
- Original date: 2026-08-11
- Surface classes: kag/source-home, generated projection, validation guard, owner return
- KAG surfaces: repo-local source surface index, artifact index, relation index, capability projection provenance
- Source lanes: owner-local capability homes, aoa-skills capability-home contract, OS Abyss repo-local kag homes
- Guard families: source-owned authority, generated projection, manifest provenance, owner return, relation evidence
- Posture: accepted

## Context

The capability-home contract declares three non-authoritative read models: a
JSON graph, a Markdown graph, and a skill-local routing card. The repo-local
KAG generator did not interpret that manifest. It therefore classified owner
paths outside a generic `generated/` directory as authored source, left
`generated_by` empty, and returned consumers to the projection itself.

This was not only a labeling defect. A generated routing card could compete
with the authored family contract during retrieval, and a consumer had no
typed `derives_from` route back to the capability owner.

## Decision

When an owner publishes `capabilities/port.manifest.json` with
`aoa_capability_home_port_v1`, classify every declared projection field as a
generated projection regardless of its physical directory. Resolve its
authored sources from the manifest's tracked capability-family root, preserve
the manifest as provenance material, preserve the declared external builder
and common validator routes, and return the consumer to the first authored
family contract.

All three declared projection paths must be distinct and tracked. The family
root must contain at least one tracked YAML contract. The declared owner must
equal the indexed repository, and `source.root_id` must resolve to exactly one
tracked family contract; that contract is the primary owner-return surface.
Malformed or incomplete recognized manifests fail closed rather than falling
back to authored-source classification. Incremental generation always rebuilds
these small declared records so stale authority cannot survive an unchanged
projection blob.

## Options Considered

- Infer authority from `read-models/`, `generated/`, or a filename: rejected
  because directory convention is weaker than the owner manifest and cannot
  supply an exact builder or owner-return route.
- Recognize only the JSON graph: rejected because the Markdown graph and
  routing card are produced by the same builder and would retain false source
  authority.
- Add metadata separately to each generated file: rejected because it
  duplicates one owner contract across read models and lets those read models
  describe their own authority.
- Interpret the complete capability-home manifest: selected because the owner
  already declares projection identity, source root, authority, and builder.

## Rationale

KAG owns derived provenance, not capability meaning. The capability owner
manifest is the strongest local evidence that the three files are projections;
the tracked family contracts are the stronger meaning to which retrieval must
return. One manifest-driven rule also works when a routing card must remain
inside a portable skill package and therefore cannot live under a generic
generated-output directory.

## Consequences

- Generated capability read models remain discoverable without competing as
  authored source.
- Each declared projection receives exact builder, validator, manifest, source,
  and owner-return provenance.
- Repository relation indexes emit deterministic `derives_from` edges from
  every declared projection to every tracked family contract it cites.
- Physical placement remains an owner packaging decision, not an authority
  decision.
- This proves projection provenance and returnability only. It does not prove
  routing quality, skill benefit, composition validity, or runtime freshness.

## Source Surfaces

- `DESIGN.md`
- `docs/BOUNDARIES.md`
- `docs/SOURCE_POLICY.md`
- `scripts/generate_repo_local_kag_index.py`
- `scripts/repo_local/indexes.py`
- `tests/test_repo_local_kag_index.py`
- `aoa-skills:schemas/capability-home-port.schema.json`
- `aoa-skills:scripts/build_capability_home_projection.py`

## Validation

Use a real owner-shaped fixture to compare source records, all three
projection records, owner-return routes, builder and validator provenance, and
the resulting `derives_from` relations. Preserve an incremental negative case
in which legacy authored-source records must be rebuilt. Then run source-fast,
generated parity, release validation, and the repository owner-family gate.
