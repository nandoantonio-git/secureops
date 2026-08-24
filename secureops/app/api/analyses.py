"""Analysis creation and retrieval endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Path
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.schemas import CreateAnalysisRequest, GateDecision, PullRequestAnalysis
from app.config import get_settings
from app.db.connection import SessionLocal
from app.engine.parser import UnsupportedLanguageError, normalize_language
from app.engine.scan import orchestrate_scan
from app.github.comments import format_pr_feedback
from app.models import analysis as _analysis_models
from app.models import finding as _finding_models
from app.models import remediation as _remediation_models
from app.models.analysis import (
    GateDecision as GateDecisionModel,
    LanguageCoverageProfile as LanguageCoverageProfileModel,
    LanguageCoverageResult as LanguageCoverageResultModel,
    PullRequestAnalysis as PullRequestAnalysisModel,
)
from app.models.enums import (
    AnalysisStatus,
    AnalysisTrigger,
    GateDecisionStatus,
    GateMode,
    LanguageCoverageLevel,
    LanguageCoverageRole,
)
from app.remediation.service import build_remediation_recommendation

del _analysis_models, _finding_models, _remediation_models


router = APIRouter(tags=["analyses"])
AnalysisId = Annotated[str, Path(alias="analysisId")]

_ANALYSES: dict[str, dict[str, Any]] = {}
_FINDINGS_BY_ANALYSIS: dict[str, list[dict[str, Any]]] = {}
_PR_FEEDBACK_BY_ANALYSIS: dict[str, str] = {}

_PYTHON_RULE_IDS = [
    "python.subprocess.shell_true",
    "python.os.system",
    "python.yaml.unsafe_load",
    "python.sql.tainted_execute",
]
_JAVASCRIPT_RULE_IDS = ["javascript.dom.inner_html"]
_LANGUAGE_COVERAGE_PROFILES = {
    "python": {
        "language": "python",
        "role": "primary",
        "coverage_level": "deep",
        "supports_data_flow": True,
        "supported_rule_ids": _PYTHON_RULE_IDS,
        "limitations": [],
    },
    "javascript": {
        "language": "javascript",
        "role": "secondary",
        "coverage_level": "minimal_deterministic",
        "supports_data_flow": False,
        "supported_rule_ids": _JAVASCRIPT_RULE_IDS,
        "limitations": [
            "No data-flow tracking for JavaScript in this MVP.",
            "JavaScript coverage is not parity with Python data-flow analysis.",
        ],
    },
}


@router.post(
    "/analyses",
    status_code=202,
    response_model=PullRequestAnalysis,
    operation_id="createAnalysis",
)
def create_analysis(request: CreateAnalysisRequest) -> dict[str, Any]:
    """Create an analysis and synchronously scan the supplied changed files."""

    analysis_id = str(uuid4())
    now = _utc_now()
    scan_result = orchestrate_scan(
        analysis_id=analysis_id,
        repository=request.repository,
        changed_files=request.changed_files,
    )
    findings = [
        _serialize_scanned_finding(scanned_finding)
        for scanned_finding in scan_result.scanned_findings
    ]
    from app.api.findings import apply_existing_manual_overrides

    findings = apply_existing_manual_overrides(findings)
    coverage_profiles = _coverage_profiles(request.changed_files)
    coverage_results = _coverage_results(
        request.changed_files,
        skipped_paths={
            skipped_file.path for skipped_file in scan_result.skipped_files
        },
    )
    analysis = {
        "id": analysis_id,
        "repository": request.repository,
        "pull_request_number": request.pull_request_number,
        "commit_sha": request.commit_sha,
        "trigger": request.trigger,
        "mode": request.mode,
        "status": AnalysisStatus.COMPLETED,
        "findings_count": len(findings),
        "failure_reason": None,
        "started_at": now,
        "completed_at": _utc_now(),
        "language_coverage_profiles": coverage_profiles,
        "language_coverage_results": coverage_results,
    }
    gate_decision = _build_gate_decision(
        analysis_id=analysis_id,
        mode=request.mode,
        findings=findings,
    )

    _ANALYSES[analysis_id] = analysis
    _FINDINGS_BY_ANALYSIS[analysis_id] = findings
    _PR_FEEDBACK_BY_ANALYSIS[analysis_id] = format_pr_feedback(
        findings=findings,
        mode=request.mode,
        language_coverage_profiles=coverage_profiles,
        language_coverage_results=coverage_results,
    )
    _persist_analysis_snapshot(analysis, coverage_results, gate_decision)
    return analysis


@router.get(
    "/analyses/{analysisId}",
    response_model=PullRequestAnalysis,
    operation_id="getAnalysis",
)
def get_analysis(analysis_id: AnalysisId) -> dict[str, Any]:
    """Return a previously created cached or persisted analysis."""

    from app.api.errors import ResourceNotFoundError

    try:
        return _ANALYSES[analysis_id]
    except KeyError as exc:
        persisted_analysis = _load_persisted_analysis(analysis_id)
        if persisted_analysis is None:
            raise ResourceNotFoundError("Analysis was not found.") from exc
        return persisted_analysis


@router.get(
    "/analyses/{analysisId}/gate-decision",
    response_model=GateDecision,
    operation_id="getGateDecision",
)
def get_gate_decision(analysis_id: AnalysisId) -> dict[str, Any]:
    """Return the current gate decision for a cached or persisted analysis."""

    from app.api.errors import ResourceNotFoundError

    try:
        analysis = _ANALYSES[analysis_id]
    except KeyError as exc:
        gate_decision = _load_or_build_persisted_gate_decision(analysis_id)
        if gate_decision is None:
            raise ResourceNotFoundError("Analysis was not found.") from exc
        return gate_decision

    gate_decision = _build_gate_decision(
        analysis_id=analysis_id,
        mode=analysis["mode"],
        findings=_FINDINGS_BY_ANALYSIS.get(analysis_id, []),
    )
    _persist_gate_decision_snapshot(gate_decision)
    return gate_decision


def list_findings_for_analysis(analysis_id: str) -> list[dict[str, Any]]:
    """Return stored findings for an analysis or raise not found."""

    from app.api.errors import ResourceNotFoundError

    if analysis_id not in _ANALYSES:
        raise ResourceNotFoundError("Analysis was not found.")
    return _FINDINGS_BY_ANALYSIS.get(analysis_id, [])


def get_pr_feedback_for_analysis(analysis_id: str) -> str:
    """Return the generated PR feedback comment for an analysis."""

    from app.api.errors import ResourceNotFoundError

    if analysis_id not in _ANALYSES:
        raise ResourceNotFoundError("Analysis was not found.")
    return _PR_FEEDBACK_BY_ANALYSIS.get(
        analysis_id,
        format_pr_feedback(
            findings=_FINDINGS_BY_ANALYSIS.get(analysis_id, []),
            mode=_ANALYSES[analysis_id]["mode"],
            language_coverage_profiles=_ANALYSES[analysis_id].get(
                "language_coverage_profiles",
                [],
            ),
            language_coverage_results=_ANALYSES[analysis_id].get(
                "language_coverage_results",
                [],
            ),
        ),
    )


@router.get("/analyses/{analysisId}/pr-feedback", include_in_schema=False)
def get_analysis_pr_feedback(analysis_id: AnalysisId) -> dict[str, str]:
    """Return the generated Markdown feedback that would be posted to the PR."""

    return {
        "analysis_id": analysis_id,
        "comment": get_pr_feedback_for_analysis(analysis_id),
    }


def _serialize_scanned_finding(scanned_finding: Any) -> dict[str, Any]:
    finding = scanned_finding.finding
    finding.id = str(uuid4())
    recommendation = build_remediation_recommendation(
        finding=finding,
        evidence=scanned_finding.evidence,
        sink=scanned_finding.sink,
        user_input=scanned_finding.user_input,
        settings=get_settings(),
    )
    return {
        "id": finding.id,
        "analysis_id": finding.analysis_id,
        "file_path": finding.file_path,
        "line_start": finding.line_start,
        "line_end": finding.line_end,
        "language": finding.language,
        "rule_id": finding.rule_id,
        "category": finding.category,
        "severity": _api_value(finding.severity),
        "status": _api_value(finding.status),
        "source": _api_value(finding.source),
        "fingerprint": finding.fingerprint,
        "remediation": {
            "cause": recommendation.cause,
            "evidence": recommendation.evidence,
            "impact": recommendation.impact,
            "recommended_correction": recommendation.recommended_correction,
            "safe_example": recommendation.safe_example,
            "generation_source": _api_value(recommendation.generation_source),
            "template_id": recommendation.template_id,
            "confidence": _api_value(recommendation.confidence),
        },
        "detection_signals": _serialize_detection_signals(finding),
        "history": [],
    }


def _serialize_detection_signals(finding: Any) -> list[dict[str, Any]]:
    return [
        {
            "signal_type": _api_value(signal.signal_type),
            "deterministic": bool(signal.deterministic),
            "summary": signal.summary,
        }
        for signal in finding.detection_signals
    ]


def _api_value(value: Any) -> Any:
    """Return JSON-facing values for enums while preserving plain scalars."""

    return getattr(value, "value", value)


def _coverage_profiles(changed_files: list[Any]) -> list[dict[str, Any]]:
    profiles = []
    for language in _seen_supported_languages(changed_files):
        profiles.append(dict(_LANGUAGE_COVERAGE_PROFILES[language]))
    return profiles


def _coverage_results(
    changed_files: list[Any],
    *,
    skipped_paths: set[str],
) -> list[dict[str, Any]]:
    files_seen: dict[str, int] = {}
    files_analyzed: dict[str, int] = {}
    for changed_file in changed_files:
        language = _supported_language(getattr(changed_file, "language", ""))
        if language is None:
            continue

        files_seen[language] = files_seen.get(language, 0) + 1
        if getattr(changed_file, "path", "") not in skipped_paths:
            files_analyzed[language] = files_analyzed.get(language, 0) + 1

    results = []
    for language in files_seen:
        analyzed_count = files_analyzed.get(language, 0)
        profile = _LANGUAGE_COVERAGE_PROFILES[language]
        results.append(
            {
                "language": language,
                "files_seen": files_seen[language],
                "files_analyzed": analyzed_count,
                "rules_applied": (
                    len(profile["supported_rule_ids"]) if analyzed_count else 0
                ),
                "limitations": _coverage_result_limitations(language),
            },
        )
    return results


def _seen_supported_languages(changed_files: list[Any]) -> list[str]:
    languages = []
    for changed_file in changed_files:
        language = _supported_language(getattr(changed_file, "language", ""))
        if language is not None and language not in languages:
            languages.append(language)
    return languages


def _supported_language(language: str) -> str | None:
    try:
        normalized = normalize_language(language)
    except UnsupportedLanguageError:
        return None
    if normalized in _LANGUAGE_COVERAGE_PROFILES:
        return normalized
    return None


def _coverage_result_limitations(language: str) -> list[str]:
    if language == "javascript":
        return [
            "Minimal deterministic JavaScript coverage is active.",
            "No data-flow tracking is available for JavaScript.",
        ]
    return []


def _persist_analysis_snapshot(
    analysis: dict[str, Any],
    coverage_results: list[dict[str, Any]],
    gate_decision: dict[str, Any],
) -> None:
    """Persist analysis, coverage, and gate details when a database is available."""

    try:
        with SessionLocal() as session:
            _upsert_language_coverage_profiles(session)
            session.merge(_analysis_model_from_api(analysis))
            for coverage_result in coverage_results:
                _upsert_language_coverage_result(
                    session,
                    analysis_id=str(analysis["id"]),
                    coverage_result=coverage_result,
                )
            _upsert_gate_decision(session, gate_decision)
            session.commit()
    except SQLAlchemyError:
        return


def _persist_gate_decision_snapshot(gate_decision: dict[str, Any]) -> None:
    """Persist a gate decision when a database is available."""

    try:
        with SessionLocal() as session:
            _upsert_gate_decision(session, gate_decision)
            session.commit()
    except SQLAlchemyError:
        return


def _upsert_language_coverage_profiles(session: Session) -> None:
    for profile in _LANGUAGE_COVERAGE_PROFILES.values():
        existing_profile = session.scalar(
            select(LanguageCoverageProfileModel).where(
                LanguageCoverageProfileModel.language == profile["language"],
            ),
        )
        if existing_profile is None:
            session.add(_profile_model_from_api(profile))
            continue

        existing_profile.role = LanguageCoverageRole(str(profile["role"]))
        existing_profile.coverage_level = LanguageCoverageLevel(
            str(profile["coverage_level"]),
        )
        existing_profile.supports_data_flow = bool(profile["supports_data_flow"])
        existing_profile.supported_rule_ids = list(profile["supported_rule_ids"])
        existing_profile.limitations = list(profile["limitations"])


def _upsert_language_coverage_result(
    session: Session,
    *,
    analysis_id: str,
    coverage_result: dict[str, Any],
) -> None:
    language = str(coverage_result["language"])
    existing_result = session.scalar(
        select(LanguageCoverageResultModel).where(
            LanguageCoverageResultModel.analysis_id == analysis_id,
            LanguageCoverageResultModel.language == language,
        ),
    )
    if existing_result is None:
        session.add(
            LanguageCoverageResultModel(
                analysis_id=analysis_id,
                language=language,
                files_seen=int(coverage_result["files_seen"]),
                files_analyzed=int(coverage_result["files_analyzed"]),
                rules_applied=int(coverage_result["rules_applied"]),
                limitations=list(coverage_result["limitations"]),
            ),
        )
        return

    existing_result.files_seen = int(coverage_result["files_seen"])
    existing_result.files_analyzed = int(coverage_result["files_analyzed"])
    existing_result.rules_applied = int(coverage_result["rules_applied"])
    existing_result.limitations = list(coverage_result["limitations"])


def _upsert_gate_decision(
    session: Session,
    gate_decision: dict[str, Any],
) -> None:
    existing_decision = session.scalar(
        select(GateDecisionModel)
        .where(GateDecisionModel.analysis_id == str(gate_decision["analysis_id"]))
        .order_by(GateDecisionModel.created_at.desc()),
    )
    if existing_decision is None:
        session.add(_gate_decision_model_from_api(gate_decision))
        return

    existing_decision.mode = GateMode(str(_api_value(gate_decision["mode"])))
    existing_decision.decision = GateDecisionStatus(
        str(_api_value(gate_decision["decision"])),
    )
    existing_decision.reasons = list(gate_decision["reasons"])
    existing_decision.blocking_finding_ids = list(
        gate_decision["blocking_findings"],
    )


def _analysis_model_from_api(analysis: dict[str, Any]) -> PullRequestAnalysisModel:
    return PullRequestAnalysisModel(
        id=str(analysis["id"]),
        repository=str(analysis["repository"]),
        pull_request_number=analysis["pull_request_number"],
        commit_sha=str(analysis["commit_sha"]),
        trigger=AnalysisTrigger(str(_api_value(analysis["trigger"]))),
        mode=GateMode(str(_api_value(analysis["mode"]))),
        status=AnalysisStatus(str(_api_value(analysis["status"]))),
        started_at=analysis["started_at"],
        completed_at=analysis["completed_at"],
        failure_reason=analysis["failure_reason"],
    )


def _profile_model_from_api(
    profile: dict[str, Any],
) -> LanguageCoverageProfileModel:
    return LanguageCoverageProfileModel(
        language=str(profile["language"]),
        role=LanguageCoverageRole(str(profile["role"])),
        coverage_level=LanguageCoverageLevel(str(profile["coverage_level"])),
        supports_data_flow=bool(profile["supports_data_flow"]),
        supported_rule_ids=list(profile["supported_rule_ids"]),
        limitations=list(profile["limitations"]),
    )


def _gate_decision_model_from_api(
    gate_decision: dict[str, Any],
) -> GateDecisionModel:
    return GateDecisionModel(
        analysis_id=str(gate_decision["analysis_id"]),
        mode=GateMode(str(_api_value(gate_decision["mode"]))),
        decision=GateDecisionStatus(str(_api_value(gate_decision["decision"]))),
        reasons=list(gate_decision["reasons"]),
        blocking_finding_ids=list(gate_decision["blocking_findings"]),
    )


def _load_persisted_analysis(analysis_id: str) -> dict[str, Any] | None:
    try:
        with SessionLocal() as session:
            analysis = session.get(PullRequestAnalysisModel, analysis_id)
            if analysis is None:
                return None

            coverage_results = [
                _coverage_result_from_model(result)
                for result in analysis.language_coverage_results
            ]
            result_languages = {result["language"] for result in coverage_results}
            profiles = session.scalars(select(LanguageCoverageProfileModel)).all()
            coverage_profiles = [
                _profile_from_model(profile)
                for profile in profiles
                if not result_languages or profile.language in result_languages
            ]
            return {
                "id": analysis.id,
                "repository": analysis.repository,
                "pull_request_number": analysis.pull_request_number,
                "commit_sha": analysis.commit_sha,
                "trigger": analysis.trigger,
                "mode": analysis.mode,
                "status": analysis.status,
                "findings_count": len(analysis.findings),
                "failure_reason": analysis.failure_reason,
                "started_at": analysis.started_at,
                "completed_at": analysis.completed_at,
                "language_coverage_profiles": coverage_profiles,
                "language_coverage_results": coverage_results,
            }
    except SQLAlchemyError:
        return None


def _load_or_build_persisted_gate_decision(
    analysis_id: str,
) -> dict[str, Any] | None:
    try:
        with SessionLocal() as session:
            analysis = session.get(PullRequestAnalysisModel, analysis_id)
            if analysis is None:
                return None

            gate_decision = session.scalar(
                select(GateDecisionModel)
                .where(GateDecisionModel.analysis_id == analysis_id)
                .order_by(GateDecisionModel.created_at.desc()),
            )
            if gate_decision is not None:
                return _gate_decision_from_model(gate_decision)

            built_decision = _build_gate_decision(
                analysis_id=analysis_id,
                mode=analysis.mode,
                findings=list(analysis.findings),
            )
            _upsert_gate_decision(session, built_decision)
            session.commit()
            return built_decision
    except SQLAlchemyError:
        return None


def _profile_from_model(
    profile: LanguageCoverageProfileModel,
) -> dict[str, Any]:
    return {
        "language": profile.language,
        "role": _api_value(profile.role),
        "coverage_level": _api_value(profile.coverage_level),
        "supports_data_flow": profile.supports_data_flow,
        "supported_rule_ids": list(profile.supported_rule_ids),
        "limitations": list(profile.limitations),
    }


def _coverage_result_from_model(
    result: LanguageCoverageResultModel,
) -> dict[str, Any]:
    return {
        "language": result.language,
        "files_seen": result.files_seen,
        "files_analyzed": result.files_analyzed,
        "rules_applied": result.rules_applied,
        "limitations": list(result.limitations),
    }


def _gate_decision_from_model(
    gate_decision: GateDecisionModel,
) -> dict[str, Any]:
    return {
        "analysis_id": gate_decision.analysis_id,
        "mode": _api_value(gate_decision.mode),
        "decision": _api_value(gate_decision.decision),
        "reasons": list(gate_decision.reasons),
        "blocking_findings": list(gate_decision.blocking_finding_ids),
    }


def _build_gate_decision(
    *,
    analysis_id: str,
    mode: str | GateMode,
    findings: list[Any],
) -> dict[str, Any]:
    from app.api.gate import build_gate_decision

    return build_gate_decision(
        analysis_id=analysis_id,
        mode=mode,
        findings=findings,
    )


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


__all__ = ["get_pr_feedback_for_analysis", "list_findings_for_analysis", "router"]
