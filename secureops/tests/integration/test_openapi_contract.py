"""Contract checks for the foundational SecureOps OpenAPI surface."""

from __future__ import annotations

import ast
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = (
    PROJECT_ROOT / "specs/001-secureops-pr-feedback/contracts/openapi.yaml"
)
SCHEMAS_PATH = PROJECT_ROOT / "secureops/app/api/schemas.py"


def _contract_text() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8")


def _schema_source() -> str:
    return SCHEMAS_PATH.read_text(encoding="utf-8")


def _path_block(path: str) -> str:
    contract = _contract_text()
    start = contract.index(f"  {path}:")
    next_path = re.search(r"^  /", contract[start + 1 :], flags=re.MULTILINE)
    if next_path is None:
        return contract[start:]
    return contract[start : start + 1 + next_path.start()]


def _component_schema_block(schema_name: str) -> str:
    contract = _contract_text()
    start = contract.index(f"    {schema_name}:")
    next_schema = re.search(
        r"^    [A-Za-z][A-Za-z0-9]+:",
        contract[start + 1 :],
        flags=re.MULTILINE,
    )
    if next_schema is None:
        return contract[start:]
    return contract[start : start + 1 + next_schema.start()]


def _schema_fields(class_name: str) -> set[str]:
    tree = ast.parse(_schema_source())
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {
                child.target.id
                for child in node.body
                if isinstance(child, ast.AnnAssign)
                and isinstance(child.target, ast.Name)
            }
    raise AssertionError(f"{class_name} schema class not found")


def _assert_ref(block: str, schema_name: str) -> None:
    assert f"$ref: '#/components/schemas/{schema_name}'" in block


def _assert_required_fields(block: str, fields: tuple[str, ...]) -> None:
    for field in fields:
        assert f"        - {field}" in block or f"required: [{field}" in block


def test_create_analysis_contract_matches_request_and_response_schemas() -> None:
    path = _path_block("/analyses")
    request = _component_schema_block("CreateAnalysisRequest")
    changed_file = _component_schema_block("ChangedFile")

    assert "post:" in path
    assert "operationId: createAnalysis" in path
    assert "'202':" in path
    assert "'400':" in path
    _assert_ref(path, "CreateAnalysisRequest")
    _assert_ref(path, "PullRequestAnalysis")

    _assert_required_fields(
        request,
        ("repository", "commit_sha", "trigger", "mode", "changed_files"),
    )
    assert "enum: [pull_request, manual_validation]" in request
    assert "enum: [advisory, blocking_enabled]" in request
    assert "default: advisory" in request
    assert "minItems: 1" in request
    _assert_ref(request, "ChangedFile")
    assert "required: [path, language, content_ref]" in changed_file

    assert _schema_fields("CreateAnalysisRequest") == {
        "repository",
        "pull_request_number",
        "commit_sha",
        "trigger",
        "mode",
        "changed_files",
    }
    assert _schema_fields("ChangedFile") == {"path", "language", "content_ref"}


def test_finding_detail_contract_includes_evidence_remediation_and_history() -> None:
    path = _path_block("/findings/{findingId}")
    finding = _component_schema_block("Finding")
    remediation = _component_schema_block("RemediationRecommendation")
    signal = _component_schema_block("DetectionSignal")

    assert "get:" in path
    assert "operationId: getFinding" in path
    assert "$ref: '#/components/parameters/FindingId'" in path
    assert "'200':" in path
    assert "'404':" in path
    _assert_ref(path, "Finding")

    _assert_required_fields(
        finding,
        (
            "id",
            "analysis_id",
            "file_path",
            "line_start",
            "language",
            "rule_id",
            "severity",
            "status",
            "source",
            "remediation",
            "detection_signals",
        ),
    )
    assert "enum: [critical, high, medium, low, info]" in finding
    assert (
        "enum: [open, in_investigation, resolved, false_positive, accepted_risk]"
        in finding
    )
    assert "history:" in finding
    _assert_ref(finding, "RemediationRecommendation")
    _assert_ref(finding, "DetectionSignal")
    _assert_ref(finding, "FindingHistoryEntry")

    _assert_required_fields(
        remediation,
        (
            "cause",
            "evidence",
            "impact",
            "recommended_correction",
            "safe_example",
            "generation_source",
            "confidence",
        ),
    )
    assert "required: [signal_type, deterministic, summary]" in signal
    assert "enum: [deterministic_rule, data_flow, template_match" in signal

    assert _schema_fields("Finding") == {
        "id",
        "analysis_id",
        "file_path",
        "line_start",
        "line_end",
        "language",
        "rule_id",
        "category",
        "severity",
        "status",
        "source",
        "fingerprint",
        "remediation",
        "detection_signals",
        "history",
    }


def test_gate_decision_contract_supports_advisory_and_blocking_outcomes() -> None:
    path = _path_block("/analyses/{analysisId}/gate-decision")
    gate_decision = _component_schema_block("GateDecision")
    schemas = _schema_source()

    assert "get:" in path
    assert "operationId: getGateDecision" in path
    assert "$ref: '#/components/parameters/AnalysisId'" in path
    assert "'200':" in path
    assert "'404':" in path
    _assert_ref(path, "GateDecision")

    assert "required: [analysis_id, mode, decision, reasons]" in gate_decision
    assert "enum: [advisory, blocking_enabled]" in gate_decision
    assert "enum: [advisory_only, passed, blocked]" in gate_decision
    assert "blocking_findings:" in gate_decision

    assert _schema_fields("GateDecision") == {
        "analysis_id",
        "mode",
        "decision",
        "reasons",
        "blocking_findings",
    }
    assert 'AliasChoices("blocking_findings", "blocking_finding_ids")' in schemas
