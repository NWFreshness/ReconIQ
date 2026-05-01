"""Module 3: Competitor Intelligence — discover and verify competitors via search + scrape."""
from __future__ import annotations

from scraper.models import ScrapeResult
from scraper.scraper import scrape
from research.parsing import JSON_RESPONSE_RULES, llm_json_call
from research.schemas import CompetitorItem, CompetitorSchema, validate_module_output
from research.scrape_context import format_competitor_context
from research.search import discover_competitors

SYSTEM_PROMPT = (
    "You are an expert competitive intelligence analyst. You are given VERIFIED competitor data "
    "from real search results and homepage scrapes. Analyze each competitor and return a JSON object with:\n"
    "- competitors: array of verified competitor objects, each with:\n"
    "  - name: company name (from search result title or scraped homepage)\n"
    "  - url: their verified website URL\n"
    "  - positioning: 1-2 sentence market position based on their scraped homepage\n"
    "  - estimated_pricing_tier: 'budget', 'mid-market', 'premium', or 'enterprise' based on their site\n"
    "  - key_messaging: their main marketing claim or tagline from their site\n"
    "  - weaknesses: 2-3 specific weaknesses or gaps visible on their site\n"
    "  - inferred_services: 3-5 services they likely offer based on their homepage\n"
    "- data_confidence: 'low', 'medium', or 'high' based on how many competitors were verified\n"
    "- data_limitations: list of caveats; explicitly state if no competitors could be verified\n\n"
    f"{JSON_RESPONSE_RULES}"
)

REQUIRED_KEYS = [
    "competitors", "data_confidence", "data_limitations",
]


def _scrape_competitor_homepage(url: str) -> dict:
    """Do a quick homepage scrape of a competitor. Returns a dict with title, description, text."""
    try:
        text = scrape(url, timeout=8)
        return {
            "url": url,
            "text": text[:3000] if text else "",
        }
    except Exception:
        return {"url": url, "text": ""}


def _build_competitor_items(search_results: list[dict], scraped_data: list[dict]) -> list[dict]:
    """Build competitor dicts from search results + scraped data."""
    items = []
    for i, result in enumerate(search_results):
        scrape_info = scraped_data[i] if i < len(scraped_data) else {"text": ""}
        items.append({
            "name": result.get("title", "").split("|")[0].split("-")[0].strip(),
            "url": result["url"],
            "homepage_text": scrape_info.get("text", ""),
            "search_snippet": result.get("snippet", ""),
        })
    return items


def run(
    company_profile: dict,
    target_url: str,
    llm_complete,
    scrape_result: ScrapeResult | None = None,
    search_discovery=None,
) -> dict:
    from research.search import discover_competitors as default_discovery

    # Step 1: Discover competitors via search
    discover_fn = search_discovery or default_discovery
    search_info = discover_fn(company_profile, target_url)
    search_results = search_info.get("results", [])

    # Step 2: Scrape each competitor's homepage for verification
    scraped_competitors: list[dict] = []
    if search_results:
        scraped_data = [_scrape_competitor_homepage(r["url"]) for r in search_results]
        scraped_competitors = _build_competitor_items(search_results, scraped_data)

    # Step 3: Build prompt with verified data only
    profile_text = "\n".join(f"- {k}: {v}" for k, v in company_profile.items() if k != "error")
    parts = [f"TARGET URL: {target_url}", f"COMPANY PROFILE:\n{profile_text}"]

    if scrape_result is not None:
        parts.append("OBSERVED EXTERNAL LINKS FROM TARGET SITE:\n" + format_competitor_context(scrape_result))

    if scraped_competitors:
        comp_lines = ["VERIFIED COMPETITORS (from search + homepage scrape):\n"]
        for comp in scraped_competitors:
            comp_lines.append(
                f"- Name: {comp['name']}\n"
                f"  URL: {comp['url']}\n"
                f"  Search snippet: {comp['search_snippet'][:200]}\n"
                f"  Homepage text: {comp['homepage_text'][:800]}\n"
            )
        parts.append("\n".join(comp_lines))
    else:
        parts.append(
            "VERIFIED COMPETITORS: None found. "
            "Search results were empty or the search API is not configured. "
            "No competitor data is available for analysis."
        )

    prompt = "\n\n".join(parts) + "\n\nAnalyze ONLY the verified competitors above. Do not invent or infer competitors."

    data = llm_json_call(
        llm_complete=llm_complete,
        prompt=prompt,
        module="competitor",
        system=SYSTEM_PROMPT,
        required_keys=REQUIRED_KEYS,
        context="competitor analysis",
        max_tokens=2000,
    )

    # Ensure competitors only contains verified URLs from search results
    verified_urls = {r["url"] for r in search_results}
    cleaned_competitors: list[dict] = []
    for comp in data.get("competitors", []):
        if isinstance(comp, dict) and comp.get("url") in verified_urls:
            cleaned_competitors.append(comp)

    data["competitors"] = cleaned_competitors
    data["scraped_competitors"] = cleaned_competitors  # All are verified from search+scrape
    data["inferred_competitors"] = []  # Never infer

    # Merge limitations
    limitations = data.setdefault("data_limitations", [])
    for lim in search_info.get("data_limitations", []):
        if lim and lim not in limitations:
            limitations.append(lim)
    if not cleaned_competitors:
        msg = "No verified competitors were found via search and homepage scrape."
        if msg not in limitations:
            limitations.append(msg)

    return validate_module_output(data, CompetitorSchema, "competitor analysis")
