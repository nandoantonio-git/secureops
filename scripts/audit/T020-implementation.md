Implemented T020 by adding [test_remediation_templates.py](/workspaces/sec-project/secureops/tests/unit/test_remediation_templates.py:1).

Coverage added:
- Reviewed template selection for Python command injection.
- Context-adapted remediation output for Python shell execution.
- JavaScript DOM XSS template adaptation to safe DOM updates.
- No reviewed template returned for an unknown/non-security pattern.

Verification:
- `python -m py_compile secureops/tests/unit/test_remediation_templates.py` passed.
- `bash scripts/gate.sh secureops/tests/unit/test_remediation_templates.py` passed.
- `bash scripts/gate.sh` passed.
- TDD red check: `python -m pytest tests/unit/test_remediation_templates.py` fails as expected with `ModuleNotFoundError: No module named 'app.remediation.templates'`, because T029 has not implemented the template catalog yet.