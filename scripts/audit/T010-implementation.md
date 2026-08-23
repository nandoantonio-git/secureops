Implemented PostgreSQL connection/session setup in [connection.py](/workspaces/sec-project/secureops/app/db/connection.py:1).

Added:
- SQLAlchemy `engine` using configured `settings.database_url`
- `SessionLocal` session factory
- Declarative `Base`
- `get_db_session` / `get_db` generator dependency

Verification:
- `python3 -m py_compile secureops/app/db/connection.py` passed
- `bash scripts/gate.sh secureops/app/db/connection.py` passed
- `bash scripts/gate.sh` passed

Note: `python -m py_compile ...` could not run because `python` is not installed in this container; the available interpreter is `python3`, which the gate script also uses.