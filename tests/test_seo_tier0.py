"""SEO Tier 0: measured keyword seeds from scrape + data_mode labeling."""
from __future__ import annotations

import json

from research import seo_keywords
from research.seo_keywords import extract_keyword_seeds
from scraper.models import LinkData, PageData, ScrapeResult
from tests.test_research_modules import COMPANY_PROFILE_RESULT, RecordingLLM, SEO_RESULT


def _rich_scrape() -> ScrapeResult:
    return ScrapeResult(
        url="https://acme.example",
        title="Acme Widgets | Custom Widget Builder",
        meta_description="Durable custom widgets for local businesses.",
        meta_keywords=["custom widgets", "widget repair"],
        headings={
            "h1": ["Custom Widgets for Local Businesses"],
            "h2": ["Same-Day Widget Repair", "Free Estimates"],
        },
        internal_links=[
            LinkData(href="https://acme.example/services", text="Widget Services"),
            LinkData(href="https://acme.example/", text="Home"),
            LinkData(href="https://acme.example/contact", text="click here"),
            LinkData(href="https://acme.example/login", text="Login"),
            LinkData(href="https://acme.example/blog", text="Widget Maintenance Tips"),
        ],
        pages=[
            PageData(
                url="https://acme.example/services",
                title="Services | Acme Widgets",
                text="We repair and build widgets.",
                headings={"h1": ["Professional Widget Services"]},
            )
        ],
    )


def test_extract_keyword_seeds_pulls_title_h1_h2_meta_and_links():
    seeds = extract_keyword_seeds(_rich_scrape())
    by_source: dict[str, list[str]] = {}
    for item in seeds:
        by_source.setdefault(item["source"], []).append(item["keyword"])

    assert any("Acme Widgets" in k for k in by_source.get("title", []))
    assert "Custom Widgets for Local Businesses" in by_source.get("h1", [])
    assert "Same-Day Widget Repair" in by_source.get("h2", [])
    assert "custom widgets" in by_source.get("meta_keywords", [])
    assert "widget repair" in by_source.get("meta_keywords", [])
    assert "Widget Services" in by_source.get("internal_link", [])
    assert "Widget Maintenance Tips" in by_source.get("internal_link", [])
    assert any("Services" in k for k in by_source.get("subpage_title", []))
    assert "Professional Widget Services" in by_source.get("subpage_h1", [])
    # short meta description kept as a phrase
    assert any(
        "custom widgets" in k.lower() for k in by_source.get("meta_description", [])
    )


def test_extract_keyword_seeds_dedupes_and_filters_stopword_anchors():
    scrape = ScrapeResult(
        url="https://acme.example",
        title="Custom Widgets",
        meta_keywords=["Custom Widgets", "custom widgets"],  # case-insensitive dupe
        headings={"h1": ["Custom Widgets"], "h2": []},
        internal_links=[
            LinkData(href="/", text="Home"),
            LinkData(href="/contact", text="Contact"),
            LinkData(href="/login", text="Login"),
            LinkData(href="/x", text="click here"),
            LinkData(href="/ok", text="Industrial Widget Coatings"),
        ],
    )
    seeds = extract_keyword_seeds(scrape)
    keywords_lower = [s["keyword"].lower() for s in seeds]

    assert keywords_lower.count("custom widgets") == 1
    assert "home" not in keywords_lower
    assert "contact" not in keywords_lower
    assert "login" not in keywords_lower
    assert "click here" not in keywords_lower
    assert any("industrial widget coatings" == k for k in keywords_lower)
    assert len(seeds) <= 25


def test_extract_keyword_seeds_none_scrape_returns_empty():
    assert extract_keyword_seeds(None) == []


def test_seo_keywords_run_injects_hybrid_seeds_when_scrape_has_seeds():
    llm = RecordingLLM(SEO_RESULT)
    scrape = _rich_scrape()
    expected_seeds = extract_keyword_seeds(scrape)

    result = seo_keywords.run(
        COMPANY_PROFILE_RESULT,
        "https://acme.example",
        llm,
        scrape_result=scrape,
    )

    assert result["seed_keywords"] == expected_seeds
    assert result["data_mode"] == "hybrid"
    assert any(
        "measured" in lim.lower() or "scrape" in lim.lower() or "inferred" in lim.lower()
        for lim in result["data_limitations"]
    )
    # Prompt includes measured seeds and forbids fake ranking claims in system prompt
    assert "MEASURED SEED KEYWORDS" in llm.calls[0]["prompt"]
    system = llm.calls[0]["system"] or ""
    assert "rank" in system.lower() or "volume" in system.lower() or "traffic" in system.lower()


def test_seo_keywords_run_sets_inferred_only_when_no_scrape():
    llm = RecordingLLM(SEO_RESULT)

    result = seo_keywords.run(
        COMPANY_PROFILE_RESULT,
        "https://acme.example",
        llm,
        scrape_result=None,
    )

    assert result["seed_keywords"] == []
    assert result["data_mode"] == "inferred_only"
    assert any("infer" in lim.lower() for lim in result["data_limitations"])


def test_seo_keywords_ignores_llm_claimed_seed_keywords():
    """Injected seeds come from scrape, not the LLM payload."""
    forged = dict(SEO_RESULT)
    forged["seed_keywords"] = [{"keyword": "fake invented kw", "source": "title"}]
    forged["data_mode"] = "measured_only"
    llm = RecordingLLM(forged)
    scrape = _rich_scrape()

    result = seo_keywords.run(
        COMPANY_PROFILE_RESULT,
        "https://acme.example",
        llm,
        scrape_result=scrape,
    )

    assert result["data_mode"] == "hybrid"
    assert not any(s["keyword"] == "fake invented kw" for s in result["seed_keywords"])
    assert result["seed_keywords"] == extract_keyword_seeds(scrape)
