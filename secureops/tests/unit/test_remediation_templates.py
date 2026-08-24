"""Unit tests for reviewed remediation template selection."""

from app.models.enums import RecommendationConfidence, RecommendationSource
from app.remediation import templates
from app.remediation.templates import (
    RemediationTemplateContext,
    render_template,
    select_template,
)


def _field(value: object, name: str) -> object:
    """Read fields from either dataclass/model instances or dict payloads."""
    if isinstance(value, dict):
        return value[name]
    return getattr(value, name)


def test_selects_reviewed_python_command_injection_template() -> None:
    template = select_template(
        rule_id="python.subprocess.shell_true",
        category="CWE-78",
        language="python",
    )

    assert template is not None
    assert _field(template, "template_id") == "python-command-injection"
    assert _field(template, "language") == "python"
    assert "CWE-78" in _field(template, "categories")


def test_python_command_injection_template_adapts_to_finding_context() -> None:
    template = select_template(
        rule_id="python.subprocess.shell_true",
        category="CWE-78",
        language="python",
    )
    assert template is not None
    context = RemediationTemplateContext(
        file_path="app/images.py",
        line_start=7,
        language="python",
        evidence="subprocess.run(command, shell=True, check=True)",
        sink="subprocess.run",
        user_input="image_path",
    )

    recommendation = render_template(template, context)

    assert _field(recommendation, "generation_source") == (
        RecommendationSource.REVIEWED_TEMPLATE
    )
    assert _field(recommendation, "template_id") == "python-command-injection"
    assert _field(recommendation, "confidence") == RecommendationConfidence.HIGH
    assert "app/images.py:7" in _field(recommendation, "evidence")
    assert "subprocess.run(command, shell=True, check=True)" in _field(
        recommendation,
        "evidence",
    )
    assert "image_path" in _field(recommendation, "cause")
    assert "subprocess.run" in _field(recommendation, "recommended_correction")
    assert "shell=True" not in _field(recommendation, "safe_example")


def test_javascript_dom_xss_template_uses_safe_dom_update() -> None:
    template = select_template(
        rule_id="javascript.dom.inner_html",
        category="CWE-79",
        language="javascript",
    )
    assert template is not None
    context = RemediationTemplateContext(
        file_path="static/search.js",
        line_start=5,
        language="javascript",
        evidence="results.innerHTML = `<strong>${term}</strong>`;",
        sink="innerHTML",
        user_input="q",
    )

    recommendation = render_template(template, context)

    assert _field(template, "template_id") == "javascript-dom-xss"
    assert _field(recommendation, "generation_source") == (
        RecommendationSource.REVIEWED_TEMPLATE
    )
    assert "static/search.js:5" in _field(recommendation, "evidence")
    assert "innerHTML" in _field(recommendation, "evidence")
    assert "q" in _field(recommendation, "cause")
    assert "textContent" in _field(recommendation, "recommended_correction")
    assert "textContent" in _field(recommendation, "safe_example")


def test_all_deterministic_rule_ids_have_actionable_reviewed_templates() -> None:
    expected = {
        "python.subprocess.shell_true": ("CWE-78", "python", "subprocess.run"),
        "python.os.system": ("CWE-78", "python", "os.system"),
        "python.yaml.unsafe_load": ("CWE-502", "python", "yaml.load"),
        "javascript.dom.inner_html": ("CWE-79", "javascript", "innerHTML"),
        "javascript.dom.outer_html": ("CWE-79", "javascript", "outerHTML"),
        "javascript.dom.insert_adjacent_html": (
            "CWE-79",
            "javascript",
            "insertAdjacentHTML",
        ),
        "javascript.dom.document_write": (
            "CWE-79",
            "javascript",
            "document.write",
        ),
        "javascript.dom.document_writeln": (
            "CWE-79",
            "javascript",
            "document.writeln",
        ),
        "javascript.eval": ("CWE-95", "javascript", "eval"),
        "javascript.function_constructor": ("CWE-95", "javascript", "Function"),
        "javascript.timer.string_execution": (
            "CWE-95",
            "javascript",
            "setTimeout",
        ),
    }

    reviewed_rule_ids = {
        rule_id
        for template in templates.reviewed_templates()
        for rule_id in _field(template, "rule_ids")
    }
    assert set(expected) <= reviewed_rule_ids

    for rule_id, (category, language, sink) in expected.items():
        template = select_template(
            rule_id=rule_id,
            category=category,
            language=language,
        )
        assert template is not None
        recommendation = render_template(
            template,
            RemediationTemplateContext(
                file_path=(
                    "app/example.py"
                    if language == "python"
                    else "static/app.js"
                ),
                line_start=12,
                language=language,
                evidence=f"{sink}(user_input)",
                sink=sink,
                user_input="user_input",
            ),
        )

        assert _field(recommendation, "generation_source") == (
            RecommendationSource.REVIEWED_TEMPLATE
        )
        assert _field(recommendation, "confidence") == RecommendationConfidence.HIGH
        for field in (
            "cause",
            "evidence",
            "impact",
            "recommended_correction",
            "safe_example",
        ):
            value = _field(recommendation, field)
            assert isinstance(value, str)
            assert value.strip()


def test_unknown_pattern_has_no_reviewed_template() -> None:
    assert (
        select_template(
            rule_id="python.style.line_length",
            category=None,
            language="python",
        )
        is None
    )
