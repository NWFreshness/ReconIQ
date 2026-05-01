"""Module 3: Competitor Intelligence — auto-discover and analyze competitors."""
from __future__ import annotations

from scraper.models import ScrapeResult
from research.parsing import JSON_RESPONSE_RULES, llm_json_call
from research.schemas import CompetitorSchema, validate_module_output
from research.scrape_context import format_competitor_context

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
    "- scraped_competitors: competitors observed from crawl/search results\n"
    "- inferred_competitors: competitors derived purely from market inference\n"
    "- data_confidence: 'low', 'medium', or 'high' with brief rationale\n"
    "- data_limitations: list of caveats, especially where competitors are inferred\n\n"
    f"{JSON_RESPONSE_RULES}"
)

REQUIRED_KEYS = [
    "competitors", "scraped_competitors", "inferred_competitors",
    "data_confidence", "data_limitations",
]


def run(
    company_profile: dict,
    target_url: str,
    llm_complete,
    scrape_result: ScrapeResult | None = None,
    search_discovery=None,
) -> dict:
    from research.search import discover_competitors as default_discovery
    profile_text = "\n".join(f"- {k}: {v}" for k, v in company_profile.items() if k != "error")
    parts = [f"TARGET URL: {target_url}", f"COMPANY PROFILE:\n{profile_text}"]

    if scrape_result is not None:
        parts.append("OBSERVED EXTERNAL LINKS:\n" + format_competitor_context(scrape_result))

    discover_fn = search_discovery or default_discovery
    search_info = discover_fn(company_profile, target_url)
    search_results = search_info.get("results", [])
    if search_results:
        lines = ["LIVE SEARCH RESULTS:\n"]
        for r in search_results[:6]:
            lines.append(f"- {r.get('title', 'Unknown')}: {r.get('url', '')}\n  {r.get('snippet', '')}")
        parts.append("".join(lines))
    else:
        parts.append("LIVE SEARCH RESULTS: None available; competitors may be inferred only.")

    prompt = "\n\n".join(parts) + "\n\nIdentify direct competitors and analyze each as instructed."

    data = llm_json_call(
        llm_complete=llm_complete,
        prompt=prompt,
        module="competitor",
        system=SYSTEM_PROMPT,
        required_keys=REQUIRED_KEYS,
        context="competitor analysis",
        max_tokens=2000,
    )
    # Merge search limitations
    limitations = data.setdefault("data_limitations", [])
    for lim in search_info.get("data_limitations", []):
        if lim and lim not in limitations:
            limitations.append(lim)
    return validate_module_output(data, CompetitorSchema, "competitor analysis")
