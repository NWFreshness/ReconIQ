from __future__ import annotations

import json

from core.models import AnalysisRequest
from core import services
from research import company_profile, competitors, coordinator, seo_keywords, social_content
from scraper.models import LinkData, PageData, ScrapeResult, SocialLink
from scraper.scraper import ScrapeCache


def fake_scrape_result() -> ScrapeResult:
    return ScrapeResult(
        url="https://acme.example",
        title="Acme Pest Control",
        meta_description="AI-ready pest control services in Vancouver WA",
        meta_keywords=["pest control", "vancouver wa exterminator"],
        headings={"h1": ["Acme Pest Control"], "h2": ["Residential Pest Services"]},
        internal_links=[LinkData(href="https://acme.example/services", text="Services")],
        external_links=[LinkData(href="https://rival.example", text="Partner competitor")],
        social_links=[SocialLink(platform="linkedin", url="https://linkedin.com/company/acme")],
        phone_numbers=["360-555-0100"],
        emails=["hello@acme.example"],
        body_text="Homepage body about pest control and recurring service plans.",
        pages=[
            PageData(
                url="https://acme.example/services",
                title="Services",
                text="Rodent control, ant control, and commercial pest management.",
                headings={"h1": ["Services"], "h2": ["Commercial Pest Management"]},
            )
        ],
        raw_html_length=2048,
        crawl_duration_s=0.2,
    )


class RecordingLLM:
    def __init__(self, response: dict):
        self.response = response
        self.calls = []

    def __call__(self, prompt: str, module: str, system=None, max_tokens=2048, **kwargs):
        self.calls.append({"prompt": prompt, "module": module, "system": system, "kwargs": kwargs})
        return json.dumps(self.response)


COMPANY_RESPONSE = {
    "company_name": "Acme Pest Control",
    "what_they_do": "Provides pest control services.",
    "target_audience": "Homeowners and commercial property managers",
    "value_proposition": "Fast local pest removal",
    "brand_voice": "Professional",
    "primary_cta": "Request a quote",
    "services_products": ["Rodent control"],
    "marketing_channels": ["website"],
    "location_city": "Vancouver",
    "location_state": "WA",
    "location_zip": "98660",
    "service_area": ["Battle Ground", "Camas"],
    "data_confidence": "high",
    "data_limitations": [],
}

SEO_RESPONSE = {
    "top_keywords": ["pest control vancouver wa"],
    "content_gaps": ["pricing pages"],
    "seo_weaknesses": ["thin local pages"],
    "quick_wins": ["add service area pages"],
    "estimated_traffic_tier": "low",
    "local_seo_signals": "moderate",
    "data_confidence": "medium",
    "data_limitations": [],
}

COMPETITOR_RESPONSE = {
    "competitors": [
        {
            "name": "Rival Pest",
            "url": "https://rival.example",
            "positioning": "Local pest control rival.",
            "estimated_pricing_tier": "mid-market",
            "key_messaging": "Fast pest help",
            "weaknesses": ["Generic messaging"],
            "inferred_services": ["Ant control"],
        }
    ],
    "scraped_competitors": [
        {
            "name": "Rival Pest",
            "url": "https://rival.example",
            "positioning": "Observed external competitor candidate.",
            "estimated_pricing_tier": "mid-market",
            "key_messaging": "Observed from crawl/search context",
            "weaknesses": ["Unknown"],
            "inferred_services": ["Pest control"],
        }
    ],
    "inferred_competitors": [],
    "data_confidence": "medium",
    "data_limitations": [],
}

SOCIAL_RESPONSE = {
    "platforms": ["LinkedIn"],
    "verified_social_accounts": [{"platform": "linkedin", "url": "https://linkedin.com/company/acme"}],
    "inferred_platforms": [],
    "content_quality": "moderate",
    "content_frequency": "sporadic",
    "engagement_signals": "weak",
    "review_sites": ["Google"],
    "blog_or_resources": "no",
    "content_gaps": ["case studies"],
    "email_signals": "present",
    "data_confidence": "medium",
    "data_limitations": [],
}


def test_core_services_passes_crawler_settings_to_coordinator(monkeypatch, tmp_path):
    calls = {}

    def fake_run_all(target_url, llm_complete, enabled_modules, progress_callback=None, max_pages=5, max_depth=2):
        calls["max_pages"] = max_pages
        calls["max_depth"] = max_depth
        return {"metadata": {"target_url": target_url}, "company_profile": {"company_name": "Acme"}}

    monkeypatch.setattr(services, "run_all", fake_run_all)
    monkeypatch.setattr(services, "write_report", lambda results, output_dir, fmt="md": str(tmp_path / "report.md"))
    monkeypatch.setattr(services, "llm_complete", lambda **kwargs: "{}")

    services.run_analysis(AnalysisRequest(target_url="https://acme.example", max_pages=7, max_depth=3))

    assert calls == {"max_pages": 7, "max_depth": 3}


def test_scrape_cache_get_structured_uses_crawler_and_settings(monkeypatch):
    calls = []

    def fake_crawl_site(url, max_pages=5, max_depth=2, timeout=15, progress_callback=None):
        calls.append((url, max_pages, max_depth, timeout))
        return fake_scrape_result()

    monkeypatch.setattr("scraper.crawler.crawl_site", fake_crawl_site)
    cache = ScrapeCache()

    first = cache.get_structured("acme.example", max_pages=2, max_depth=1)
    second = cache.get_structured("https://acme.example", max_pages=2, max_depth=1)
    third = cache.get_structured("https://acme.example", max_pages=4, max_depth=1)

    assert first is second
    assert third is not first
    assert calls == [
        ("https://acme.example", 2, 1, 15),
        ("https://acme.example", 4, 1, 15),
    ]


def test_coordinator_passes_shared_scrape_result_to_modules(monkeypatch):
    scrape_result = fake_scrape_result()
    seen = {}

    monkeypatch.setattr(
        "scraper.scraper.ScrapeCache.get_structured",
        lambda self, url, timeout=15, max_pages=5, max_depth=2, progress_callback=None: scrape_result,
    )

    def fake_profile(target_url, llm_complete, scraped_content=None, scrape_result=None):
        seen["profile"] = scrape_result
        return {"company_name": "Acme", "data_limitations": []}

    def fake_downstream(name):
        def _run(company_profile, target_url, llm_complete, scrape_result=None):
            seen[name] = scrape_result
            return {"data_limitations": []}
        return _run

    monkeypatch.setattr(coordinator, "run_company_profile", fake_profile)
    monkeypatch.setattr(coordinator, "run_seo_keywords", fake_downstream("seo"))
    monkeypatch.setattr(coordinator, "run_competitors", fake_downstream("competitor"))
    monkeypatch.setattr(coordinator, "run_social_content", fake_downstream("social"))
    monkeypatch.setattr(coordinator, "run_swot", lambda **kwargs: {"data_limitations": []})

    results = coordinator.run_all("https://acme.example", lambda *a, **k: "ok", {
        "company_profile": True,
        "seo_keywords": True,
        "competitor": True,
        "social_content": True,
        "swot": True,
    }, max_pages=2, max_depth=1)

    assert seen == {"profile": scrape_result, "seo": scrape_result, "competitor": scrape_result, "social": scrape_result}
    assert results["metadata"]["crawl"]["pages_crawled"] == 1
    assert results["metadata"]["crawl"]["max_pages"] == 2
    assert results["metadata"]["crawl"]["max_depth"] == 1


def test_research_prompts_include_structured_scrape_context(monkeypatch):
    scrape_result = fake_scrape_result()

    company_llm = RecordingLLM(COMPANY_RESPONSE)
    company_profile.run("https://acme.example", company_llm, scrape_result=scrape_result)
    assert "Acme Pest Control" in company_llm.calls[0]["prompt"]
    assert "360-555-0100" in company_llm.calls[0]["prompt"]
    assert "Commercial Pest Management" in company_llm.calls[0]["prompt"]

    seo_llm = RecordingLLM(SEO_RESPONSE)
    seo_keywords.run(COMPANY_RESPONSE, "https://acme.example", seo_llm, scrape_result=scrape_result)
    assert "vancouver wa exterminator" in seo_llm.calls[0]["prompt"]
    assert "Residential Pest Services" in seo_llm.calls[0]["prompt"]

    social_llm = RecordingLLM(SOCIAL_RESPONSE)
    social_content.run(COMPANY_RESPONSE, "https://acme.example", social_llm, scrape_result=scrape_result)
    assert "https://linkedin.com/company/acme" in social_llm.calls[0]["prompt"]

    competitor_llm = RecordingLLM(COMPETITOR_RESPONSE)
    competitors.run(
        COMPANY_RESPONSE,
        "https://acme.example",
        competitor_llm,
        scrape_result=scrape_result,
        search_discovery=lambda profile, url: {"results": [], "provider": "disabled", "query": "", "data_limitations": []},
    )
    assert "https://rival.example" in competitor_llm.calls[0]["prompt"]
