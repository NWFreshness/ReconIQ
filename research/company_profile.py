"""Module 1: Company Profile — extract what the company does and how they present themselves."""
from __future__ import annotations

from scraper.models import ScrapeResult
from scraper.scraper import extract_domain_name, scrape
from research.parsing import JSON_RESPONSE_RULES, llm_json_call
from research.schemas import CompanyProfileSchema, validate_module_output
from research.scrape_context import format_company_context

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
    "company_name", "what_they_do", "target_audience", "value_proposition", "brand_voice",
    "primary_cta", "services_products", "marketing_channels", "data_confidence", "data_limitations",
]


def run(
    target_url: str,
    llm_complete,
    scraped_content: str | None = None,
    scrape_result: ScrapeResult | None = None,
) -> dict:
    """Run the company profile module."""
    if scrape_result is not None:
        content = format_company_context(scrape_result, max_chars=12_000)
        content_label = "WEBSITE STRUCTURED CRAWL DATA"
    elif scraped_content is not None:
        content = scraped_content
        content_label = "WEBSITE CONTENT"
    else:
        content = scrape(target_url)
        content_label = "WEBSITE CONTENT"

    if not content:
        domain = extract_domain_name(target_url)
        content = (
            f"Could not access {target_url}. "
            f"The company's domain is: {domain}. "
            f"Analyze based on the domain name alone."
        )

    prompt = (
        f"TARGET URL: {target_url}\n\n"
        f"{content_label}:\n{content[:12000]}\n\n"
        f"Extract the company profile as instructed."
    )

    data = llm_json_call(
        llm_complete=llm_complete,
        prompt=prompt,
        module="company_profile",
        system=SYSTEM_PROMPT,
        required_keys=REQUIRED_KEYS,
        context="company profile",
        max_tokens=1500,
    )
    return validate_module_output(data, CompanyProfileSchema, "company profile")
