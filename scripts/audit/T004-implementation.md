Implemented T004 by adding package marker files:

- `secureops/app/__init__.py`
- `secureops/app/api/__init__.py`
- `secureops/app/db/__init__.py`
- `secureops/app/engine/__init__.py`
- `secureops/app/engine/rules/__init__.py`
- `secureops/app/github/__init__.py`
- `secureops/app/models/__init__.py`
- `secureops/app/remediation/__init__.py`

Verification:
- `python3 -m py_compile secureops/app/__init__.py` passed
- `bash scripts/gate.sh secureops/app/__init__.py` passed
- `bash scripts/gate.sh` passed

Note: the literal `python -m py_compile ...` command could not run because this container does not have a `python` executable, only `python3`. No commit was made.