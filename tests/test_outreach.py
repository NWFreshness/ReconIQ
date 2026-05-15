from __future__ import annotations

import json

import pytest

from research import outreach
from research.parsing import JsonParsingError


COMPANY_PROFILE = {
    "company_name": "Acme HVAC",
    "what_they_do": "Residential HVAC installation and repair.",
    "target_audience": "Homeowners in Vancouver, WA",
    "value_proposition": "Fast local HVAC service.",
    "primary_cta": "Schedule service",
}

SEO_KEYWORDS = {
    "top_keywords": ["hvac repair vancouver wa", "furnace installation"],
    "content_gaps": ["No heat pump rebate page", "No emergency HVAC landing page"],
    "quick_wins": ["Add local service pages"],
}

COMPETITORS = {
    "competitors": [
        {
            "name": "Comfort Pros",
            "positioning": "Premium same-day service",
            "weaknesses": ["Thin automation messaging"],
        }
    ],
}

SOCIAL_CONTENT = {
    "content_quality": "sporadic",
    "content_gaps": ["No maintenance tips sequence"],
    "verified_social_accounts": [{"platform": "facebook", "url": "https://facebook.com/acme"}],
}

SWOT = {
    "swot": {
        "strengths": ["Strong local service reputation"],
        "weaknesses": ["Weak conversion follow-up"],
        "opportunities": ["Automated quote follow-up"],
        "threats": ["Larger regional competitors"],
    },
    "acquisition_angle": "Lead with an AI follow-up automation audit.",
    "talking_points": ["You could recover missed estimate requests."],
    "recommended_next_steps": ["Map quote intake and follow-up workflow."],
}

OUTREACH_RESULT = {
    "cold_email": "Subject: Recovering missed HVAC estimate requests\n\nHi Acme team...",
    "linkedin_dm": "Noticed Acme HVAC has a strong local service angle...",
    "discovery_call_opener": "I noticed your service flow could benefit from faster estimate follow-up.",
    "proposal_outline": "1. Intake audit\n2. Follow-up automation\n3. Reporting dashboard",
    "follow_up_sequence": [
        "Day 2: Share the missed-estimate recovery idea.",
        "Day 5: Send a short local HVAC automation example.",
        "Day 9: Offer a 15-minute workflow audit.",
    ],
    "data_confidence": "medium",
    "data_limitations": ["Generated from provided ReconIQ analysis outputs."],
}


class RecordingLLM:
    def __init__(self, response: dict | str):
        self.response = response
        self.calls: list[dict] = []

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


def test_outreach_module_generates_valid_pack_from_all_upstream_outputs():
    llm = RecordingLLM(OUTREACH_RESULT)

    result = outreach.run(
        company_profile=COMPANY_PROFILE,
        seo_keywords=SEO_KEYWORDS,
        competitor=COMPETITORS,
        social_content=SOCIAL_CONTENT,
        swot=SWOT,
        target_url="https://acme.example",
        llm_complete=llm,
    )

    assert result == OUTREACH_RESULT
    assert llm.calls[0]["module"] == "outreach"
    assert llm.calls[0]["max_tokens"] >= 1800
    prompt = llm.calls[0]["prompt"]
    assert "TARGET URL: https://acme.example" in prompt
    assert "--- COMPANY PROFILE ---" in prompt
    assert "Acme HVAC" in prompt
    assert "--- SEO & KEYWORDS ---" in prompt
    assert "hvac repair vancouver wa" in prompt
    assert "--- COMPETITOR INTELLIGENCE ---" in prompt
    assert "Comfort Pros" in prompt
    assert "--- SOCIAL & CONTENT ---" in prompt
    assert "maintenance tips sequence" in prompt
    assert "--- SWOT & ACQUISITION STRATEGY ---" in prompt
    assert "AI follow-up automation audit" in prompt


def test_outreach_module_uses_strict_sales_asset_prompt():
    llm = RecordingLLM(OUTREACH_RESULT)

    outreach.run(COMPANY_PROFILE, SEO_KEYWORDS, COMPETITORS, SOCIAL_CONTENT, SWOT, "https://acme.example", llm)

    system = llm.calls[0]["system"]
    assert "cold_email" in system
    assert "linkedin_dm" in system
    assert "discovery_call_opener" in system
    assert "proposal_outline" in system
    assert "follow_up_sequence" in system
    assert "Return valid JSON only" in system


def test_outreach_module_validates_output_schema():
    invalid = OUTREACH_RESULT.copy()
    invalid["follow_up_sequence"] = "not a list"

    with pytest.raises(JsonParsingError, match="follow_up_sequence"):
        outreach.run(COMPANY_PROFILE, SEO_KEYWORDS, COMPETITORS, SOCIAL_CONTENT, SWOT, "https://acme.example", RecordingLLM(invalid))


def test_outreach_module_retries_on_bad_json_then_succeeds():
    calls = {"count": 0}

    def flaky_llm(prompt: str, module: str, system: str | None = None, max_tokens: int = 2048, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            return "not json"
        return json.dumps(OUTREACH_RESULT)

    result = outreach.run(COMPANY_PROFILE, SEO_KEYWORDS, COMPETITORS, SOCIAL_CONTENT, SWOT, "https://acme.example", flaky_llm)

    assert calls["count"] == 2
    assert result["cold_email"].startswith("Subject:")
