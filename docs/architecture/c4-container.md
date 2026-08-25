# C4 — Containers

The deployable units — matches `docker-compose.yml` and
`.github/workflows/secureops-gate.yml` exactly; nothing here is aspirational.
See [c4-context.md](c4-context.md) for the system boundary these sit inside.

```mermaid
C4Container
    title SecureOps — Containers

    Person(reviewer, "Developer / Reviewer")

    Container_Boundary(secureops, "SecureOps") {
        Container(api, "SecureOps API", "FastAPI / Python 3.12, secureops/Dockerfile", "Scans changed files synchronously; builds findings, remediation, and gate decisions; publishes to GitHub")
        Container(dashboard, "Dashboard", "React 19 + Vite, served by nginx, frontend/Dockerfile", "Read-only analytics: severity distribution, weekly trend, top critical files, filterable findings list with inline overrides")
    }

    ContainerDb_Ext(postgres, "PostgreSQL 16", "Analyses, findings, remediations, detection signals, override history")
    Container_Ext(ollama, "Ollama", "Local model runtime (e.g. codellama)")
    System_Ext(github, "GitHub", "PR trigger, comments, commit status")

    Rel(reviewer, dashboard, "Views findings, filters, overrides status", "HTTPS")
    Rel(reviewer, github, "Reads PR comment + check status")
    Rel(dashboard, api, "GET /dashboard/*, POST /findings/{id}/override", "JSON/HTTPS, CORS-restricted to DASHBOARD_FRONTEND_ORIGIN")
    Rel(github, api, "pull_request → POST /analyses (via the gate workflow)", "JSON/HTTPS")
    Rel(api, github, "PR comment + commit status (best-effort)", "GitHub API")
    Rel(api, postgres, "Best-effort read/write", "SQL, SQLAlchemy")
    Rel(api, ollama, "Remediation + severity suggestion (falls back to templates)", "HTTP, /api/generate")
```

## Inside the API container

Not separate deployables — Python packages under `secureops/app/`, listed
here because the boundaries matter more than the container count:

| Package | Responsibility |
| --- | --- |
| `app/api/` | HTTP boundary: `/analyses`, `/findings`, `/dashboard`, gate decisions |
| `app/engine/` | Tree-sitter parsing, deterministic rules, taint analysis, fingerprinting |
| `app/remediation/` | Ollama client (remediation text + severity suggestion) with reviewed-template/deterministic fallback |
| `app/github/` | PR comment formatting + redaction, commit status payloads, the one place that calls the GitHub API (`publisher.py`) |
| `app/models/`, `app/db/` | SQLAlchemy models and Alembic migrations |

This split is the one enforced by `.specify/memory/constitution.md`: the
engine and remediation packages never import `app.github` or `app.api`
directly, so a finding's cause/evidence/impact is fully computed before
anything decides whether or how to publish it.
