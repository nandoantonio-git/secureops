Implemented [001_initial_secureops_schema.py](/workspaces/sec-project/secureops/app/db/migrations/versions/001_initial_secureops_schema.py) with the initial Alembic schema for all current ORM entities, including foreign keys, cascade deletes, unique constraints, JSON fields, enum columns, and indexes.

Verification:
- `bash scripts/gate.sh secureops/app/db/migrations/versions/001_initial_secureops_schema.py` passed
- `python3 -m py_compile secureops/app/db/migrations/versions/001_initial_secureops_schema.py` passed
- `bash scripts/gate.sh` passed

Note: the literal `python -m py_compile ...` command could not run because this container has no `python` executable on PATH; the project gate uses `python3`, which passed. No commit was made.