# Promotion Candidate Validation

Use `docs/validation/COMMAND_AUTHORITY.md` and the nearest `AGENTS.md` for executable validation commands.

Part-local route:

- Builder check: `mechanics/agon/parts/promotion-candidates/scripts/build_promotion_candidate_registry.py` with `--check`.
- Validator: `mechanics/agon/parts/promotion-candidates/scripts/validate_promotion_candidate_registry.py`.
- Focused test target: `mechanics/agon/parts/promotion-candidates/tests/test_promotion_candidate_registry.py`.

The builder may write only this part's
`generated/agon_kag_promotion_candidate_registry.min.json` when run without
`--check`.
