# Return Regrounding Validation

Run:

```bash
python mechanics/recurrence/parts/return-regrounding/scripts/validate_return_regrounding.py
python -m unittest discover -s mechanics/recurrence/parts/return-regrounding/tests -p 'test_*.py'
```

For repo-wide compatibility after manifest or generated surface changes, also
run:

```bash
python scripts/generate_kag.py
python scripts/validate_kag.py
python scripts/validate_mechanics_skeleton.py
```

The repo-wide generated lane still checks full return-pack parity through the
part-local generated outputs. This part owns the focused recurrence operation
contract around stronger refs, mode order, memo readiness ownership, and
source-first return posture.
