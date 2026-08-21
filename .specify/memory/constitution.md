<!--
Sync Impact Report
Version change: 2.0.0 -> 2.1.0
Modified principles:
- I. Actionable Feedback Before Broad Coverage -> unchanged
- II. Automatic Blocking Is Earned, Not Default -> unchanged
- III. Two Languages With Explicitly Unequal Coverage -> unchanged
- Added IV. Academic Traceability Without Product Distortion
- Added V. AI Components Are Never an Isolated Critical Dependency
Added sections:
- Quality Gate Requirements
Removed sections: None
Follow-up TODOs: None
-->
# SecureOps Constitution

## Core Principles

### I. Actionable Feedback Before Broad Coverage
SecureOps MUST optimize every delivered SAST finding for practical usefulness before expanding
pattern coverage. Every finding shown to a reviewer MUST include the suspected cause, concrete
evidence from the analyzed code, security impact, and a recommended correction with a safe example
or clearly described safe pattern. A feature MUST NOT increase the volume of findings by weakening
explanation quality, evidence quality, or reviewer actionability.

Coverage breadth is subordinate to finding reliability. New rules, model-assisted explanations, and
UI changes MUST be evaluated by whether a student or reviewer can understand why the finding exists
and what change would reduce risk.

Rationale: SecureOps is PR-first security feedback. A smaller set of trusted, teachable findings is
more valuable for review and defense than a larger set of vague alerts.

### II. Automatic Blocking Is Earned, Not Default
SecureOps MUST launch merge-blocking behavior in consultative mode. Automated merge blocking MAY
only be enabled for a narrow, validated subset of critical findings with measured false-positive
behavior and deterministic evidence. A blocking decision MUST NOT rely on isolated AI judgment,
unverified natural-language reasoning, or a rule whose false-positive rate has not been reviewed.

Any expansion of blocking scope MUST document the finding class, validation evidence, measured or
observed false-positive rate, and rollback path to consultative-only behavior. Non-critical,
experimental, or AI-assisted findings MUST remain advisory until they satisfy the blocking criteria.

Rationale: Blocking a PR is a high-trust action. SecureOps must earn that privilege through evidence
and controlled scope rather than treating all alerts as equally authoritative.

### III. Two Languages With Explicitly Unequal Coverage
SecureOps MUST support Python as the primary analysis language with complete MVP coverage, including
AST-based parsing and data-flow tracking for supported vulnerability patterns. SecureOps MUST also
support one secondary language with minimal but real analysis coverage. The secondary language MAY
have fewer rules, simpler flow reasoning, and narrower explanations, but its limitations MUST be
visible in documentation, specs, and demonstrations.

This unequal coverage is a permanent MVP scope decision, not a hidden defect. Features, reports,
and checkpoint materials MUST NOT imply parity between Python and the secondary language unless
that parity has actually been implemented and validated.

Rationale: The project team must deliver reliable depth in the primary language while still proving
multi-language extensibility within academic time constraints.

### IV. Academic Traceability Without Product Distortion
Every relevant architecture decision MUST be documentable and linkable to FIAP evaluation criteria,
including architecture, SAST robustness, AI innovation, DevSecOps practice, and technical defense.
Specs, reports, and checkpoint materials MUST preserve traceability from product decisions to these
criteria without changing the product into a checklist for the evaluation board.

The developer user experience MUST NOT be sacrificed to make the project appear broader, more
complex, or more complete for academic presentation. Features that improve checkpoint optics but
make findings harder to act on, PR flow harder to use, or system behavior harder to explain MUST be
rejected or redesigned.

Rationale: SecureOps must satisfy academic assessment while remaining a coherent PR-first security
product that a developer would actually use.

### V. AI Components Are Never an Isolated Critical Dependency
Any AI capability, including severity classification, remediation suggestions, summarization,
fine-tuning, or explanation enhancement, MUST have a deterministic or template-based fallback. The
system MUST remain functional, testable, and demonstrable if the local Ollama component fails,
times out, returns low-confidence output, or is unavailable.

AI output MUST augment evidence produced by deterministic analysis rather than replace required
facts such as source location, vulnerable pattern, data-flow evidence, or blocking eligibility.
When AI confidence or availability is insufficient, SecureOps MUST degrade to advisory deterministic
feedback instead of failing the PR workflow or fabricating unsupported explanations.

Rationale: Local AI is an innovation component, not the single point of truth. The platform must be
robust enough for real review and reliable enough for checkpoint demonstration without depending on
one model call succeeding.

## Operational Constraints

SecureOps is a Python/FastAPI/PostgreSQL platform for PR-first static application security testing.
The analysis engine MUST use AST parsing as its foundation for supported rules. Python analysis MUST
include data-flow tracking for the vulnerability classes claimed by the MVP. The AI module MUST run
locally via Ollama; required tests, demos, and validation gates MUST NOT depend on paid APIs or
externally hosted model services.

The product is developed as a FIAP Engenharia de Software Projeto Integrador by a group of four to
five contributors. Until a formal code-owner hierarchy exists, ownership and review responsibility
MUST be shared by the group and documented per checkpoint or feature. Architectural choices MUST fit
student delivery constraints: clear modules, reproducible local setup, and behavior that can be
explained during technical defense.

Security claims MUST be backed by implementation evidence, tests, fixtures, or documented manual
validation. Findings that depend on local AI output MUST be reproducible enough for checkpoint
demonstration and MUST fail safely into advisory feedback when confidence or required evidence is
insufficient.

## Academic Delivery and Quality Gates

Work MUST stay aligned with FIAP checkpoint delivery: CP1, CP2, CP3, and the final technical
defense. Each checkpoint plan MUST identify the PR-first user flow being demonstrated, the supported
language scope, the finding classes in scope, and the validation evidence that proves the checkpoint
claim.

Every feature specification and implementation plan MUST state whether the change affects finding
generation, explanation content, blocking behavior, AI assistance, data persistence, or PR workflow
integration. Changes that affect finding generation MUST include representative vulnerable and safe
fixtures. Changes that affect blocking behavior MUST include explicit false-positive reasoning and
MUST default to consultative behavior unless Principle II criteria are satisfied.

The minimum validation gate for ordinary changes is the smallest reproducible local command set that
exercises the affected FastAPI, database, AST-analysis, and AI-adapter behavior. Tests MAY use local
Ollama mocks, fixtures, or deterministic adapters, but MUST NOT require a paid API. If a change
cannot be fully verified locally, the blocker and safest manual verification path MUST be documented
before checkpoint or defense use.

## Quality Gate Requirements

Changes to the analysis engine, supported rules, AST parsing, or taint analysis MUST include a test
or controlled fixture demonstrating the expected behavior before the change is considered complete.
The test MUST show the relevant vulnerable case and, when practical, a safe or non-vulnerable case
that guards against obvious false positives.

Changes to merge-blocking behavior MUST be validated against the controlled corpus of known
vulnerabilities before merge. The validation evidence MUST identify which findings would block,
which would remain advisory, and whether the result is consistent with the false-positive discipline
required by Principle II.

Quality gates MUST be local and reproducible by the group. Paid APIs, unavailable hosted services,
or one-off manual inspection MUST NOT be the only evidence for completing analysis-engine,
taint-analysis, or blocking changes.

## Governance

This constitution supersedes conflicting project conventions for Spec Kit planning, feature scope,
review, and checkpoint claims. README files, technical reports, feature specs, and defense materials
provide operational detail, but they MUST be interpreted in a way that satisfies these principles.

Amendments MUST update this file, include a Sync Impact Report, and explain the semantic version
change. Versioning follows semantic versioning: MAJOR for incompatible governance or principle
redefinitions, MINOR for added principles or materially expanded guidance, and PATCH for wording,
clarifications, or non-semantic corrections.

Compliance MUST be reviewed during feature planning, before checkpoint submission, and before the
technical defense. Reviewers MUST reject or defer changes that increase finding volume without
usable explanations, introduce blocking without measured justification, imply equal language
coverage without implementation evidence, require paid APIs for required validation, cannot survive
AI component failure, lack required analysis or taint-analysis tests, or cannot be explained by the
group during defense. Exceptions require an explicit written rationale in the feature spec,
checkpoint material, or technical report and MUST include a path back to compliance.

**Version**: 2.1.0 | **Ratified**: 2026-08-20 | **Last Amended**: 2026-08-20
