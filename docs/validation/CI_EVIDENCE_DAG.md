# CI Evidence DAG and Optimization Protocol

This document is the working cost model for KAG validation. It does not replace
the command authority in `config/validation_lanes.json`, change a proof verdict,
or authorize proof reuse. It makes dependencies, repeated work, measurement,
and experiment admission explicit so a faster run remains the same proof.

## Current baseline

The latest exact-main postmerge before the bounded-checkout landing is
[`30736109206`](https://github.com/8Dionysus/aoa-kag/actions/runs/30736109206)
at `6e3de285236dfa5952eeb911dec33c602360445f`. Its critical workflow span was
398 seconds: source-fast and owner-family took 108 seconds, the full OS-wide
job took 273 seconds, and the summary took 5 seconds. The full job spent about
114 seconds in checkout fan-in and 148 seconds in the release command. This is
the production comparison baseline for the bounded public-provider checkout
wave.

The detailed post-`AOA-KAG-D-0032` component run, observed on 2026-08-01,
was [`30728022522`](https://github.com/8Dionysus/aoa-kag/actions/runs/30728022522)
at exact commit `6c6d94fe7963da726f38dba11276fe8208643d33`:

- source-fast and owner-family job: 113 seconds, including 23 seconds across
  its checkout steps, 20 seconds for the leading family check, and 59 seconds
  for source-fast validation;
- full OS-wide job: 374 seconds;
- full provider checkout fan-in: 121 seconds;
- generated/release audit command: 237 seconds;
- run-scoped release-continuation lane wall time: 235.746 seconds;
- provider coverage build: 100.718 seconds over all 21 configured owners;
- OS-wide validation command: 197.160 seconds, with 195.257 seconds summed
  across provider-home timings;
- portable-family semantic validation: 33.631 seconds summed across the
  release-continuation receipt;
- the first and final local validations cost 10.851 and 10.656 seconds;
- process peak RSS observed by the release receipt: 550,040 KiB;
- the release receipt recorded 202 accelerated accepts, 23 Python shadow
  confirmations, two typed `propertyNames` fallbacks, and zero disagreements.

The same run's critical job span was 499 seconds and its three job runtimes
summed to 491 seconds. The residual source job is not one opaque 113-second
node: checkout steps consumed 23 seconds, the leading family action 20
seconds, and source-fast validation 59 seconds. Inside that last step,
`scripts/run_tests.py` consumed 45.561 seconds, of which the root `tests/`
discovery occupied approximately 39.778 seconds; the 28 mechanics-part homes
then completed in approximately 5.751 seconds. Local KAG validation added
10.715 seconds. This makes the root test corpus, not broad mechanics-test
parallelism, the first source-fast profiling target.

The pre-acceleration postmerge run
[`30710043887`](https://github.com/8Dionysus/aoa-kag/actions/runs/30710043887)
remains the comparison point: source-fast was 115 seconds and the full job was
606 seconds. The admitted evaluator therefore removed 232 seconds, or 38.3
percent, from that full hosted job while source-fast remained effectively flat.

Impact routing is already a real bounded saving, not a hypothetical DAG edge.
PR 191 recorded three first-attempt hosted `owner-local` workflows at one exact
workflow blob: 198, 188, and 179 seconds (median 188 seconds). Every sample kept
source-fast and owner-family blocking, reported the OS-wide audit as
`correctly-not-required`, and ended in the typed required summary. Those runs
prove routed execution and its absolute cost; they are not a paired
counterfactual against an otherwise identical full audit, so no causal saving
is attributed to the difference from the current 499-second full critical
span.

The floating compatibility canary is supplementary drift detection, not proof
that makes an owner-local skip valid. Its latest observed scheduled run,
`30695223927`, failed at pre-fix commit `32a8b6f` because the retired `Dionysus`
provider had no admitted manifest. `AOA-KAG-D-0031` and PR 198 removed that
retired provider from the registry and both workflows at `ba780519`; current
main contains that fix. A scheduled or manual exact-current-main canary has not
yet reconfirmed the repair, so current hosted canary health remains pending
rather than green by inference.

These values are an orientation baseline, not a performance guarantee. Hosted
comparisons must use current paired runs because runner placement and shared
host load are noisy.

## Dependency graph

The graph has independent branches, barriers, and one real strongly connected
component (SCC). It is therefore useful as a component DAG only after the fixed
point is collapsed.

```text
owner checkout + command authority
        |
        +--> source-fast proof ------------------------+
        |                                              |
        +--> self owner-family proof ------------------+--> landing summary
        |
        +--> bounded public full-history checkout wave --+
        +--> isolated private pinned checkout ------------+--> complete provider identity capture
                    |
                    +--> provider proof A --+
                    +--> provider proof B --+--> canonical owner composition
                    +--> ...                +           |
                    +--> provider proof N --+           v
                                              [self_coverage_fixed_point SCC]
                                              coverage -> generated KAG
                                                 ^              |
                                                 |              v
                                                 +-- portable family
                                                         |
                                                         v
                                              parity checks + final local
                                                         |
                                                         v
                                                artifact/release gates
```

The provider proofs are logically independent after the complete input
identity is captured. Their result is not admissible until every configured
owner appears exactly once in canonical order and the complete input identity
is rechecked. That shape permits bounded scheduling experiments, but it does
not imply that more workers are faster: the providers contend for CPU, memory,
filesystem cache, and Git object access.

The `self_coverage_fixed_point` SCC is genuine. Root coverage affects generated
KAG surfaces; generated KAG affects the root portable family; the root family
is itself one coverage input. A pure acyclic execution would either omit an
edge or weaken the fixed-point proof. The safe DAG node is the entire SCC,
whose internal convergence and final `--check` operations remain blocking.

## Typed telemetry

Every lane run keeps its existing ephemeral coverage packet and JSONL receipt.
Additive `aoa-kag-validation-timing-v1` events measure:

- each canonical validation command;
- each OS-wide provider-home proof;
- the root repo-local index phases: read, payload validation, source rebuild,
  parity, repository-family build, family parity, semantic validation, portable
  rebuild, and portable parity.

The same run receipt aggregates schema-engine events by exact engine version,
fast acceptance, Python shadow confirmation, accelerated rejection, typed
fallback reason, and disagreement. Those counters explain which evaluator ran;
they never replace a schema or semantic verdict.

Each timing binds a component type and ID, pass/fail status, wall time,
user/system CPU, process peak RSS observation, and bounded component details.
The aggregate receipt reports typed records and wall totals by component type.
Telemetry publication is deliberately degraded-only: losing a timing may make
the performance evidence incomplete, but cannot turn a failing proof green or
a passing proof red.

## Methods that remain live candidates

No candidate is rejected merely because another method looks simpler or one
run is noisy. Each method receives its own cold-path, identity, resource, and
hosted comparison evidence.

| Method | Potential saving | Required safety boundary | Current posture |
| --- | --- | --- | --- |
| In-process compiled-schema reuse | avoid parsing and meta-validating identical schema bytes for every owner payload | cache key is the complete schema bytes; every payload and semantic assertion still executes; changed bytes compile cold | retained bounded primitive; insufficient hosted improvement alone |
| Bounded accelerated schema evaluation | reduce per-payload JSON Schema interpreter cost | exact engine version, closed vocabulary and local references, first-valid Python shadow, Python-confirmed rejection, typed fallback/disagreement, explicit Python rollback | accepted by `AOA-KAG-D-0032` after two strong paired hosted wins |
| Exact same-run root-family proof | avoid a later process repeating semantic family assertions already completed in the same lane | run ID/lane, root, portable-family digest, validator/schema/runtime epoch, self-digest, cold fallback | locally effective, but failed the three-pair hosted benefit gate; do not land unchanged |
| Checkout/history routing | remove independent checkout waits from the critical path without reducing proof inputs | retain complete commit history and exact pins; isolate secret-owned checkout; bound workers; compare checkout plus real owner proof, missing objects, storage, and fallback | bounded three-worker full-history public wave accepted by `AOA-KAG-D-0033`; `blob:none` rejected for time and `blob:limit=1m` rejected after three semantic proof failures |
| Provider validation algorithm | reduce cold scan/decode/build work without caching a verdict | same schemas, source bytes, family parity, coverage row, and final identity barrier | bounded relation lookup and copy isolation accepted by `AOA-KAG-D-0034`; profile the remaining largest providers before another mechanism |
| SCC-aware bounded scheduling | overlap independent provider proofs or prefetch without oversubscribing the runner | canonical barrier, deterministic output, bounded workers/RSS, cancellation and cold serial fallback | root family/coverage cycle is now modeled as one atomic ordered SCC; resource-class provider waves remain unadmitted |
| Fail-closed impact routing | avoid the full OS-wide branch for positively admitted owner-local PR changes | source-fast and owner-family always block; mixed, unknown, malformed, empty, unprovable, non-PR, main, and manual inputs route full; required summary rejects an invalid skip | accepted by `AOA-KAG-D-0022`; hosted owner-local cost is measured, while exact-current canary health and a paired counterfactual remain open evidence |
| Cross-run owner fragments | replace unchanged external-owner proof with admitted prior evidence | owner-admitted artifact class, trusted main producer, provenance, expiry/revocation, exact consumer gate, cold fallback | blocked by `AOA-KAG-D-0029`; preserve feasibility evidence |

The earlier whole-provider `workers=2` experiment remains a valid negative data
point: its hosted lane regressed even though local wall time improved. It rules
out that exact scheduling policy on that evidence; it does not rule out narrow
prefetch, memory-aware waves, a different provider partition, or faster cold
algorithms. Likewise, one hosted regression of leading-local omission is not
enough to discard all exact same-run reuse designs.

## Experiment protocol

Every candidate starts with a proof-equivalence matrix. It must name the exact
assertions retained, the work moved or omitted, the identity fields that bind
reuse, invalidation cases, and the cold fallback. Missing, malformed,
ambiguous, changed, stale, or tampered evidence always executes the full cold
proof or fails closed according to the existing owner contract.

The comparison sequence is:

1. capture a current cold baseline with typed command, provider, phase, CPU,
   RSS, file/byte, and Git-invocation evidence;
2. prove local output and verdict parity, negative invalidation cases, and the
   complete generated fixed point;
3. compare cold candidate versus cold main on the same host when possible;
4. run interleaved hosted main/candidate pairs, normally at least three pairs,
   and retain every run including regressions and outliers;
5. compare median wall time, pair wins, CPU, peak RSS, checkout time, and cold
   fallback overhead rather than selecting the best single run;
6. land only a reproducible material improvement with all blocking proofs
   intact, then verify the merged postmerge path.

A hosted candidate passes the benefit gate only when it wins at least two of
three comparable pairs and removes at least 60 seconds or 15 percent from the
targeted full-path median without a material cold-path or resource regression.
A smaller result may still land only for a separately proven resource benefit,
such as materially lower billed compute, storage, network, or RSS without a
meaningful latency regression. Failure, deferral, and inconclusive evidence
stay recorded so a promising mechanism is neither forgotten nor repeatedly
retried unchanged.

## DAG efficiency answer

An effective DAG is possible, but its main benefit is explicit identity and
scheduling, not automatic maximum parallelism. The safe future shape is:

- a component graph generated from canonical commands and proof dependencies;
- content and builder identities on every reusable edge;
- the fixed-point cycle represented as one SCC with an internal convergence
  contract;
- resource annotations for CPU, RSS, I/O, and history needs;
- deterministic canonical fan-in after independent provider nodes;
- same-run proof edges first; cross-run edges only after artifact admission;
- cold execution as the universal fallback.

This form can eliminate redundant work, route checkout depth, and schedule
independent nodes conservatively while preserving all current owner coverage.
It cannot safely turn owner truth into a cache key or remove the fixed-point
cycle.

## Experiment ledger

All local comparisons below used the same pinned 21-owner registry and the
canonical validators. `PYTHONDONTWRITEBYTECODE=1` kept disposable provider
checkouts clean; it did not change proof inputs or outputs. Absolute host times
are not substituted for hosted evidence.

| Candidate | Comparison | Result | Posture |
| --- | --- | --- | --- |
| Exact same-run semantic proof | three interleaved pairs of two local validators | warm lane 16.572/17.683/20.326 s versus forced-cold 21.936/22.278/23.608 s; warm won 3/3 by 5.364/4.595/3.282 s; each warm receipt recorded one issue and one exact hit | proof-equivalent local success; full-job hosted benefit still required |
| Exact same-run semantic proof | one full generated pair, normalized for provider-home time | warm non-provider 28.843 s versus forced-cold 32.783 s; final semantic traversal 5.187 s to 0; total wall was noisy and cold happened to win because its providers were 10.952 s faster | preserve candidate, do not infer from total alone |
| Exact same-run semantic proof | three paired GitHub-hosted full jobs against exact current main | candidate/main full jobs were 584/606, 577/541, and 577/543 s; release lanes were approximately 447/470, 450/421, and 441/417 s; one win and two losses, candidate median 577 s versus main 543 s | stop unchanged implementation and omit it from landing; reopen only when the proof edge removes a materially larger node or composes with admitted fragments |
| Exact-byte compiled schema | two complete interleaved OS-wide pairs | cached 198.435/214.097 s versus forced-cold 223.850/239.199 s; cached won both by 25.415/25.102 s; semantic component improved by 17.132/14.366 s | locally material candidate; third pair and hosted proof pending |
| Exact-byte compiled schema | third pair | cached half completed at 235.570 s; forced-cold admission was blocked by the host hard memory reserve and unknown-demand gate after swap activity | incomplete, do not count as a pair; retry only after resource admission |
| Bounded `jsonschema-rs==0.49.2` evaluation | current-corpus differential proof | 13 schema/payload pairs with five probes each, 65 cases total, zero disagreement; unknown `propertyNames`, wrong version, errors, and disagreement route to Python | correctness gate passed with closed vocabulary, local refs, shadow, rejection confirmation, and exact rollback |
| Bounded `jsonschema-rs==0.49.2` evaluation | two paired GitHub-hosted full jobs against exact current main | candidate/main full jobs were 361/583 and 320/583 s; candidate won 2/2 by 222 s (38.1 percent) and 263 s (45.1 percent), with all 21 owners, two typed `propertyNames` fallbacks, and zero disagreement | accepted by `AOA-KAG-D-0032`; two wins above 90 s satisfied the predeclared early stop |
| Full versus partial-clone checkout | cold exact-pin checkout plus real source snapshot and portable-family proof for Agents-of-Abyss, Tree-of-Sophia, and abyss-stack | aggregate full 95.349 s; `blob:none` 110.910 s (+16.3 percent, one win of three); `blob:limit=1m` 96.274 s (+0.97 percent, two small wins of three) | reject `blob:none` for CI time; retain `blob:limit=1m` as an isolated storage/hosted candidate rather than composing it with the accepted engine change |
| All-provider checkout scheduling | three paired hosted attempts on exact commit `d73e1199`, each followed by the identical complete release proof | sequential full jobs 324/317/280 s versus bounded three-worker full-history jobs 255/264/264 s; bounded won 3/3, medians 317 to 264 s, saving 53 s or 16.7 percent; exact pins, complete history, generated cleanliness, and zero missing objects held | accepted by `AOA-KAG-D-0033`; implementation still requires exact-head PR and postmerge proof |
| All-provider `blob:limit=1m` | the same three hosted attempts and complete release proof | object stores before proof were about one third smaller, but all 3/3 attempts changed `coverage_summary.migration_needed` and failed the blocking proof | reject for the full-audit lane; storage benefit does not establish semantic equivalence |
| Whole provider sweep with two workers | local plus hosted experiment recorded by PR 185 | local improved 7.86 percent, hosted lane regressed from 938.768 to 990.153 s | reject that exact scheduler; retain narrower DAG scheduling candidates |
| Leading-local omission | one hosted candidate recorded by PR 197 | candidate lane 486.930 s versus main 455.497 s with higher CPU | negative but noisy single run; do not generalize to all same-run proof reuse |
| Cross-run owner fragments | historical feasibility model in `AOA-KAG-D-0029` | optimistic mean gross saving 213.077 s, median zero; no admitted artifact class | deferred, no implementation or bypass |
| Digest copy elision, admitted source-schema routing, and exact-byte local schema-validator reuse | first exact local fused OS-wide pair, candidate `dc7d8a2f` versus control `6c6d94fe` | 85.851 versus 118.181 s, saving 32.330 s or 27.36 percent; candidate won 1/1, retained 21/21 owners, and reported zero fallback or disagreement | inconclusive: the pair predates the final cold-path commit, does not satisfy the two-win minimum, and is not hosted evidence |
| Final candidate root-test path | three interleaved local pairs, candidate `de61d446` versus control `6c6d94fe` | candidate won 3/3 while running 431 rather than 425 tests; median wall was 31.860 versus 32.747 s, saving 0.888 s or 2.71 percent; median RSS was 180,292 versus 191,344 KiB | corroborating mechanism evidence only; below the landing benefit gate |
| Final candidate source-fast path | three interleaved local pairs, candidate `de61d446` versus control `6c6d94fe` | candidate won 2/3; median wall was 42.712 versus 45.211 s, saving 2.498 s or 5.53 percent; all six canonical lanes passed with zero systemd-observed swap | retain for the full OS-wide comparison, but do not land for source-fast benefit alone because the material-saving gate failed |
| Global rollback testability | run the canonical test runner with `AOA_KAG_FORCE_COLD_SCHEMA_COMPILATION=1` and separately with `AOA_KAG_FORCE_PYTHON_SCHEMA_VALIDATION=1` | the first attempts exposed two behavior-specific tests per flag that inherited the global override and asserted the opposite path; after isolating those test preconditions, both complete runners passed in 60.737 and 43.381 s with 0 B swap | retain the test isolation as part of the rollback contract; full OS-wide rollback paths remain required before landing |
| Final candidate full OS-wide path | three interleaved local pairs, candidate `b3131a4b` versus control `6c6d94fe` | candidate won 3/3: 76.031/70.059/69.661 s versus 123.650/110.073/128.103 s; medians were 70.059 versus 123.650 s, saving 53.592 s or 43.34 percent; every run retained 21/21 owners, fused canonical fan-in, zero disagreement, and 0 B systemd swap | local benefit gate passed by percentage; exact hosted A/B remains mandatory |
| Final candidate full rollback paths | full OS-wide candidate at `b3131a4b` with each global rollback flag | forced-cold passed in 99.204 s with accelerated payload evaluation still admitted; forced-Python passed in 180.303 s with 191 typed Python fallbacks; both retained 21/21 owners, zero disagreement, and 0 B swap | correctness and rollback gate passed locally; these are fallback proofs, not candidate latency samples |
| Final hotspot attribution | parity benchmark over all 21 pinned owners | source-schema route saved 10.618 s across 21/21 cases; copy elision saved 4.963 s direct and 10.768 s on the prior double-copy helper path across 147/147 equal digests; schema-def cache saved 7.755 s across 149/149 cases | retained attribution evidence; full-path and hosted comparisons remain authoritative for benefit |
| SCC convergence strategy | bounded local regeneration trials on the candidate branch | naive simultaneous/Jacobi regeneration did not converge within four passes plus confirmation; ordered staging of family, coverage/root outputs, then family regeneration reached a clean fixed point and passed final checks | retained mechanism evidence: model the cycle as one atomic ordered SCC node; workflow benefit and exact-head proof remain pending |
| Fail-closed impact routing | PR 191 terminal hosted corpus plus classifier/summary negative corpus | three eligible owner-local workflows were 198/188/179 s (median 188 s), all kept both local proofs, correctly skipped the full audit, and passed the typed summary; unknown, invalid, empty, mixed, unprovable, and required-full skip cases are rejected by tests | retain the existing router; do not add a duplicate DAG classifier; separately reconfirm the post-PR-198 compatibility canary and do not claim paired causal saving |
| Cold reconstruction profile | three current cold baselines plus cProfile at `cc74651e` | `release_continuation` median 95.454 s; reconstruction consumed 52.206 profiled seconds, `copy.deepcopy` 36.982 s, relation-entry scans 20.119 s, while source snapshot capture was 5.809 s | algorithmic family reconstruction, not I/O or a generic worker increase, was the dominant new target |
| First-wins relation-source map | three interleaved local pairs at the same pins | candidate won 2/3 with a 21.6-percent median improvement, but lost one pair and one control accumulated swap | retain as promising mechanism evidence; do not admit alone |
| Selective repository-record copy | exact 21-owner build comparison | 45.798 to 42.105 s, saving 3.693 s or 8.06 percent; all external-owner outputs matched and focused mutation tests passed | below the standalone 15-percent gate; retain for combined proof |
| Selective portable-family reconstruction copy | exact 21-owner load-plus-build comparison | 82.149 to 70.824 s, saving 11.324 s or 13.79 percent; RSS fell and exact outputs matched | below the standalone 15-percent gate; retain for combined proof |
| Combined bounded reconstruction | three interleaved local full-path pairs, candidate `304ce44f` versus control `cc74651e` | candidate won 3/3; medians 90.752 to 73.040 s, saving 17.712 s or 19.52 percent; 21/21 owners, stable payloads, zero failed timings, zero swap, lower median RSS | local gate passed; admitted to immutable hosted comparison |
| Combined bounded reconstruction | three exact-head hosted `workflow_dispatch` pairs, candidate `304ce44f` versus control `cc74651e` | candidate won 3/3: 111.452/114.733/72.632 s versus 143.473/140.350/103.691 s; medians 140.350 to 111.452 s, saving 28.898 s or 20.59 percent; all six runs retained 21/21 owners, 76/76 timings, exact pins, stable per-head payloads, and zero disagreement | accepted by `AOA-KAG-D-0034`; median RSS also fell from 513,292 to 510,036 KiB |
| Combined bounded reconstruction postmerge | canonical push run `31250935353` at `fa6f71ee` | full proof passed in 112.382 s with 21/21 owners, 76/76 timings, zero reject/failure/disagreement, committed fixed point, and 509,820 KiB peak RSS | landed by PR 204; 19.93 percent faster than hosted control median and within 0.83 percent of candidate median |

The exact same-run semantic proof prototype was fail-closed and passed its
negative identity matrix, but its approximately 3--5 second local saving did
not survive full hosted variance. The mechanism remains useful design evidence
for a larger SCC or admitted owner-fragment edge; its code and feature flag are
not part of the landing diff.

Compiled-schema reuse is narrower still: the complete schema bytes are the
cache key inside one Python process. Schema meta-validation is reused, but
`iter_errors` and every family cross-reference assertion still run for every
owner. `AOA_KAG_FORCE_COLD_SCHEMA_COMPILATION=1` provides the exact cold
comparison and rollback route.

The accepted accelerated evaluator changes only the bounded JSON Schema
execution mechanism. Python remains installed and authoritative for shadow,
rejection confirmation, fallback, and disagreement. Unknown vocabulary or an
engine version other than exactly `0.49.2` selects Python, and
`AOA_KAG_FORCE_PYTHON_SCHEMA_VALIDATION=1` disables the accelerated path.

The final candidate's source-fast decomposition confirms that its main expected
benefit is not in the quick lane. Root discovery improved only 2.71 percent at
the median and the complete source-fast command improved 5.53 percent, below
the 15-percent or 60-second material-saving gate. The dominant candidate root
modules remain repo-local index tests (12.742-second median), repository-index
tests (5.744 seconds), local KAG validation tests (4.340 seconds), and MCP owner
review tests (3.256 seconds). This evidence keeps source-fast as a required
early-failure lane and avoids redesigning it around an effect too small for
hosted variance.

The rollback flags must also be usable around the complete test command, not
only around a hand-picked validator call. The first global forced-cold and
forced-Python source-fast attempts correctly changed runtime behavior but made
two behavior-specific tests in each run assert the opposite route. Those tests
now set their own precondition explicitly: cache-reuse tests disable the cold
override, while accelerator-fallback-cause tests disable the blanket Python
override. This does not hide or weaken either rollback path; the separate
forced-path tests remain blocking, and the complete canonical test runner now
passes under each global override. At `b3131a4b`, forced-cold passed the
complete fused path in 99.204 seconds and forced-Python passed in 180.303
seconds with 191 typed fallbacks. Both retained all 21 owners, the canonical
fan-in, zero disagreement, and zero systemd-observed swap.

The final unprofiled full-path local comparison passed the material-benefit
gate independently of the hotspot benchmark. Across three interleaved pairs,
the candidate won 3/3 and reduced the median from 123.650 to 70.059 seconds,
or 53.592 seconds and 43.34 percent. Median process CPU fell from 117.147 to
65.573 seconds while self-observed peak RSS remained approximately 506 MiB.
This is strong local evidence, not permission to land without hosted pairs.

Resource-wave modelling also narrows the next scheduling experiment. Seven
owners accounted for 64.0 percent of the profiled owner duration, while every
sub-three-second owner together accounted for only 5.9 percent and source
snapshot capture only 4.3 percent. Therefore idealized two-way partitioning is
not a new hypothesis after the real hosted `workers=2` regression. The distinct
remaining candidate is parallel provider checkout or object acquisition with
serial semantic proof and deterministic canonical fan-in.

The first post-`D-0032` cProfile of the fused OS-wide path took 327.898 seconds
under profiling. It attributed 105.084 cumulative seconds to deep copies,
57.385 seconds to 420 `payload_digest` calls, approximately 58.398 seconds to
21 source-index schema checks, and 28.253 seconds to 155 schema meta-checks.
Those figures identified the three current code candidates. Exact local
hotspot parity and three full-path pairs now corroborate them; hosted A/B and
canonical postmerge proof remain outstanding.

## Related decisions

- `AOA-KAG-D-0021`: run-scoped coverage proof reuse;
- `AOA-KAG-D-0022`: additive fail-closed impact routing;
- `AOA-KAG-D-0025`: exact same-run source-fast handoff;
- `AOA-KAG-D-0027`: history-bounded source-fast donor checkouts;
- `AOA-KAG-D-0028`: run-scoped provider coverage fusion;
- `AOA-KAG-D-0029`: defer cross-run owner proof fragments until artifact
  admission exists;
- `AOA-KAG-D-0032`: fail-closed accelerated schema validation.
- `AOA-KAG-D-0033`: bounded public provider checkout wave with private checkout
  isolation and sequential rollback.
- `AOA-KAG-D-0034`: bounded repository-family reconstruction with targeted
  copy isolation and an atomic ordered SCC.
