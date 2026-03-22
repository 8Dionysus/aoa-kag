# Spark Swarm Recipe — aoa-kag

Рекомендуемый путь назначения: `Spark/SWARM.md`

## Для чего этот рой
Используй Spark здесь для одного lift/projection seam: provenance-aware lift, retrieval-ready section/chunk map, graph-friendly bounded schema или registry contract. Этот рой усиливает derived substrate и не даёт KAG тихо заменить source-owned meaning.

## Читать перед стартом
- `README.md`
- `CHARTER.md`
- `docs/KAG_MODEL.md`
- `docs/BOUNDARIES.md`
- `docs/SOURCE_POLICY.md`
- `ROADMAP.md`

## Форма роя
- **Coordinator**: выбирает один derived substrate seam
- **Scout**: картографирует source-owned inputs, projection outputs и provenance traces
- **Builder**: делает минимальный lift/projection diff
- **Verifier**: запускает `python scripts/validate_kag.py`
- **Boundary Keeper**: следит за source-first discipline и anti-graph-empire posture

## Параллельные дорожки
- Lane A: source-to-derived contract
- Lane B: schema / registry / generated KAG surface
- Lane C: provenance wording and retrieval/graph bounds
- Не запускай больше одного пишущего агента на одну и ту же семью файлов.

## Allowed
- чинить один provenance-aware lift
- делать section/chunk or node/edge views яснее и bounded
- обновлять compact KAG registry surface
- прояснять source-first conversion contracts

## Forbidden
- переписывать authored meaning здесь
- превращать KAG projections в canonical truth
- раздувать слой в graph platform or giant framework app
- терять provenance

## Launch packet для координатора
```text
We are working in aoa-kag with a one-repo one-swarm setup.
Pick exactly one target:
- one lift contract
- one projection surface
- one schema/registry seam

Return:
1. authoritative source-owned inputs
2. derived outputs
3. exact files to touch
4. provenance and anti-overbuild risks
```

## Промпт для Scout
```text
Map only. Do not edit.
Return:
- source-owned inputs
- current derived outputs
- provenance traces or gaps
- whether the seam is retrieval-oriented, graph-oriented, or registry-oriented
- whether this belongs here or upstream in a source repo
```

## Промпт для Builder
```text
Make the smallest reviewable change.
Rules:
- source repositories keep authored meaning
- keep derived surfaces explicit and reviewable
- keep graph readiness bounded
- preserve provenance visibility
```

## Промпт для Verifier
```text
Run:
- python scripts/validate_kag.py
Then report:
- commands run
- which derived surfaces changed
- whether provenance and boundedness remained explicit
```

## Промпт для Boundary Keeper
```text
Review only for anti-scope.
Check:
- no authored meaning migrated into KAG as source of truth
- no graph engine empire-building
- provenance remained visible
- framework adapters stayed downstream
```

## Verify
```bash
python scripts/validate_kag.py
```

## Done when
- один derived substrate seam tightened
- source inputs and derived outputs названы явно
- validator реально прогнан
- source-first discipline сохранена

## Handoff
Если обнаружен source wording bug, fix it upstream first in `Tree-of-Sophia`, `aoa-techniques`, `aoa-skills` или `aoa-evals`.
