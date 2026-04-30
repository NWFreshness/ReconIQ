"""Module 1: Company Profile — extract what the company does and how they present themselves."""
from __future__ import annotations

from scraper.scraper import scrape, extract_domain_name
from research.parsing import JSON_RESPONSE_RULES, extract_json_object, require_keys


SYSTEM_PROMPT = (
    "You are an expert marketing analyst. Analyze the following website content "
    "and extract a structured company profile. Return a JSON object with these fields:\n"
    "- company_name: inferred name\n"
    "- what_they_do: 1-2 sentence description\n"
    "- target_audience: who they serve\n"
    "- value_proposition: their main value claim\n"
    "- brand_voice: descriptive tags (e.g. professional, friendly, urgent)\n"
    "- primary_cta: main call-to-action text\n"
    "- services_products: list of 3-8 specific offerings\n"
    "- marketing_channels: inferred channels they use (website, social, email, etc.)\n"
    "- data_confidence: 'low', 'medium', or 'high' with brief rationale\n"
    "- data_limitations: list of key caveats about source quality\n"
    "If you cannot determine a field, use 'Not discernible from available data'.\n\n"
    f"{JSON_RESPONSE_RULES}"
)

REQUIRED_KEYS = [
    "company_name",
    "what_they_do",
    "target_audience",
    "value_proposition",
    "brand_voice",
    "primary_cta",
    "services_products",
    "marketing_channels",
    "data_confidence",
    "data_limitations",
]


def run(target_url: str, llm_complete) -> dict:
    """
    Run the company profile module.

    Args:
        target_url: URL to analyze.
        llm_complete: Callable(prompt, module, system, max_tokens) -> str.

    Returns:
        Dict with company profile fields.
    """
    content = scrape(target_url)

    if not content:
        # Fallback: use domain name as hint
        domain = extract_domain_name(target_url)
        content = (
            f"Could not access {target_url}. "
            f"The company's domain is: {domain}. "
            f"Analyze based on the domain name alone."
        )

    prompt = (
        f"TARGET URL: {target_url}\n\n"
        f"WEBSITE CONTENT:\n{content[:8000]}\n\n"
        f"Extract the company profile as instructed."
    )

    raw = llm_complete(prompt, module="company_profile", system=SYSTEM_PROMPT, max_tokens=1500)

    return _parse_response(raw)


def _parse_response(raw: str) -> dict:
    """Parse the LLM text response into a structured dict."""
    data = extract_json_object(raw)
    return require_keys(data, REQUIRED_KEYS, context="company profile")
