# Quest Store Validation

Run:

```bash
python mechanics/questbook/parts/quest-store/scripts/validate_quest_store.py
python -m unittest discover -s mechanics/questbook/parts/quest-store/tests -p 'test_*.py'
```

For repo-wide compatibility after a quest-store change, also run:

```bash
python scripts/validate_kag.py
python scripts/validate_mechanics_skeleton.py
```

The root `scripts/validate_kag.py` route delegates quest-store validation here
so existing release lanes keep working while questbook mechanics owns the
focused contract.
