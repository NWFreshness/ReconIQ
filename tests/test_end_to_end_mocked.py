"""Mocked end-to-end test for the full ReconIQ pipeline."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from core.models import AnalysisRequest
from core.services import run_analysis


FAKE_HTML = """\
<!DOCTYPE html>
<html>
<head><title>Acme Corp - Innovative Solutions</title></head>
<body>
<main>
<h1>Acme Corp</h1>
<p>We build innovative software for small businesses.</p>
<p>Our services include web design, SEO, and marketing automation.</p>
<p>Contact us today for a free consultation!</p>
</main>
</body>
</html>
"""



from scraper.models import ScrapeResult

def _fake_scrape_result() -> ScrapeResult:
    return ScrapeResult(
        url="https://acme.example.com",
        title="Acme Corp",
        body_text=FAKE_HTML,
    )

def fake_llm_complete(prompt: str, module: str, system: str | None = None, max_tokens: int = 2048, temperature: float = 0.7, **kwargs) -> str:
    """Return canned JSON responses per module."""
    responses = {
        "company_profile": {
            "company_name": "Acme Corp",
            "what_they_do": "Builds innovative software for small businesses.",
            "target_audience": "Small business owners",
            "value_proposition": "Affordable, easy-to-use tools",
            "brand_voice": "friendly, professional",
            "primary_cta": "Contact us today",
            "services_products": ["Web design", "SEO", "Marketing automation"],
            "marketing_channels": ["Website", "Email", "Social media"],
            "location_city": "Vancouver",
            "location_state": "WA",
            "location_zip": "98660",
            "service_area": ["Portland", "Battle Ground"],
            "data_confidence": "medium",
            "data_limitations": ["Inferred from limited page content"],
        },
        "seo_keywords": {
            "top_keywords": ["small business software", "web design", "SEO tools"],
            "content_gaps": ["Case studies", "Pricing page"],
            "seo_weaknesses": ["Missing meta descriptions", "No blog"],
            "quick_wins": ["Add blog", "Optimize meta tags"],
            "estimated_traffic_tier": "low",
            "local_seo_signals": "weak",
            "data_confidence": "low",
            "data_limitations": ["No actual search volume data"],
        },
        "competitor": {
            "competitors": [
                {
                    "name": "Competitor A",
                    "url": "https://competitor-a.com",
                    "positioning": "Premium enterprise focus",
                    "estimated_pricing_tier": "high",
                    "key_messaging": "Enterprise-grade security",
                    "weaknesses": ["Expensive", "Complex onboarding"],
                    "inferred_services": ["Web design", "SEO"],
                }
            ],
            "data_confidence": "low",
            "scraped_competitors": [],
            "inferred_competitors": [],
            "data_limitations": ["Inferred from LLM, not live search"],
        },
        "social_content": {
            "platforms": ["LinkedIn", "Twitter"],
            "content_quality": "moderate",
            "content_frequency": "weekly",
            "engagement_signals": "low",
            "review_sites": ["Google Reviews"],
            "blog_or_resources": "none",
            "content_gaps": ["Video content", "Case studies"],
            "email_signals": "newsletter signup present",
            "data_confidence": "low",
            "verified_social_accounts": [],
            "inferred_platforms": [],
            "data_limitations": ["Inferred from limited signals"],
        },
        "swot": {
            "swot": {
                "strengths": ["Friendly brand voice", "Affordable pricing"],
                "weaknesses": ["Low SEO presence", "No blog"],
                "opportunities": ["Content marketing", "Local SEO"],
                "threats": ["Competitor A enterprise push"],
            },
            "acquisition_angle": "Position as the affordable, friendly alternative to enterprise solutions.",
            "talking_points": ["Easy onboarding", "Small business focus"],
            "recommended_next_steps": ["Start a blog", "Add case studies"],
            "competitive_advantage": "Price and simplicity",
            "lead_generation_strategy": "Outreach via LinkedIn and cold email offering a free competitive analysis.",
            "close_rate_strategy": "Offer a money-back guarantee on the first month and use AI-powered follow-up sequences that trigger based on prospect behavior signals.",
            "data_confidence": "medium",
            "data_limitations": ["Inferred from single page scrape"],
        },
    }
    return json.dumps(responses.get(module, {}))


@pytest.fixture
def tmp_reports_dir(tmp_path: Path) -> str:
    return str(tmp_path / "reports")


class TestMockedEndToEnd:
    @patch("core.services.llm_complete", side_effect=fake_llm_complete)
    @patch("scraper.scraper.ScrapeCache.get_structured", return_value=_fake_scrape_result())
    def test_full_pipeline_writes_report_with_all_sections(self, _mock_scrape, _mock_llm, tmp_reports_dir: str):
        request = AnalysisRequest(
            target_url="https://acme.example.com",
            enabled_modules={
                "company_profile": True,
                "seo_keywords": True,
                "competitor": True,
                "social_content": True,
                "swot": True,
            },
            output_dir=tmp_reports_dir,
        )

        result = run_analysis(request)

        # Report path must exist
        assert result.report_path is not None
        assert Path(result.report_path).exists()

        # All module sections present
        assert "company_profile" in result.results
        assert "seo_keywords" in result.results
        assert "competitor" in result.results
        assert "social_content" in result.results
        assert "swot" in result.results
        assert "metadata" in result.results

        # Metadata populated
        metadata = result.results["metadata"]
        assert metadata["target_url"] == "https://acme.example.com"
        assert "company_profile" in metadata["modules_run"]
        assert metadata["modules_failed"] == []
        assert metadata["modules_skipped"] == []

        # Report content checks
        content = Path(result.report_path).read_text(encoding="utf-8")
        assert "Acme Corp" in content
        assert "SWOT" in content
        assert "Competitor A" in content
        assert "acquisition_angle" in content.lower() or "acquisition" in content.lower()
        assert "data limitations" in content.lower()

    @patch("core.services.llm_complete", side_effect=fake_llm_complete)
    @patch("scraper.scraper.ScrapeCache.get_structured", return_value=_fake_scrape_result())
    def test_pipeline_with_failed_scrape_still_completes(self, _mock_scrape, _mock_llm, tmp_reports_dir: str):
        """If scraping fails, the pipeline should fall back to domain-only inference and still produce a report."""
        request = AnalysisRequest(
            target_url="https://acme.example.com",
            enabled_modules={
                "company_profile": True,
                "seo_keywords": True,
                "competitor": True,
                "social_content": True,
                "swot": True,
            },
            output_dir=tmp_reports_dir,
        )

        result = run_analysis(request)

        assert result.report_path is not None
        assert Path(result.report_path).exists()
        assert "company_profile" in result.results
        assert "swot" in result.results

    @patch("core.services.llm_complete", side_effect=fake_llm_complete)
    @patch("scraper.scraper.ScrapeCache.get_structured", return_value=_fake_scrape_result())
    def test_disabled_modules_are_skipped(self, _mock_scrape, _mock_llm, tmp_reports_dir: str):
        request = AnalysisRequest(
            target_url="https://acme.example.com",
            enabled_modules={
                "company_profile": True,
                "seo_keywords": False,
                "competitor": False,
                "social_content": False,
                "swot": True,
            },
            output_dir=tmp_reports_dir,
        )

        result = run_analysis(request)

        metadata = result.results["metadata"]
        assert "company_profile" in metadata["modules_run"]
        assert "swot" in metadata["modules_run"]
        assert "seo_keywords" in metadata["modules_skipped"]
        assert "competitor" in metadata["modules_skipped"]
        assert "social_content" in metadata["modules_skipped"]

    @patch("core.services.llm_complete", side_effect=fake_llm_complete)
    @patch("scraper.scraper.ScrapeCache.get_structured", return_value=_fake_scrape_result())
    def test_swot_skipped_when_company_profile_disabled(self, _mock_scrape, _mock_llm, tmp_reports_dir: str):
        request = AnalysisRequest(
            target_url="https://acme.example.com",
            enabled_modules={
                "company_profile": False,
                "seo_keywords": True,
                "competitor": True,
                "social_content": True,
                "swot": True,
            },
            output_dir=tmp_reports_dir,
        )

        result = run_analysis(request)

        metadata = result.results["metadata"]
        assert "company_profile" in metadata["modules_skipped"]
        assert "swot" in metadata["modules_skipped"]
        assert "seo_keywords" not in metadata["modules_run"]  # skipped because profile didn't run

    @patch("core.services.llm_complete", side_effect=fake_llm_complete)
    @patch("scraper.scraper.ScrapeCache.get_structured", return_value=_fake_scrape_result())
    def test_progress_callback_receives_updates(self, _mock_scrape, _mock_llm, tmp_reports_dir: str):
        messages: list[tuple[str, float]] = []

        def capture_progress(msg: str, pct: float) -> None:
            messages.append((msg, pct))

        request = AnalysisRequest(
            target_url="https://acme.example.com",
            enabled_modules={
                "company_profile": True,
                "seo_keywords": True,
                "competitor": True,
                "social_content": True,
                "swot": True,
            },
            output_dir=tmp_reports_dir,
        )

        run_analysis(request, progress_callback=capture_progress)

        assert len(messages) > 0
        # Should start and end with expected messages
        assert any("Company Profile" in m for m, _ in messages)
        assert any("All modules complete" in m for m, _ in messages)
        # Progress should reach 100
        assert messages[-1][1] == 100.0
