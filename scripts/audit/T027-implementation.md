Implemented T027.

Changes:
- Added [python.py](/workspaces/sec-project/secureops/app/engine/rules/python.py:1) with deterministic Python rules, exact source evidence extraction, import alias resolution, and findings for:
  - `python.subprocess.shell_true`
  - `python.os.system`
  - `python.yaml.unsafe_load`
- Added [conftest.py](/workspaces/sec-project/secureops/tests/conftest.py:1) so the requested root-level pytest command can import the local `app` package.

Verification passed:
- `python -m py_compile secureops/app/engine/rules/python.py`
- `pytest secureops/tests/unit/test_python_rules.py` → `2 passed`
- `bash scripts/gate.sh secureops/app/engine/rules/python.py`
- `bash scripts/gate.sh`

No commit was made.