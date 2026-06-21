# Reasoning Handoff Validation

Run:

```bash
python mechanics/checkpoint/parts/reasoning-handoff/scripts/validate_reasoning_handoff.py
python -m unittest discover -s mechanics/checkpoint/parts/reasoning-handoff/tests -p 'test_*.py'
```

For repo-wide compatibility after manifest or generated surface changes, also
run:

```bash
python scripts/generate_kag.py
python scripts/validate_kag.py
python scripts/validate_mechanics_skeleton.py
```

The repo-wide generated lane still checks full handoff-pack parity through the
part-local generated outputs. This part owns the focused checkpoint operation
contract around handoff guardrails, counterpart contract refs, and owner-state
stop-lines.
