Implemented T034 in [findings.py](/workspaces/sec-project/secureops/app/api/findings.py:19).

Changes:
- Added contract-aligned paths: `/analyses/{analysisId}/findings` and `/findings/{findingId}`.
- Added `Finding` response models and operation IDs: `listFindings`, `getFinding`.
- Added path aliases so internals stay snake_case.
- Split finding detail lookup into `find_finding_by_id`.

Verification passed:
- `python -m py_compile secureops/app/api/findings.py`
- `bash scripts/gate.sh secureops/app/api/findings.py`
- `bash scripts/gate.sh`
- `PYTHONPATH=secureops pytest secureops/tests/integration/test_analysis_feedback_flow.py -q`
- Runtime probe confirmed `GET /findings/{findingId}` returns `200` and OpenAPI exposes the expected operation IDs.