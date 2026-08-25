# Repository Guidelines

## Project Structure & Module Organization

`secureops/` contains the Python 3.12 FastAPI service. Application code lives in `secureops/app/`, organized by API routes, database and Alembic migrations, analysis engine, GitHub integration, models, and remediation. Backend tests are grouped in `secureops/tests/{unit,integration,validation}`; reusable fixture notes belong in `tests/fixtures/`. The React 19/TypeScript dashboard is in `frontend/`, with UI components under `src/components/`, API clients under `src/api/`, hooks, utilities, and design tokens in their corresponding directories. Product specifications and contracts live in `specs/001-secureops-pr-feedback/`; task automation and audit records live in `scripts/`.

## Build, Test, and Development Commands

- `cd secureops && python -m pip install -e '.[dev]'` installs the backend and developer tools.
- `cd secureops && uvicorn app.main:app --reload` runs the API locally.
- `cd secureops && python -m pytest` runs all backend tests; pass a path such as `tests/unit` for a narrower run.
- `./scripts/gate.sh` compiles Python files and runs Ruff when available.
- `cd frontend && npm ci && npm run dev` installs locked dependencies and starts Vite.
- `cd frontend && npm run lint` runs Oxlint; `npm run build` type-checks and creates the production bundle.

## Coding Style & Naming Conventions

Use four spaces, type hints, and concise docstrings in Python. Keep modules and functions `snake_case`, classes `PascalCase`, and constants `UPPER_SNAKE_CASE`. Ruff is the backend lint authority. In TypeScript, follow the existing two-space style, use `PascalCase.tsx` for React components, `camelCase` for functions and hooks, and single-quoted imports. Keep API, engine, and persistence responsibilities in their existing packages.

## Testing Guidelines

Pytest discovers `test_*.py`, `Test*`, and `test_*` and enforces strict markers. Mark tests as `unit`, `integration`, or `validation` where appropriate. Add focused unit coverage for deterministic logic, integration coverage for API/database boundaries, and validation tests for end-to-end security scenarios. Run the relevant subset and the full suite before submitting.

## Commit & Pull Request Guidelines

Recent history uses Conventional Commit prefixes such as `feat:`, `chore:`, and `docs:`. Write imperative, scoped summaries and keep unrelated changes separate. Pull requests should explain behavior and security impact, link the relevant issue or spec task (for example `T034`), list verification commands, and include screenshots for dashboard changes. Call out schema, configuration, API-contract, or redaction changes explicitly; never commit credentials or local `.env` files.
