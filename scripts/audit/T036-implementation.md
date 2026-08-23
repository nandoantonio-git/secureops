Implemented T036 in [analyses.py](/workspaces/sec-project/secureops/app/api/analyses.py:14).

What changed:
- Integrated PR feedback formatting via `format_pr_feedback` during `create_analysis`.
- Persisted generated PR feedback in the existing in-memory analysis store.
- Added `get_pr_feedback_for_analysis()` plus a hidden `/analyses/{analysisId}/pr-feedback` helper endpoint.
- Normalized serialized enum values for stored findings/remediation/signals.

Verification passed:
- `python -m py_compile secureops/app/api/analyses.py`
- `pytest secureops/tests/integration/test_analysis_feedback_flow.py`
- `pytest secureops/tests/validation/test_advisory_python_feedback.py`
- `bash scripts/gate.sh secureops/app/api/analyses.py`
- `bash scripts/gate.sh`
- `pytest secureops/tests` -> 20 passed

No commit was made.