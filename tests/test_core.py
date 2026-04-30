from __future__ import annotations

from pathlib import Path

import yaml

from core.models import AnalysisRequest, AnalysisResult
from core.settings import load_config, resolve_env_values


def test_resolve_env_values_recurses_through_nested_config(monkeypatch):
    monkeypatch.setenv("RECONIQ_TEST_KEY", "secret-value")

    resolved = resolve_env_values(
        {
            "provider": {"api_key": "${RECONIQ_TEST_KEY}"},
            "items": ["${RECONIQ_TEST_KEY}", "plain"],
        }
    )

    assert resolved == {
        "provider": {"api_key": "secret-value"},
        "items": ["secret-value", "plain"],
    }


def test_load_config_reads_yaml_from_explicit_path(tmp_path: Path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump({"defaults": {"provider": "deepseek"}}),
        encoding="utf-8",
    )

    assert load_config(config_path)["defaults"]["provider"] == "deepseek"


def test_analysis_request_defaults_are_framework_neutral():
    request = AnalysisRequest(target_url="https://example.com")

    assert request.enabled_modules == {
        "company_profile": True,
        "seo_keywords": True,
        "competitor": True,
        "social_content": True,
        "swot": True,
    }
    assert request.provider_override is None
    assert request.model_override is None
    assert request.output_dir is None


def test_analysis_result_stores_results_and_report_path():
    result = AnalysisResult(results={"metadata": {"target_url": "https://example.com"}}, report_path="reports/example/report.md")

    assert result.results["metadata"]["target_url"] == "https://example.com"
    assert result.report_path == "reports/example/report.md"
