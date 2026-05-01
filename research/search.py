"""Optional live search helpers for competitor and social discovery via Firecrawl."""
from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import requests

from core.settings import load_config


def _empty_search_result(reason: str, provider: str = "disabled", query: str = "") -> dict[str, Any]:
    return {"results": [], "accounts": [], "provider": provider, "query": query, "data_limitations": [reason]}


def _build_competitor_query(company_profile: dict, target_url: str) -> str:
    domain = urlparse(target_url).netloc.replace("www.", "") or target_url
    parts = []
    # Use location if available
    city = company_profile.get("location_city", "")
    state = company_profile.get("location_state", "")
    if city and state:
        parts.append(f"{city} {state}")
    elif city:
        parts.append(city)
    # Use services to find similar companies
    for item in company_profile.get("services_products", [])[:3]:
        parts.append(str(item))
    # Add company name to find similar
    name = company_profile.get("company_name", "")
    if name:
        parts.append(f"companies like {name}")
    if not parts:
        parts = [str(company_profile.get("company_name") or domain), "competitors"]
    return " ".join(part for part in parts if part).strip()


def _firecrawl_search(query: str, api_key: str, api_url: str, limit: int = 5) -> list[dict[str, str]]:
    from firecrawl import FirecrawlApp

    app = FirecrawlApp(api_key=api_key, api_url=api_url)
    response = app.v2.search(query=query, limit=limit)

    results = []
    web_results = getattr(response, "web", None) or []
    for item in web_results[:limit]:
        url = getattr(item, "url", None) or ""
        if url:
            results.append({
                "title": getattr(item, "title", "") or "",
                "url": url,
                "snippet": getattr(item, "description", "") or getattr(item, "snippet", "") or "",
            })
    return results


def discover_competitors(company_profile: dict, target_url: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = config or load_config()
    search_cfg = cfg.get("search", {})
    query = _build_competitor_query(company_profile, target_url)

    if not search_cfg.get("enabled", False):
        return _empty_search_result("Live competitor search is disabled.", query=query)

    provider = search_cfg.get("provider", "firecrawl")
    if provider != "firecrawl":
        return _empty_search_result(f"Unsupported search provider '{provider}'.", provider=provider, query=query)

    firecrawl_cfg = search_cfg.get("firecrawl", {})
    api_key = firecrawl_cfg.get("api_key") or ""
    api_url = firecrawl_cfg.get("api_url") or "https://api.firecrawl.dev"
    if not api_key or api_key.startswith("${"):
        return _empty_search_result("Firecrawl API key is not configured.", provider="firecrawl", query=query)

    max_results = int(search_cfg.get("max_results", 5) or 5)

    try:
        results = _firecrawl_search(query, api_key, api_url, max_results)
    except Exception as exc:
        return _empty_search_result(f"Live competitor search failed: {exc}", provider="firecrawl", query=query)

    limitations = [] if results else ["Live competitor search returned no results."]
    return {"results": results, "accounts": [], "provider": "firecrawl", "query": query, "data_limitations": limitations}


def discover_social_accounts(company_name: str, target_url: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Search for verified social media accounts for a company via Firecrawl."""
    cfg = config or load_config()
    search_cfg = cfg.get("search", {})

    if not search_cfg.get("enabled", False):
        return _empty_search_result("Live social search is disabled.")

    provider = search_cfg.get("provider", "firecrawl")
    if provider != "firecrawl":
        return _empty_search_result(f"Unsupported search provider '{provider}'.", provider=provider)

    firecrawl_cfg = search_cfg.get("firecrawl", {})
    api_key = firecrawl_cfg.get("api_key") or ""
    api_url = firecrawl_cfg.get("api_url") or "https://api.firecrawl.dev"
    if not api_key or api_key.startswith("${"):
        return _empty_search_result("Firecrawl API key is not configured.", provider="firecrawl")

    accounts: list[dict[str, str]] = []
    limitations: list[str] = []

    if not company_name:
        return _empty_search_result("No company name available for social search.", provider="firecrawl")

    # Search for each major platform
    platforms = [
        ("linkedin", f"{company_name} LinkedIn"),
        ("facebook", f"{company_name} Facebook"),
        ("instagram", f"{company_name} Instagram"),
        ("twitter", f"{company_name} Twitter OR X"),
    ]

    for platform, query in platforms:
        try:
            results = _firecrawl_search(query, api_key, api_url, limit=3)
            target_netloc = urlparse(target_url).netloc.lower()
            for r in results:
                url = r["url"].lower()
                # Skip if it's the company's own domain
                if target_netloc and target_netloc in url:
                    continue
                if platform in url:
                    accounts.append({"platform": platform, "url": r["url"]})
                    break  # Only take top result per platform
        except Exception as exc:
            limitations.append(f"Social search for {platform} failed: {exc}")

    if not accounts:
        limitations.append("No verified social media accounts found via search.")

    return {
        "results": [],
        "accounts": accounts,
        "provider": "firecrawl",
        "query": company_name,
        "data_limitations": limitations,
    }
