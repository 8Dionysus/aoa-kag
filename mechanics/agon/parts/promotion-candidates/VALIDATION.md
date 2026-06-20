# Promotion Candidate Validation

Run:

```bash
python mechanics/agon/parts/promotion-candidates/scripts/build_promotion_candidate_registry.py --check
python mechanics/agon/parts/promotion-candidates/scripts/validate_promotion_candidate_registry.py
python -m unittest discover -s mechanics/agon/parts/promotion-candidates/tests -p 'test_*.py'
```

The builder may write only `generated/agon_kag_promotion_candidate_registry.min.json`
when run without `--check`.
