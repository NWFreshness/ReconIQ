"""Module 3: Competitor Intelligence — auto-discover and analyze competitors."""
from __future__ import annotations

from research.parsing import JSON_RESPONSE_RULES, JsonParsingError, extract_json_array, extract_json_object


SYSTEM_PROMPT = (
    "You are an expert competitive intelligence analyst. Based on the company profile and target URL, "
    "identify 4-5 direct competitors in the same market. Return a JSON array of competitor objects, "
    "each with:\n"
    "- name: company name\n"
    "- url: their website (use plausible URLs if unknown)\n"
    "- positioning: 1-2 sentence market position description\n"
    "- estimated_pricing_tier: 'budget', 'mid-market', 'premium', or 'enterprise'\n"
    "- key_messaging: their main marketing claim or tagline\n"
    "- weaknesses: 2-3 specific weaknesses or gaps\n"
    "- inferred_services: 3-5 services they likely offer\n\n"
    f"{JSON_RESPONSE_RULES}"
)


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

    raw = llm_complete(prompt, module="competitor", system=SYSTEM_PROMPT, max_tokens=2000)
    return _parse_response(raw)


def _parse_response(raw: str) -> dict:
    try:
        data = extract_json_object(raw)
    except JsonParsingError:
        competitors = extract_json_array(raw)
        return {"competitors": competitors}

    if "competitors" not in data:
        raise JsonParsingError("competitor analysis missing required keys: competitors")
    return data
