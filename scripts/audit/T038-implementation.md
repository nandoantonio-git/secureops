Added [test_taint.py](/workspaces/sec-project/secureops/tests/unit/test_taint.py:1) with TDD coverage for Python taint flow:

- Detects `request.args["email"]` flowing into `cursor.execute(query)` as `python.sql.tainted_execute`
- Verifies the parameterized clean fixture produces no taint findings

Verification:
- `python -m py_compile secureops/tests/unit/test_taint.py` passed
- `bash scripts/gate.sh secureops/tests/unit/test_taint.py` passed
- `bash scripts/gate.sh` passed
- `pytest secureops/tests/unit/test_taint.py` fails as expected for TDD because `app.engine.taint` is not implemented yet (`ModuleNotFoundError`)