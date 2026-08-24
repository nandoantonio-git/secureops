Implemented T042 and verified it.

Changes:
- Added Python taint analysis in [taint.py](/workspaces/sec-project/secureops/app/engine/taint.py:51) for request-derived input reaching SQL `execute`/`executemany`.
- Wired taint findings into Python scans in [scan.py](/workspaces/sec-project/secureops/app/engine/scan.py:249).
- Added data-flow detection signals plus language coverage response/feedback support in [analyses.py](/workspaces/sec-project/secureops/app/api/analyses.py:37), [schemas.py](/workspaces/sec-project/secureops/app/api/schemas.py:51), and [comments.py](/workspaces/sec-project/secureops/app/github/comments.py:48).

Verification passed:
- `python -m py_compile secureops/app/engine/taint.py`
- `PYTHONPATH=secureops pytest secureops/tests/unit/test_taint.py -q`
- `bash scripts/gate.sh secureops/app/engine/taint.py`
- `bash scripts/gate.sh`
- `PYTHONPATH=secureops pytest -q` → `27 passed`

No commit made. The workspace still has pre-existing script metadata changes and `.devcontainer/`; I left those alone.