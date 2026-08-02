# Fail-Closed Accelerated Schema Validation

## Index Metadata

- Decision ID: AOA-KAG-D-0032
- Original date: 2026-08-01
- Surface classes: validation guard, CI performance, schema engine, dependency admission
- KAG surfaces: repository family validation, provider-home audit, OS-wide coverage
- Source lanes: aoa-kag, provider registry
- Guard families: exact engine version, bounded schema vocabulary, Python shadow, fail-closed fallback, explicit rollback
- Posture: accepted

## Context

The strict release path validates the complete repository family for every
configured owner and then composes all owners into OS-wide coverage. Profiling
showed that Python JSON Schema evaluation dominated much of this required
semantic work. Exact-byte compiled-validator reuse reduced repeated setup, but
did not produce a reproducible hosted improvement large enough to accept as the
remaining answer.

The pressure is to accelerate the same blocking proof, not to remove owners,
schemas, semantic cross-reference checks, generated fixed-point work, or
standalone fallback behavior. A replacement schema engine also cannot be
treated as equivalent for every future schema feature merely because it
implements the same draft family.

A bounded `jsonschema-rs==0.49.2` candidate was therefore tested against the
current admitted schema vocabulary and payload corpus. The differential corpus
covered 65 schema/payload cases with no engine mismatch. Two paired hosted
full-audit comparisons completed in 361 versus 583 seconds and 320 versus 583
seconds, saving 222 seconds (38.1 percent) and 263 seconds (45.1 percent).
Both runs retained every configured owner and blocking release stage, reported
zero engine disagreement, and used only typed safe fallback for the known
unadmitted `propertyNames` vocabulary. This satisfied the predeclared
two-strong-win early-stop gate.

## Decision

Admit exactly `jsonschema-rs==0.49.2` as an optional accelerated evaluator for
repository-family payloads only when the complete schema uses the explicitly
admitted vocabulary and local references. Python `jsonschema` remains the
compatibility and fail-closed authority: the first valid instance for each
exact engine-version, schema-byte, and payload-shape route is shadow-validated
in Python; every accelerated rejection is confirmed in Python; and any
missing or wrong engine version, unknown vocabulary, non-local reference,
engine error, or disagreement executes the Python path.

Keep all semantic cross-reference assertions, owner ordering, coverage parity,
generated fixed-point, artifact, and landing gates unchanged. Emit typed
per-run engine, version, fast-path, shadow, rejection, fallback-reason, and
disagreement telemetry. `AOA_KAG_FORCE_PYTHON_SCHEMA_VALIDATION=1` is the exact
operational rollback and comparison route; removing the optional dependency
also preserves the Python path.

Vocabulary admission is closed by default. A future schema keyword or engine
version must first receive focused behavior tests and differential corpus
coverage, then independently satisfy correctness and hosted benefit gates. It
does not inherit this decision by similarity.

## Options Considered

- Keep only exact-byte Python validator compilation reuse: retained as a
  bounded in-process optimization, but insufficient as the accepted hosted
  acceleration.
- Use a pinned native standards-compliant evaluator under a bounded admission
  gate with Python shadow, confirmation, fallback, and rollback: selected.
- Replace Python unconditionally or accept an engine version range: rejected
  because vocabulary/version drift could silently change proof semantics.
- Remove validators, owners, semantic assertions, or generated checks:
  rejected because lower wall time would come from weaker proof.
- Reuse proof fragments across runs: still deferred by AOA-KAG-D-0029 until an
  owner-governed artifact class and consumer admission route exist.
- Use partial-clone checkout filtering in the same change: tested separately.
  `blob:none` regressed aggregate checkout-plus-proof time by 16.3 percent;
  `blob:limit=1m` was approximately neutral at 0.97 percent slower while
  reducing transferred object storage. Preserve the latter as a separate
  hosted candidate so its causality and cold-proof cost remain measurable.

## Rationale

The selected route changes the evaluator for a provably bounded input class,
not the set or authority of facts being proved. Exact pinning and closed
vocabulary admission prevent a dependency or schema expansion from widening
the fast path implicitly. Python shadowing samples accelerated acceptance,
Python confirmation prevents a native false rejection from becoming a proof
failure, and fallback makes ambiguity cost time rather than correctness.

The paired hosted effect is large enough to justify the added implementation
surface and remains visible independently of checkout variance. Keeping
partial-clone and cross-run reuse outside this decision avoids combining
uncertain methods with the accepted cause.

## Consequences

- Full hosted audits keep the same owners, payloads, semantic assertions,
  generated outputs, and blocking verdicts while current admitted schemas use
  the faster evaluator.
- Unknown vocabulary, version drift, native errors, or disagreement degrade to
  Python validation rather than weakening or blocking solely on acceleration.
- Dependency installation and engine telemetry become part of source-fast,
  compatibility-canary, and release workflow maintenance.
- Python remains required; this decision does not authorize its removal or a
  native-only proof claim.
- `AOA_KAG_FORCE_PYTHON_SCHEMA_VALIDATION=1` provides immediate comparison and
  rollback without changing schema or proof topology.
- Checkout filtering remains a separately measurable future experiment.
  Cross-run proof caching remains blocked on AOA-KAG-D-0029.
- An effective future validation DAG may route only from typed owner and input
  dependencies; it may not infer proof equivalence from the generated graph or
  use this engine decision to skip required nodes.

## Source Surfaces

- `scripts/validators/repo_local_kag_index.py`
- `scripts/coverage_run.py`
- `tests/test_repo_local_kag_index.py`
- `.github/actions/repo-local-kag-index/action.yml`
- `.github/workflows/repo-validation.yml`
- `.github/workflows/compatibility-canary.yml`
- `docs/validation/CI_EVIDENCE_DAG.md`
- `docs/validation/COMMAND_AUTHORITY.md`
- `docs/decisions/AOA-KAG-D-0029-defer-cross-run-owner-proof-fragments.md`

## Validation

Regenerate and validate decision indexes and the repository-local KAG family.
Run focused admission, exact-version, fallback, rejection-confirmation,
disagreement, rollback, differential-corpus, and telemetry tests; the complete
test suite; source-fast; and the full release continuation under the host
resource gate. Hosted acceptance requires at least two of three paired wins
with median full-job saving of at least 60 seconds or 15 percent, zero engine
disagreements, only typed admitted fallbacks, and every existing required job.
Two wins each exceeding 90 seconds permit the predeclared early stop. After the
decision is included, require one final clean hosted workflow on the exact
landing head and one clean post-merge `main` workflow.
