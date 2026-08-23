Implemented T039.

Added:
- [test_secondary_rules.py](/workspaces/sec-project/secureops/tests/unit/test_secondary_rules.py:1) for vulnerable and safe JavaScript secondary fixtures.
- [secondary.py](/workspaces/sec-project/secureops/app/engine/rules/secondary.py:1) with deterministic DOM XSS detection for HTML-parsing property assignment, currently `innerHTML`/`outerHTML`.

Verification:
- Confirmed TDD red first: test import failed before `app.engine.rules.secondary` existed.
- `python -m pytest secureops/tests/unit/test_secondary_rules.py` passed.
- `python -m py_compile secureops/tests/unit/test_secondary_rules.py` passed.
- `bash scripts/gate.sh secureops/tests/unit/test_secondary_rules.py` passed.
- `bash scripts/gate.sh secureops/app/engine/rules/secondary.py` passed.
- `bash scripts/gate.sh` passed.

One broader targeted pytest run including `test_taint.py` failed because `app.engine.taint` is missing; that appears unrelated/pre-existing to this story. No commit made.