"""Module 2: SEO & Keywords — analyze search presence and content gaps."""
from __future__ import annotations

from research.parsing import JSON_RESPONSE_RULES, extract_json_object


SYSTEM_PROMPT = (
    "You are an expert SEO analyst. Based on the provided company profile and target URL, "
    "infer the company's SEO landscape. Return a JSON object with:\n"
    "- top_keywords: 8-12 likely organic search terms they rank for\n"
    "- content_gaps: 4-6 keyword areas they likely do NOT target well\n"
    "- seo_weaknesses: 4-5 specific weaknesses (technical, content, or backlink)\n"
    "- quick_wins: 3-4 SEO improvements they could make with moderate effort\n"
    "- estimated_traffic_tier: 'low', 'medium', or 'high' (explain briefly)\n"
    "- local_seo_signals: 'strong', 'moderate', or 'weak' (Google Business Profile, local keywords)\n\n"
    f"{JSON_RESPONSE_RULES}"
)


def run(company_profile: dict, target_url: str, llm_complete) -> dict:
    """
    Run the SEO & keywords module.

    Args:
        company_profile: Output from Module 1.
        target_url: Original target URL.
        llm_complete: LLM completion callable.

    Returns:
        Dict with SEO analysis fields.
    """
    profile_text = "\n".join(f"- {k}: {v}" for k, v in company_profile.items() if k != "error")

    prompt = (
        f"TARGET URL: {target_url}\n"
        f"COMPANY PROFILE:\n{profile_text}\n\n"
        f"Infer the SEO landscape as instructed."
    )

    raw = llm_complete(prompt, module="seo_keywords", system=SYSTEM_PROMPT, max_tokens=1200)
    return _parse_response(raw)


def _parse_response(raw: str) -> dict:
    return extract_json_object(raw)
