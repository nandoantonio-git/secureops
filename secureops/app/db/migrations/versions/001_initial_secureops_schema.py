"""Initial SecureOps schema.

Revision ID: 001
Revises:
Create Date: 2026-08-22 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


analysis_trigger = sa.Enum(
    "pull_request",
    "manual_validation",
    name="analysistrigger",
    native_enum=False,
)
gate_mode = sa.Enum(
    "advisory",
    "blocking_enabled",
    name="gatemode",
    native_enum=False,
)
analysis_status = sa.Enum(
    "requested",
    "running",
    "completed",
    "failed",
    name="analysisstatus",
    native_enum=False,
)
gate_decision_status = sa.Enum(
    "advisory_only",
    "passed",
    "blocked",
    name="gatedecisionstatus",
    native_enum=False,
)
language_coverage_role = sa.Enum(
    "primary",
    "secondary",
    name="languagecoveragerole",
    native_enum=False,
)
language_coverage_level = sa.Enum(
    "deep",
    "minimal_deterministic",
    name="languagecoveragelevel",
    native_enum=False,
)
validation_case_type = sa.Enum(
    "clean",
    "valid_finding",
    "critical_unprotected",
    "false_positive_guard",
    "ollama_unavailable",
    name="validationcasetype",
    native_enum=False,
)
expected_blocking_outcome = sa.Enum(
    "not_blocked",
    "blocked",
    name="expectedblockingoutcome",
    native_enum=False,
)
severity = sa.Enum(
    "critical",
    "high",
    "medium",
    "low",
    "info",
    name="severity",
    native_enum=False,
)
finding_status = sa.Enum(
    "open",
    "in_investigation",
    "resolved",
    "false_positive",
    "accepted_risk",
    name="findingstatus",
    native_enum=False,
)
finding_source = sa.Enum(
    "primary_language_rule",
    "primary_language_taint",
    "secondary_language_rule",
    "validation_fixture",
    name="findingsource",
    native_enum=False,
)
signal_type = sa.Enum(
    "deterministic_rule",
    "data_flow",
    "template_match",
    "ai_assisted_classification",
    name="signaltype",
    native_enum=False,
)
finding_change_type = sa.Enum(
    "status_change",
    "severity_override",
    "risk_acceptance",
    "reopen",
    name="findingchangetype",
    native_enum=False,
)
recommendation_source = sa.Enum(
    "reviewed_template",
    "ollama_contextualized",
    "deterministic_fallback",
    name="recommendationsource",
    native_enum=False,
)
recommendation_confidence = sa.Enum(
    "high",
    "medium",
    "low",
    name="recommendationconfidence",
    native_enum=False,
)


def upgrade() -> None:
    """Apply schema changes."""
    op.create_table(
        "language_coverage_profiles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("language", sa.String(length=64), nullable=False),
        sa.Column("role", language_coverage_role, nullable=False),
        sa.Column("coverage_level", language_coverage_level, nullable=False),
        sa.Column("supports_data_flow", sa.Boolean(), nullable=False),
        sa.Column("supported_rule_ids", sa.JSON(), nullable=False),
        sa.Column("limitations", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("language"),
    )
    op.create_table(
        "pull_request_analyses",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("repository", sa.String(length=255), nullable=False),
        sa.Column("pull_request_number", sa.Integer(), nullable=True),
        sa.Column("commit_sha", sa.String(length=128), nullable=False),
        sa.Column("trigger", analysis_trigger, nullable=False),
        sa.Column("mode", gate_mode, nullable=False),
        sa.Column("status", analysis_status, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_pull_request_analyses_commit_sha"),
        "pull_request_analyses",
        ["commit_sha"],
        unique=False,
    )
    op.create_index(
        op.f("ix_pull_request_analyses_repository"),
        "pull_request_analyses",
        ["repository"],
        unique=False,
    )
    op.create_table(
        "validation_scenarios",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("language", sa.String(length=64), nullable=False),
        sa.Column("case_type", validation_case_type, nullable=False),
        sa.Column("expected_findings", sa.JSON(), nullable=False),
        sa.Column(
            "expected_blocking_outcome",
            expected_blocking_outcome,
            nullable=False,
        ),
        sa.Column("reviewer_usefulness_rating", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "findings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("repository", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("line_start", sa.Integer(), nullable=False),
        sa.Column("line_end", sa.Integer(), nullable=True),
        sa.Column("language", sa.String(length=64), nullable=False),
        sa.Column("rule_id", sa.String(length=128), nullable=False),
        sa.Column("category", sa.String(length=128), nullable=False),
        sa.Column("severity", severity, nullable=False),
        sa.Column("status", finding_status, nullable=False),
        sa.Column("source", finding_source, nullable=False),
        sa.Column("fingerprint", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_id"],
            ["pull_request_analyses.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_findings_analysis_id"),
        "findings",
        ["analysis_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_findings_fingerprint"),
        "findings",
        ["fingerprint"],
        unique=False,
    )
    op.create_index(
        op.f("ix_findings_repository"),
        "findings",
        ["repository"],
        unique=False,
    )
    op.create_index(
        op.f("ix_findings_rule_id"),
        "findings",
        ["rule_id"],
        unique=False,
    )
    op.create_table(
        "gate_decisions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("mode", gate_mode, nullable=False),
        sa.Column("decision", gate_decision_status, nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("blocking_finding_ids", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_id"],
            ["pull_request_analyses.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_gate_decisions_analysis_id"),
        "gate_decisions",
        ["analysis_id"],
        unique=False,
    )
    op.create_table(
        "language_coverage_results",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("language", sa.String(length=64), nullable=False),
        sa.Column("files_seen", sa.Integer(), nullable=False),
        sa.Column("files_analyzed", sa.Integer(), nullable=False),
        sa.Column("rules_applied", sa.Integer(), nullable=False),
        sa.Column("limitations", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_id"],
            ["pull_request_analyses.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_language_coverage_results_analysis_id"),
        "language_coverage_results",
        ["analysis_id"],
        unique=False,
    )
    op.create_table(
        "detection_signals",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("finding_id", sa.String(length=36), nullable=False),
        sa.Column("signal_type", signal_type, nullable=False),
        sa.Column("deterministic", sa.Boolean(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["finding_id"],
            ["findings.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_detection_signals_finding_id"),
        "detection_signals",
        ["finding_id"],
        unique=False,
    )
    op.create_table(
        "finding_history_entries",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("finding_id", sa.String(length=36), nullable=False),
        sa.Column("changed_by", sa.String(length=255), nullable=False),
        sa.Column("change_type", finding_change_type, nullable=False),
        sa.Column("from_value", sa.String(length=255), nullable=True),
        sa.Column("to_value", sa.String(length=255), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["finding_id"],
            ["findings.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_finding_history_entries_finding_id"),
        "finding_history_entries",
        ["finding_id"],
        unique=False,
    )
    op.create_table(
        "remediation_recommendations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("finding_id", sa.String(length=36), nullable=False),
        sa.Column("cause", sa.Text(), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("impact", sa.Text(), nullable=False),
        sa.Column("recommended_correction", sa.Text(), nullable=False),
        sa.Column("safe_example", sa.Text(), nullable=False),
        sa.Column("generation_source", recommendation_source, nullable=False),
        sa.Column("template_id", sa.String(length=128), nullable=True),
        sa.Column("confidence", recommendation_confidence, nullable=False),
        sa.ForeignKeyConstraint(
            ["finding_id"],
            ["findings.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_remediation_recommendations_finding_id"),
        "remediation_recommendations",
        ["finding_id"],
        unique=True,
    )


def downgrade() -> None:
    """Revert schema changes."""
    op.drop_index(
        op.f("ix_remediation_recommendations_finding_id"),
        table_name="remediation_recommendations",
    )
    op.drop_table("remediation_recommendations")
    op.drop_index(
        op.f("ix_finding_history_entries_finding_id"),
        table_name="finding_history_entries",
    )
    op.drop_table("finding_history_entries")
    op.drop_index(
        op.f("ix_detection_signals_finding_id"),
        table_name="detection_signals",
    )
    op.drop_table("detection_signals")
    op.drop_index(
        op.f("ix_language_coverage_results_analysis_id"),
        table_name="language_coverage_results",
    )
    op.drop_table("language_coverage_results")
    op.drop_index(
        op.f("ix_gate_decisions_analysis_id"),
        table_name="gate_decisions",
    )
    op.drop_table("gate_decisions")
    op.drop_index(op.f("ix_findings_rule_id"), table_name="findings")
    op.drop_index(op.f("ix_findings_repository"), table_name="findings")
    op.drop_index(op.f("ix_findings_fingerprint"), table_name="findings")
    op.drop_index(op.f("ix_findings_analysis_id"), table_name="findings")
    op.drop_table("findings")
    op.drop_table("validation_scenarios")
    op.drop_index(
        op.f("ix_pull_request_analyses_repository"),
        table_name="pull_request_analyses",
    )
    op.drop_index(
        op.f("ix_pull_request_analyses_commit_sha"),
        table_name="pull_request_analyses",
    )
    op.drop_table("pull_request_analyses")
    op.drop_table("language_coverage_profiles")
