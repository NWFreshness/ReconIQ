from __future__ import annotations

from core.models import AnalysisRequest
from core import services


def test_run_analysis_uses_coordinator_and_report_writer(monkeypatch, tmp_path):
    calls = {}

    def fake_run_all(target_url, llm_complete, enabled_modules, progress_callback=None, max_pages=5, max_depth=2):
        calls["target_url"] = target_url
        calls["enabled_modules"] = enabled_modules
        calls["max_pages"] = max_pages
        calls["max_depth"] = max_depth
        calls["llm_result"] = llm_complete("prompt", module="company_profile")
        if progress_callback:
            progress_callback("done", 100.0)
        return {"metadata": {"target_url": target_url}, "company_profile": {"company_name": "Example"}}

    def fake_write_report(results, output_dir, fmt="md"):
        calls["output_dir"] = output_dir
        assert results["metadata"]["target_url"] == "https://example.com"
        return str(tmp_path / "report.md")

    def fake_complete(**kwargs):
        calls["provider_override"] = kwargs["provider_override"]
        calls["model_override"] = kwargs["model_override"]
        return "llm ok"

    progress = []
    monkeypatch.setattr(services, "run_all", fake_run_all)
    monkeypatch.setattr(services, "write_report", fake_write_report)
    monkeypatch.setattr(services, "llm_complete", fake_complete)

    result = services.run_analysis(
        AnalysisRequest(
            target_url="https://example.com",
            provider_override="openai",
            model_override="gpt-4o-mini",
            output_dir="reports",
        ),
        progress_callback=lambda msg, pct: progress.append((msg, pct)),
    )

    assert result.report_path.endswith("report.md")
    assert result.results["company_profile"]["company_name"] == "Example"
    assert calls["target_url"] == "https://example.com"
    assert calls["enabled_modules"]["company_profile"] is True
    assert calls["provider_override"] == "openai"
    assert calls["model_override"] == "gpt-4o-mini"
    assert calls["output_dir"] == "reports"
    assert progress == [("done", 100.0)]
