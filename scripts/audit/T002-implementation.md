Implemented T002 by adding [secureops/pyproject.toml](/workspaces/sec-project/secureops/pyproject.toml:1) with Python `>=3.12` project metadata, setuptools build config, runtime dependencies for FastAPI/Pydantic/PostgreSQL/SQLAlchemy/Alembic/Tree-sitter/Ollama/GitHub integration, and dev extras for pytest/ruff.

Verification:
- `npx --yes @taplo/cli@latest check secureops/pyproject.toml` passed.
- `bash scripts/gate.sh secureops/pyproject.toml` could not run because `scripts/gate.sh` does not exist in this repo.

No commit was made.