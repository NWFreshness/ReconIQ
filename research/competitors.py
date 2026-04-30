"""Module 3: Competitor Intelligence — auto-discover and analyze competitors."""
from __future__ import annotations

from research.parsing import JSON_RESPONSE_RULES, JsonParsingError, llm_json_call, require_keys

SYSTEM_PROMPT = (
    "You are an expert competitive intelligence analyst. Based on the company profile and target URL, "
    "identify 4-5 direct competitors in the same market. Return a JSON object with a competitors array. "
    "Each competitor object must include:\n"
    "- name: company name\n"
    "- url: their website (use plausible URLs if unknown)\n"
    "- positioning: 1-2 sentence market position description\n"
    "- estimated_pricing_tier: 'budget', 'mid-market', 'premium', or 'enterprise'\n"
    "- key_messaging: their main marketing claim or tagline\n"
    "- weaknesses: 2-3 specific weaknesses or gaps\n"
    "- inferred_services: 3-5 services they likely offer\n"
    "Also include top-level keys:\n"
    "- data_confidence: 'low', 'medium', or 'high' with brief rationale\n"
    "- data_limitations: list of caveats, especially where competitors are inferred\n\n"
    f"{JSON_RESPONSE_RULES}"
)

REQUIRED_KEYS = ["competitors", "data_confidence", "data_limitations"]
REQUIRED_COMPETITOR_KEYS = [
    "name",
    "url",
    "positioning",
    "estimated_pricing_tier",
    "key_messaging",
    "weaknesses",
    "inferred_services",
]


def run(company_profile: dict, target_url: str, llm_complete) -> dict:
    """
    Run the competitor intelligence module.

    Args:
        company_profile: Output from Module 1.
        target_url: Original target URL.
        llm_complete: LLM completion callable.

    Returns:
        Dict with 'competitors' key containing list of competitor dicts.
    """
    profile_text = "\n".join(f"- {k}: {v}" for k, v in company_profile.items() if k != "error")

    prompt = (
        f"TARGET URL: {target_url}\n"
        f"COMPANY PROFILE:\n{profile_text}\n\n"
        f"Identify direct competitors and analyze each as instructed."
    )

    data = llm_json_call(
        llm_complete=llm_complete,
        prompt=prompt,
        module="competitor",
        system=SYSTEM_PROMPT,
        required_keys=REQUIRED_KEYS,
        context="competitor analysis",
        max_tokens=2000,
    )

    # Extra validation: check competitor list structure
    competitors = data.get("competitors")
    if not isinstance(competitors, list):
        raise JsonParsingError("competitor analysis field 'competitors' must be a list")
    for index, competitor in enumerate(competitors, start=1):
        if not isinstance(competitor, dict):
            raise JsonParsingError(f"competitor analysis item {index} must be an object")
        require_keys(competitor, REQUIRED_COMPETITOR_KEYS, context=f"competitor analysis item {index}")

    return data