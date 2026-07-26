# Bound Route Examples By Review Invariants

## Index Metadata

- Decision ID: AOA-KAG-D-0019
- Original date: 2026-07-25
- Surface classes: public example, validation guard, mechanics part
- KAG surfaces: ToS route lift, derived route pack, review fixture
- Source lanes: Tree-of-Sophia, distillation, generated projection
- Guard families: source-owned authority, schema parity, selected-content parity, coverage closure
- Posture: accepted

## Context

The public Zarathustra route-pack example duplicated the complete generated
payload: 92 nodes, 125 edges, and 155,091 bytes. The path was labeled as an
example, but its validator required byte-equivalent semantic content from the
entire generated read model. It therefore added a second review surface without
an independent fixture invariant.

The other public examples and generated payloads have distinct bounded,
authority, or compatibility roles. Byte equality alone does not authorize
their contraction.

## Decision

Keep the public example path, schema, source links, and provenance posture, but
make its role explicit: it is a reviewed invariant fixture containing ten nodes
and six edges selected from the current source-derived full payload.

The fixture must cover all nine canonical node types and all three edge kinds,
keep every selected edge endpoint inside the fixture, and preserve exact
selected node and edge content. The generated full and min route packs remain
unchanged and authoritative only as derived read models.

## Options Considered

- Keep duplicating the full generated payload in the public example.
- Remove the example and its stable path.
- Retain the path as a bounded, schema-valid invariant fixture.

## Rationale

A bounded fixture gives the public example an independent review purpose while
remaining subordinate to Tree of Sophia source meaning and KAG generation. It
reduces repeated payload without weakening source refs, schema validation,
generated parity, node-family coverage, edge-kind coverage, or endpoint
closure.

## Consequences

- The example becomes substantially smaller while its stable path remains.
- Selected source-derived content drift fails closed.
- Generated full/min payloads and the registry ABI do not contract.
- No other exact example/generated pair inherits this decision by similarity.
- Changing the reviewed ID set is a contract change requiring the same focused
  and release proof.

## Source Surfaces

- `mechanics/distillation/parts/tos-route-lift/CONTRACT.md`
- `mechanics/distillation/parts/tos-route-lift/manifests/tos_zarathustra_route_pack.json`
- `mechanics/distillation/parts/tos-route-lift/examples/tos_zarathustra_route_pack.example.json`
- `mechanics/distillation/parts/tos-route-lift/generated/tos_zarathustra_route_pack.json`
- `mechanics/distillation/parts/tos-route-lift/generated/tos_zarathustra_route_pack.min.json`
- `mechanics/distillation/parts/tos-route-lift/tests/test_tos_route_lift.py`
- `scripts/validators/examples/tos_examples.py`
- `scripts/validators/expected/tos_contracts.py`

## Validation

Run the part-local tests, decision-index checks, source-fast lane, generated
lane, release gate, repo-local KAG family checks, and exact forward/reverse
rollback proof.
