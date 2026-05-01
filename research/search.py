"""Optional live search helpers for competitor and social discovery."""
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


def _brave_search(query: str, api_key: str, endpoint: str, limit: int = 5) -> list[dict[str, str]]:
    response = requests.get(
        endpoint,
        headers={"Accept": "application/json", "X-Subscription-Token": api_key},
        params={"q": query, "count": limit},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    results = []
    for item in data.get("web", {}).get("results", [])[:limit]:
        url = str(item.get("url") or "")
        if url:
            results.append({
                "title": str(item.get("title") or ""),
                "url": url,
                "snippet": str(item.get("description") or item.get("snippet") or ""),
            })
    return results


def discover_competitors(company_profile: dict, target_url: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = config or load_config()
    search_cfg = cfg.get("search", {})
    query = _build_competitor_query(company_profile, target_url)
    if not search_cfg.get("enabled", False):
        return _empty_search_result("Live competitor search is disabled.", query=query)

    provider = search_cfg.get("provider", "brave")
    max_results = int(search_cfg.get("max_results", 5) or 5)
    if provider != "brave":
        return _empty_search_result(f"Unsupported search provider '{provider}'.", provider=provider, query=query)

    brave_cfg = search_cfg.get("brave", {})
    api_key = brave_cfg.get("api_key") or ""
    endpoint = brave_cfg.get("endpoint") or "https://api.search.brave.com/res/v1/web/search"
    if not api_key or api_key.startswith("${"):
        return _empty_search_result("Brave Search API key is not configured.", provider="brave", query=query)

    try:
        results = _brave_search(query, api_key, endpoint, max_results)
    except Exception as exc:
        return _empty_search_result(f"Live competitor search failed: {exc}", provider="brave", query=query)

    limitations = [] if results else ["Live competitor search returned no results."]
    return {"results": results, "accounts": [], "provider": "brave", "query": query, "data_limitations": limitations}


def discover_social_accounts(company_name: str, target_url: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Search for verified social media accounts for a company."""
    cfg = config or load_config()
    search_cfg = cfg.get("search", {})

    if not search_cfg.get("enabled", False):
        return _empty_search_result("Live social search is disabled.")

    provider = search_cfg.get("provider", "brave")
    if provider != "brave":
        return _empty_search_result(f"Unsupported search provider '{provider}'.", provider=provider)

    brave_cfg = search_cfg.get("brave", {})
    api_key = brave_cfg.get("api_key") or ""
    endpoint = brave_cfg.get("endpoint") or "https://api.search.brave.com/res/v1/web/search"
    if not api_key or api_key.startswith("${"):
        return _empty_search_result("Brave Search API key is not configured.", provider="brave")

    accounts: list[dict[str, str]] = []
    limitations: list[str] = []

    # Search for each major platform
    platforms = [
        ("linkedin", f'{company_name} LinkedIn'),
        ("facebook", f'{company_name} Facebook'),
        ("instagram", f'{company_name} Instagram'),
        ("twitter", f'{company_name} Twitter'),
    ]

    for platform, query in platforms:
        if not company_name:
            continue
        try:
            results = _brave_search(query, api_key, endpoint, limit=3)
            for r in results:
                url = r["url"].lower()
                if platform in url and platform not in urlparse(target_url).netloc.lower():
                    # Verify it's actually the company's page by checking title
                    accounts.append({"platform": platform, "url": r["url"]})
                    break  # Only take top result per platform
        except Exception as exc:
            limitations.append(f"Social search for {platform} failed: {exc}")

    if not accounts:
        limitations.append("No verified social media accounts found via search.")

    return {
        "results": [],
        "accounts": accounts,
        "provider": "brave",
        "query": company_name,
        "data_limitations": limitations,
    }
