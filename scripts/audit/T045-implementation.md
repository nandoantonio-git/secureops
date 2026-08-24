Implemented T045.

Added language coverage persistence in [analyses.py](/workspaces/sec-project/secureops/app/api/analyses.py:356): analyses now persist coverage profile catalog rows and per-analysis coverage result rows when a DB is available, with persisted GET fallback. Added a per-analysis/language uniqueness constraint in [analysis.py](/workspaces/sec-project/secureops/app/models/analysis.py:164).

Verification passed:
- `python -m py_compile secureops/app/models/analysis.py`
- `python -m py_compile secureops/app/api/analyses.py`
- `PYTHONPATH=secureops pytest secureops/tests/integration/test_language_coverage.py -q`
- `bash scripts/gate.sh secureops/app/models/analysis.py`
- `bash scripts/gate.sh secureops/app/api/analyses.py`
- `bash scripts/gate.sh`
- `PYTHONPATH=secureops pytest secureops/tests -q` -> 27 passed
- Extra SQLite persistence smoke check passed

No commit made.