from __future__ import annotations

from pathlib import Path

from report import writer


def _results(**overrides) -> dict:
    base = {
        "metadata": {
            "target_url": "https://acme.example",
            "timestamp": "2026-04-30 12:00:00",
            "modules_run": ["company_profile", "seo_keywords", "swot"],
            "modules_skipped": ["social_content"],
            "modules_failed": ["competitor"],
            "data_limitations": ["profile caveat", "seo caveat"],
        },
        "company_profile": {
            "company_name": "Acme Widgets",
            "what_they_do": "Builds widgets.",
            "target_audience": "Local businesses",
            "value_proposition": "Durable widgets.",
            "brand_voice": "Professional",
            "primary_cta": "Request a quote",
            "services_products": ["Custom widgets"],
            "marketing_channels": ["website"],
            "data_confidence": "high",
            "data_limitations": ["profile caveat"],
        },
        "seo_keywords": {
            "top_keywords": ["widgets", "custom widgets"],
            "content_gaps": ["comparison pages"],
            "seo_weaknesses": ["thin pages"],
            "quick_wins": ["add local pages"],
            "estimated_traffic_tier": "low",
            "local_seo_signals": "weak",
            "data_confidence": "low",
            "data_limitations": ["seo caveat"],
        },
        "competitor": {"error": "competitor boom"},
        "social_content": {"error": "social boom"},
        "swot": {
            "swot": {
                "strengths": ["clear niche", "strong local presence"],
                "weaknesses": ["thin content"],
                "opportunities": ["local SEO"],
                "threats": ["larger competitors"],
            },
            "acquisition_angle": "Lead with local SEO audit.",
            "talking_points": ["Your service pages could capture more intent."],
            "recommended_next_steps": ["Build a local landing page plan."],
            "competitive_advantage": "Focused local agency.",
            "data_confidence": "medium",
            "data_limitations": ["strategy inferred"],
        },
    }
    base.update(overrides)
    return base


def test_write_report_creates_file_in_configured_directory(tmp_path):
    report_path = writer.write_report(_results(), output_dir=str(tmp_path))

    assert Path(report_path).exists()
    assert Path(report_path).parent.parent == tmp_path


def test_slugifies_company_name_safely(tmp_path):
    results = _results()
    results["company_profile"]["company_name"] = "Acme & Co. (Widgets!)"

    report_path = writer.write_report(results, output_dir=str(tmp_path))

    slug = Path(report_path).parent.name
    assert slug == "acme-co-widgets"


def test_includes_target_url_timestamp_and_module_status(tmp_path):
    report_path = writer.write_report(_results(), output_dir=str(tmp_path))
    content = Path(report_path).read_text(encoding="utf-8")

    assert "**Target URL:** https://acme.example" in content
    assert "**Generated:** 2026-04-30 12:00:00" in content
    assert "company_profile" in content
    assert "social_content" in content
    assert "competitor" in content


def test_renders_competitor_list_cleanly(tmp_path):
    results = _results()
    results["competitor"] = {
        "competitors": [
            {
                "name": "WidgetCo",
                "url": "https://widgetco.example",
                "positioning": "Premium regional.",
                "estimated_pricing_tier": "premium",
                "key_messaging": "Widgets that scale.",
                "weaknesses": ["generic messaging"],
                "inferred_services": ["consulting"],
            }
        ],
        "data_confidence": "low",
        "data_limitations": ["inferred"],
    }

    report_path = writer.write_report(results, output_dir=str(tmp_path))
    content = Path(report_path).read_text(encoding="utf-8")

    assert "### 1. WidgetCo" in content
    assert "Premium regional." in content
    assert "generic messaging" in content


def test_renders_swot_without_broken_markdown_tables(tmp_path):
    report_path = writer.write_report(_results(), output_dir=str(tmp_path))
    content = Path(report_path).read_text(encoding="utf-8")

    swot_start = content.index("## 5. SWOT Analysis")
    swot_end = content.index("## 6. Client Acquisition Strategy")
    swot_section = content[swot_start:swot_end]

    assert "|" in swot_section
    lines = [line for line in swot_section.splitlines() if "|" in line]
    for line in lines:
        parts = line.split("|")
        assert len(parts) == 5, f"Broken table row: {line}"


def test_handles_missing_module_data_gracefully(tmp_path):
    results = _results()
    del results["seo_keywords"]
    del results["swot"]

    report_path = writer.write_report(results, output_dir=str(tmp_path))
    content = Path(report_path).read_text(encoding="utf-8")

    assert "## 2. SEO & Keyword Analysis" in content
    assert "## 5. SWOT Analysis" in content


def test_includes_data_confidence_and_limitations(tmp_path):
    report_path = writer.write_report(_results(), output_dir=str(tmp_path))
    content = Path(report_path).read_text(encoding="utf-8")

    assert "high" in content
    assert "profile caveat" in content
    assert "seo caveat" in content


def test_does_not_crash_when_company_name_is_missing(tmp_path):
    results = _results()
    del results["company_profile"]["company_name"]

    report_path = writer.write_report(results, output_dir=str(tmp_path))
    content = Path(report_path).read_text(encoding="utf-8")

    assert "Unknown Company" in content


def test_does_not_crash_when_company_name_is_not_a_string(tmp_path):
    results = _results()
    results["company_profile"]["company_name"] = 12345

    report_path = writer.write_report(results, output_dir=str(tmp_path))
    content = Path(report_path).read_text(encoding="utf-8")

    assert "12345" in content
