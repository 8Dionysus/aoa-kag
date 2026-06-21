# Surface Growth Stop Rule Validation

Run:

```bash
python mechanics/growth-cycle/parts/surface-growth-stop-rule/scripts/validate_surface_growth_stop_rule.py
python -m unittest discover -s mechanics/growth-cycle/parts/surface-growth-stop-rule/tests -p 'test_*.py'
```

For repo-wide compatibility after maturity governance changes, also run:

```bash
python scripts/generate_kag.py
python scripts/validate_kag.py
python scripts/validate_mechanics_skeleton.py
```

The repo-wide generated lane still checks full maturity-pack parity. This part owns
the focused growth-cycle operation contract around owner waits, blocked growth,
and pause posture.
