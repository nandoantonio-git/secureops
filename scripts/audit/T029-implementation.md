Implemented T029.

Added reviewed remediation catalog in [templates.py](/workspaces/sec-project/secureops/app/remediation/templates.py:1) with:
- Python command injection template for `CWE-78` / subprocess shell usage.
- JavaScript DOM XSS template for `CWE-79` / unsafe DOM HTML sinks.
- Template selection and rendering into remediation recommendation fields.

Also added [fallback.py](/workspaces/sec-project/secureops/app/remediation/fallback.py:1) so deterministic fallback can use reviewed templates first, which makes the related fallback tests pass.

Verification passed:
- `python -m py_compile secureops/app/remediation/templates.py`
- `pytest secureops/tests/unit/test_remediation_templates.py` -> 4 passed
- `pytest secureops/tests/unit/test_remediation_fallback.py` -> 3 passed
- `bash scripts/gate.sh`
- `bash scripts/gate.sh secureops/app/remediation/templates.py`

I also tried `pytest secureops/tests`; it is blocked by unrelated existing collection errors: missing `fastapi` and missing `app.github.comments`. No commit was made.