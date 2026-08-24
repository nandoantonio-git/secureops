Implemented T052.

Changes:
- Added detection signal creation in [scan.py](/workspaces/sec-project/secureops/app/engine/scan.py:310):
  - deterministic rule signals
  - data-flow signals for taint findings
  - reviewed template match signals
  - non-deterministic AI-assisted classification signals for non-taint rule findings
- Updated [analyses.py](/workspaces/sec-project/secureops/app/api/analyses.py:247) to serialize the scan-created `DetectionSignal` objects instead of fabricating signal dictionaries.

Verification passed:
- `python -m py_compile secureops/app/engine/scan.py`
- `bash scripts/gate.sh secureops/app/engine/scan.py`
- `bash scripts/gate.sh secureops/app/engine/scan.py secureops/app/api/analyses.py`
- `bash scripts/gate.sh`
- `pytest -q` → `38 passed`

No commit was made.