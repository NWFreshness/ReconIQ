from __future__ import annotations

import json

import pytest

from research import company_profile, competitors, seo_keywords, social_content, swot
from research.parsing import JsonParsingError, llm_json_call

COMPANY_PROFILE_RESULT = {
    "company_name": "Acme Widgets",
    "what_they_do": "Builds widgets for local businesses.",
    "target_audience": "Local business owners",
    "value_proposition": "Durable widgets delivered quickly.",
    "brand_voice": "Professional and practical",
    "primary_cta": "Request a quote",
    "services_products": ["Custom widgets", "Widget maintenance"],
    "marketing_channels": ["website", "local search"],
    "data_confidence": "high",
    "data_limitations": ["Only homepage content was available."],
}

SEO_RESULT = {
    "top_keywords": ["custom widgets", "local widgets"],
    "content_gaps": ["comparison pages", "case studies"],
    "seo_weaknesses": ["thin service pages"],
    "quick_wins": ["add local landing pages"],
    "estimated_traffic_tier": "low — inferred from narrow content footprint",
    "local_seo_signals": "weak — inferred from provided profile only",
    "data_confidence": "low",
    "data_limitations": ["No live traffic or ranking data was available."],
}

COMPETITOR_RESULT = {
    "competitors": [
        {
            "name": "WidgetCo",
            "url": "https://widgetco.example",
            "positioning": "Premium widgets for regional teams.",
            "estimated_pricing_tier": "premium",
            "key_messaging": "Widgets that scale.",
            "weaknesses": ["generic local messaging"],
            "inferred_services": ["widget consulting"],
        }
    ],
    "data_confidence": "low",
    "data_limitations": ["Competitors are inferred from market context."],
}

SOCIAL_RESULT = {
    "platforms": ["LinkedIn", "Facebook"],
    "content_quality": "moderate — inferred from company profile",
    "content_frequency": "sporadic",
    "engagement_signals": "weak",
    "review_sites": ["Google"],
    "blog_or_resources": "no",
    "content_gaps": ["customer stories"],
    "email_signals": "minimal",
    "data_confidence": "low",
    "data_limitations": ["No live social profile scrape was performed."],
}

SWOT_RESULT = {
    "swot": {
        "strengths": ["clear niche"],
        "weaknesses": ["thin content"],
        "opportunities": ["local SEO expansion"],
        "threats": ["larger regional competitors"],
    },
    "acquisition_angle": "Lead with a consultative local SEO and content audit.",
    "talking_points": ["Your service pages could capture more local intent."],
    "recommended_next_steps": ["Build a local landing page plan."],
    "competitive_advantage": "A focused local automation agency can move faster than a generic vendor.",
    "lead_generation_strategy": "Target local service businesses via Google Ads and LinkedIn outreach with a free SEO audit hook.",
    "close_rate_strategy": "Use AI lead scoring to prioritize high-intent prospects and deploy an AI chatbot for 24/7 objection handling, freeing the sales team to focus on qualified leads most likely to convert.",
    "data_confidence": "medium",
    "data_limitations": ["Strategy is inferred from module outputs."],
}


class RecordingLLM:
    def __init__(self, response: dict | str):
        self.response = response
        self.calls = []

    def __call__(self, prompt: str, module: str, system: str | None = None, max_tokens: int = 2048, **kwargs):
        self.calls.append({
            "prompt": prompt,
            "module": module,
            "system": system,
            "max_tokens": max_tokens,
            "kwargs": kwargs,
        })
        if isinstance(self.response, str):
            return self.response
        return json.dumps(self.response)


class FailingThenSucceedingLLM:
    """Returns unparseable text first, then valid JSON on retry."""
    def __init__(self, valid_response: dict):
        self.valid_response = valid_response
        self.call_count = 0

    def __call__(self, prompt: str, module: str, system: str | None = None, max_tokens: int = 2048, **kwargs):
        self.call_count += 1
        if self.call_count == 1:
            return "This is not JSON at all, just prose."
        return json.dumps(self.valid_response)


def test_company_profile_uses_scraped_content_when_available(monkeypatch):
    monkeypatch.setattr(company_profile, "scrape", lambda url: "Homepage says Acme builds durable widgets.")
    llm = RecordingLLM(COMPANY_PROFILE_RESULT)

    result = company_profile.run("https://acme.example", llm)

    assert result == COMPANY_PROFILE_RESULT
    assert llm.calls[0]["module"] == "company_profile"
    assert "Homepage says Acme builds durable widgets." in llm.calls[0]["prompt"]


def test_company_profile_falls_back_to_domain_context_when_scrape_fails(monkeypatch):
    monkeypatch.setattr(company_profile, "scrape", lambda url: "")
    llm = RecordingLLM(COMPANY_PROFILE_RESULT)

    company_profile.run("https://www.acme.example/path", llm)

    assert "Could not access https://www.acme.example/path" in llm.calls[0]["prompt"]
    assert "The company's domain is: acme.example" in llm.calls[0]["prompt"]


def test_company_profile_accepts_pre_scraped_content():
    """company_profile.run() should use scraped_content when provided, bypassing scrape()."""
    llm = RecordingLLM(COMPANY_PROFILE_RESULT)
    pre_scraped = "Pre-scraped content from cache"

    result = company_profile.run("https://acme.example", llm, scraped_content=pre_scraped)

    assert result == COMPANY_PROFILE_RESULT
    assert pre_scraped in llm.calls[0]["prompt"]


@pytest.mark.parametrize(
    ("runner", "args", "expected_module", "response"),
    [
        (company_profile.run, ("https://acme.example",), "company_profile", COMPANY_PROFILE_RESULT),
        (seo_keywords.run, (COMPANY_PROFILE_RESULT, "https://acme.example"), "seo_keywords", SEO_RESULT),
        (competitors.run, (COMPANY_PROFILE_RESULT, "https://acme.example"), "competitor", COMPETITOR_RESULT),
        (social_content.run, (COMPANY_PROFILE_RESULT, "https://acme.example"), "social_content", SOCIAL_RESULT),
        (
            swot.run,
            (COMPANY_PROFILE_RESULT, SEO_RESULT, COMPETITOR_RESULT, SOCIAL_RESULT, "https://acme.example"),
            "swot",
            SWOT_RESULT,
        ),
    ],
)
def test_each_module_calls_llm_with_correct_module_name(monkeypatch, runner, args, expected_module, response):
    monkeypatch.setattr(company_profile, "scrape", lambda url: "Homepage content")
    llm = RecordingLLM(response)

    result = runner(*args, llm)

    assert result == response
    assert llm.calls[0]["module"] == expected_module


# ── llm_json_call tests ─────────────────────────────────────────────────────


def test_llm_json_call_parses_valid_json():
    """llm_json_call should parse a valid JSON response and validate keys."""
    llm = RecordingLLM(COMPANY_PROFILE_RESULT)

    result = llm_json_call(
        llm_complete=llm,
        prompt="Analyze this company",
        module="company_profile",
        system="You are an analyst.",
        required_keys=["company_name", "what_they_do"],
        context="test",
    )

    assert result["company_name"] == "Acme Widgets"
    assert result["what_they_do"] == "Builds widgets for local businesses."


def test_llm_json_call_retries_on_bad_json():
    """llm_json_call should retry when the first response is not valid JSON."""
    llm = FailingThenSucceedingLLM(COMPANY_PROFILE_RESULT)

    result = llm_json_call(
        llm_complete=llm,
        prompt="Analyze this company",
        module="company_profile",
        system="You are an analyst.",
        required_keys=company_profile.REQUIRED_KEYS,
        context="company profile",
        max_tokens=1500,
    )

    assert llm.call_count == 2
    assert result["company_name"] == "Acme Widgets"


def test_llm_json_call_raises_after_max_retries():
    """llm_json_call should raise JsonParsingError after exhausting retries."""
    always_fail_llm = RecordingLLM("This is never valid JSON")

    with pytest.raises(JsonParsingError):
        llm_json_call(
            llm_complete=always_fail_llm,
            prompt="Analyze this",
            module="company_profile",
            system="You are an analyst.",
            required_keys=["company_name"],
            context="test",
            max_retries=2,
        )


def test_llm_json_call_retries_on_missing_keys():
    """llm_json_call should retry when JSON parses but required keys are missing."""
    incomplete = {"company_name": "Acme"}  # missing most required keys
    # First call returns incomplete JSON, second returns complete JSON
    call_count = [0]
    complete = COMPANY_PROFILE_RESULT

    def partial_then_full(prompt, module, system=None, max_tokens=2048, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return json.dumps(incomplete)
        return json.dumps(complete)

    result = llm_json_call(
        llm_complete=partial_then_full,
        prompt="Analyze",
        module="company_profile",
        system="Analyst.",
        required_keys=["company_name", "what_they_do", "target_audience"],
        context="test",
    )

    assert call_count[0] == 2
    assert result["company_name"] == "Acme Widgets"


# ── Direct parsing tests (via extract_json_object + require_keys) ────────────


@pytest.mark.parametrize(
    ("response",),
    [
        (COMPANY_PROFILE_RESULT,),
        (SEO_RESULT,),
        (COMPETITOR_RESULT,),
        (SOCIAL_RESULT,),
        (SWOT_RESULT,),
    ],
)
def test_extract_json_object_parses_strict_json(response):
    """All module result dicts should round-trip through JSON parse."""
    from research.parsing import extract_json_object, require_keys
    raw = json.dumps(response)
    assert extract_json_object(raw) == response


def test_require_keys_rejects_incomplete_json():
    """require_keys should raise JsonParsingError when keys are missing."""
    from research.parsing import extract_json_object, require_keys
    incomplete = {"company_name": "Acme"}
    with pytest.raises(JsonParsingError):
        require_keys(incomplete, ["company_name", "what_they_do"], context="test")


def test_bad_json_raises_controlled_error():
    """extract_json_object should raise JsonParsingError on garbage input."""
    from research.parsing import extract_json_object
    with pytest.raises(JsonParsingError):
        extract_json_object("not json at all")


def test_competitor_module_requires_object_with_metadata_not_legacy_array():
    legacy_array = json.dumps(COMPETITOR_RESULT["competitors"])

    with pytest.raises(JsonParsingError):
        competitors.run(COMPANY_PROFILE_RESULT, "https://acme.example", RecordingLLM(legacy_array))


def test_swot_module_requires_nested_swot_keys():
    incomplete = SWOT_RESULT.copy()
    incomplete["swot"] = {"strengths": [], "weaknesses": [], "opportunities": []}

    with pytest.raises(JsonParsingError):
        swot.run(
            COMPANY_PROFILE_RESULT, SEO_RESULT, COMPETITOR_RESULT, SOCIAL_RESULT,
            "https://acme.example", RecordingLLM(incomplete),
        )