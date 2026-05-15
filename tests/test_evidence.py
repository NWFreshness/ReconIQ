from __future__ import annotations

from research import company_profile
from research.evidence import collect_scrape_evidence
from scraper.models import LinkData, PageData, ScrapeResult, SocialLink
from tests.test_research_modules import COMPANY_PROFILE_RESULT, RecordingLLM


def _scrape_result() -> ScrapeResult:
    return ScrapeResult(
        url="https://acme.example",
        title="Acme Widgets | Custom Widget Builder",
        meta_description="Acme builds durable custom widgets for local businesses.",
        meta_keywords=["custom widgets", "widget maintenance"],
        headings={"h1": ["Custom Widgets for Local Businesses"], "h2": ["Request a Quote"]},
        internal_links=[LinkData(href="https://acme.example/services", text="Services")],
        external_links=[LinkData(href="https://partner.example", text="Partner")],
        social_links=[SocialLink(platform="linkedin", url="https://linkedin.com/company/acme")],
        phone_numbers=["360-555-1212"],
        emails=["sales@acme.example"],
        body_text="Acme builds custom widgets, repairs widgets, and serves local businesses.",
        pages=[
            PageData(
                url="https://acme.example/services",
                title="Services | Acme Widgets",
                text="Widget repair, widget maintenance, and custom fabrication.",
                headings={"h1": ["Widget Services"]},
            )
        ],
        raw_html_length=1234,
        crawl_duration_s=0.25,
    )


def test_collect_scrape_evidence_preserves_source_fields():
    evidence = collect_scrape_evidence(_scrape_result(), module="company_profile")

    assert evidence
    first = evidence[0]
    assert first["module"] == "company_profile"
    assert first["source_type"] == "scrape"
    assert first["url"] == "https://acme.example"
    assert first["page_title"] == "Acme Widgets | Custom Widget Builder"
    assert first["selector_or_field"] == "title"
    assert first["confidence"] == "high"
    assert "Acme Widgets" in first["excerpt"]


def test_collect_scrape_evidence_includes_subpage_and_social_evidence():
    evidence = collect_scrape_evidence(_scrape_result(), module="social_content")
    fields = {item["selector_or_field"] for item in evidence}
    urls = {item["url"] for item in evidence}

    assert "social_links.linkedin" in fields
    assert "page.text" in fields
    assert "https://acme.example/services" in urls


def test_company_profile_attaches_evidence_when_structured_scrape_is_available():
    llm = RecordingLLM(COMPANY_PROFILE_RESULT)

    result = company_profile.run("https://acme.example", llm, scrape_result=_scrape_result())

    assert "evidence" in result
    assert result["evidence"][0]["module"] == "company_profile"
    assert any(item["selector_or_field"] == "meta_description" for item in result["evidence"])
