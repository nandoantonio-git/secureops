# Implementation Plan: SecureOps PR Vulnerability Feedback

**Branch**: `001-secureops-pr-feedback` | **Date**: 2026-08-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-secureops-pr-feedback/spec.md`

## Summary

Build SecureOps as a PR-first security feedback platform. The critical MVP flow is: Pull Request opened → GitHub Actions dispatches analysis → the SecureOps engine scans changed code → findings are generated → each finding receives structured severity/remediation feedback → a PR comment/status is published → the result remains advisory by default or blocks only when a restricted deterministic critical-finding criterion is met.

Python is the primary analysis language and receives the full MVP depth: AST-based parsing, deterministic rules, and supported data-flow tracking from untrusted inputs to sensitive sinks. A second language is mandatory, but intentionally narrower: deterministic minimum coverage with documented limitations and fixtures, without complete taint analysis or parity claims.

FastAPI provides the service boundary, PostgreSQL persists analyses/findings/status history, Tree-sitter provides parsing foundations, and a local Ollama component augments severity/remediation explanations. The MVP must remain functional when Ollama is unavailable by using reviewed remediation templates and deterministic fallback. LoRA/QLoRA fine-tuning is a stretch goal only, not a required architecture dependency.

## Technical Context

**Language/Version**: Python 3.12 for the SecureOps service and analysis engine; JavaScript/TypeScript is the recommended secondary language for minimum deterministic coverage because it is common in PR workflows and well supported by Tree-sitter.

**Primary Dependencies**: FastAPI, Pydantic, PostgreSQL, SQLAlchemy or equivalent thin persistence layer, Alembic or equivalent migrations, Tree-sitter grammars for Python and the secondary language, Ollama local runtime, GitHub Actions, pytest.

**Storage**: PostgreSQL stores Pull Request analyses, findings, remediation recommendations, detection signals, finding history, language coverage profiles, and validation scenarios.

**Testing**: pytest for unit/integration tests; controlled vulnerable and safe fixtures for Python and the secondary language; API contract validation for FastAPI; GitHub Actions dry-run or fixture-based PR workflow validation; Ollama adapter tests using mocks/fallbacks.

**Target Platform**: Local reproducible development environment plus GitHub Pull Request workflow. Containerization is acceptable for reproducibility, but the MVP must not depend on hosted paid APIs.

**Project Type**: Python web API + static analysis engine + CI/PR integration.

**Performance Goals**: Controlled PR fixture scans complete quickly enough to be usable during review. The MVP optimizes correctness, actionability, and reproducibility over large-repository throughput. Large repository scale and async queues are future work.

**Constraints**: Advisory mode by default; automatic blocking only for critical findings validated by multiple deterministic signals; IA never sole blocking authority; Ollama must have deterministic/template fallback; fine-tuning optional; no Redis/Celery queue dependency, dashboard-as-core, RBAC/full audit log, or DAST in this phase.

**Scale/Scope**: MVP validation set includes clean and vulnerable PR scenarios, Python deep coverage, one secondary-language deterministic pattern, an unprotected known critical case, and clean-code non-blocking cases.

## FIAP Evaluation Traceability Notes

These notes map evaluation expectations to existing product decisions and evidence without changing the PR-first SecureOps scope into a checklist-driven demo.

- **Architecture**: FastAPI, PostgreSQL, parser/engine/remediation/GitHub modules, and explicit API contracts show a service-oriented architecture with clear boundaries, durable state, and reproducible local operation.
- **SAST robustness**: Python deep coverage, AST parsing, deterministic rules, supported taint/data-flow tracking, secondary-language minimum coverage, detection signals, and vulnerable/clean fixtures demonstrate controlled static-analysis depth and known limitations.
- **AI innovation**: Local Ollama-assisted severity/remediation contextualization, reviewed templates, deterministic fallback, and optional fine-tuning research demonstrate AI use while preserving reliability when AI output is unavailable or low confidence.
- **DevSecOps**: GitHub Actions dispatch, PR comments/status publishing, advisory-first behavior, restricted critical gate decisions, and `scripts/gate.sh` validation show integration into the pull request workflow.
- **Defense evidence**: `research.md`, `data-model.md`, `contracts/openapi.yaml`, `quickstart.md`, validation fixtures, clean-code non-blocking checks, critical-case blocking checks, and manual override history provide traceable artifacts for checkpoint review and technical defense.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Actionable Feedback Before Broad Coverage

PASS. The plan prioritizes structured PR feedback over broad finding volume. Each finding must include cause, code evidence, impact, recommended correction, and a safe example. Rule expansion is constrained by actionability and fixture-backed validation.

### II. Automatic Blocking Is Earned, Not Default

PASS. The plan preserves advisory mode as the default. Automatic blocking is restricted to a narrow subset of critical findings validated by multiple deterministic signals. IA-assisted severity or explanation cannot independently block a PR.

### III. Two Languages With Explicitly Unequal Coverage

PASS. Python is explicitly the primary language with complete MVP depth, including AST parsing and supported data-flow tracking. The secondary language is mandatory but limited to real deterministic coverage with visible limitations and no parity claim.

### IV. Academic Traceability Without Product Distortion

PASS. The plan keeps the product PR-first while preserving FIAP-relevant evidence: two-language support, SAST robustness, AI innovation through local Ollama/fallback, DevSecOps via GitHub Actions/gates, and defense-ready validation artifacts. Dashboard/core-scope inflation is excluded.

### V. AI Components Are Never an Isolated Critical Dependency

PASS. Ollama is an enhancement layer for severity/remediation, not a single point of truth. Reviewed templates and deterministic fallback keep the PR workflow functional, testable, and demonstrable when the local AI component fails or returns low-confidence output.

### Academic Delivery and Quality Gates

PASS. The plan identifies the PR-first flow, language scope, finding classes, fixture requirements, affected state transitions, validation boundaries, security implications, and reproducible local verification expectations.

## Project Structure

### Documentation (this feature)

```text
specs/001-secureops-pr-feedback/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── openapi.yaml
├── checklists/
│   └── requirements.md
└── spec.md
```

### Source Code (repository root)

```text
secureops/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── analyses.py
│   │   ├── findings.py
│   │   └── gate.py
│   ├── models/
│   │   ├── analysis.py
│   │   ├── finding.py
│   │   └── remediation.py
│   ├── db/
│   │   ├── connection.py
│   │   └── migrations/
│   ├── engine/
│   │   ├── parser.py
│   │   ├── scan.py
│   │   ├── taint.py
│   │   └── rules/
│   │       ├── python.py
│   │       └── secondary.py
│   ├── remediation/
│   │   ├── templates.py
│   │   ├── ollama_client.py
│   │   └── fallback.py
│   └── github/
│       ├── comments.py
│       └── status.py
├── tests/
│   ├── fixtures/
│   │   ├── python_clean/
│   │   ├── python_vulnerable/
│   │   ├── secondary_clean/
│   │   └── secondary_vulnerable/
│   ├── unit/
│   ├── integration/
│   └── validation/
├── pyproject.toml
└── README.md
```

**Structure Decision**: Use a compact Python service under `secureops/` with explicit modules for API, engine, remediation, GitHub integration, and tests. Avoid premature Clean Architecture, broad abstractions, Redis/Celery, dashboard-first modules, RBAC/full audit infrastructure, and DAST components in this phase.

## Complexity Tracking

No constitution violations are present. No exception or complexity waiver is required.

## Phase 0: Research Summary

See [research.md](./research.md). Decisions resolve the technology and scope choices needed for implementation planning: Python primary depth, secondary deterministic support, Tree-sitter parsing, FastAPI boundary, PostgreSQL persistence, Ollama with fallback, advisory-first blocking, and explicit future exclusions.

## Phase 1: Design Summary

See [data-model.md](./data-model.md), [contracts/openapi.yaml](./contracts/openapi.yaml), and [quickstart.md](./quickstart.md). The design defines durable analysis/finding states, manual override history, deterministic blocking evidence, remediation recommendation structure, API contracts, and reproducible validation scenarios.

## Post-Design Constitution Check

### I. Actionable Feedback Before Broad Coverage

PASS. Design artifacts require structured remediation fields on every published finding and fixture-backed rules before expansion.

### II. Automatic Blocking Is Earned, Not Default

PASS. The data model and API contract separate advisory outcomes from blocking decisions. Blocking requires critical severity plus multiple deterministic detection signals and excludes IA-only decisions.

### III. Two Languages With Explicitly Unequal Coverage

PASS. The data model includes language coverage profiles with one primary deep profile and one secondary minimal deterministic profile. Quickstart scenarios validate both without implying parity.

### IV. Academic Traceability Without Product Distortion

PASS. Quickstart evidence maps to the project evaluation needs while preserving the developer PR feedback workflow as the product core.

### V. AI Components Are Never an Isolated Critical Dependency

PASS. Remediation recommendation design includes `reviewed_template`, `ollama_contextualized`, and `deterministic_fallback` sources. Quickstart explicitly validates Ollama-unavailable behavior.

### Academic Delivery and Quality Gates

PASS. Quickstart defines local reproducible validation for fixtures, clean-code non-blocking, critical-case blocking, structured feedback completeness, and manual override history.

No violations are recorded. No blocking constitution issue remains before `/speckit-tasks`.
