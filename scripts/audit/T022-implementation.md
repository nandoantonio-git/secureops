Implemented T022 by adding [test_python_rules.py](/workspaces/sec-project/secureops/tests/unit/test_python_rules.py:1).

It covers:
- Python vulnerable fixture detection for `python.subprocess.shell_true`
- Safe Python fixture non-detection for `safe_request_handler.py`

Verification:
- `python -m pytest tests/unit/test_python_rules.py` fails as expected for TDD because `app.engine.rules.python` is not implemented yet.
- `python -m py_compile secureops/tests/unit/test_python_rules.py` passed.
- `bash scripts/gate.sh secureops/tests/unit/test_python_rules.py` passed.
- `bash scripts/gate.sh` passed.

No commit was made.