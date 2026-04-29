"""Module 3: Competitor Intelligence — auto-discover and analyze competitors."""
from __future__ import annotations

import json
import re


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
    "Return ONLY the JSON array, no preamble or explanation."
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
    # Try to extract JSON array
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if match:
        try:
            competitors = json.loads(match.group())
            return {"competitors": competitors}
        except json.JSONDecodeError:
            pass

    # Try JSON object
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            if "competitors" in data:
                return data
        except json.JSONDecodeError:
            pass

    return {"competitors": [], "raw_error": raw}