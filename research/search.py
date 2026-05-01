"""Optional live search helpers for competitor discovery."""
from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import requests

from core.settings import load_config


def _empty_search_result(reason: str, provider: str = "disabled", query: str = "") -> dict[str, Any]:
    return {"results": [], "provider": provider, "query": query, "data_limitations": [reason]}


def _build_competitor_query(company_profile: dict, target_url: str) -> str:
    domain = urlparse(target_url).netloc.replace("www.", "") or target_url
    parts = [str(company_profile.get("company_name") or domain), "competitors"]
    for item in company_profile.get("services_products", [])[:4]:
        parts.append(str(item))
    audience = company_profile.get("target_audience")
    if audience:
        parts.append(str(audience))
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
        results.append({
            "title": str(item.get("title") or ""),
            "url": str(item.get("url") or ""),
            "snippet": str(item.get("description") or item.get("snippet") or ""),
        })
    return [result for result in results if result["url"]]


def discover_competitors(company_profile: dict, target_url: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = config or load_config()
    search_cfg = cfg.get("search", {})
    query = _build_competitor_query(company_profile, target_url)
    if not search_cfg.get("enabled", False):
        return _empty_search_result("Live competitor search is disabled; competitors may be inferred.", query=query)

    provider = search_cfg.get("provider", "brave")
    max_results = int(search_cfg.get("max_results", 5) or 5)
    if provider != "brave":
        return _empty_search_result(f"Unsupported search provider '{provider}'; competitors may be inferred.", provider=provider, query=query)

    brave_cfg = search_cfg.get("brave", {})
    api_key = brave_cfg.get("api_key") or ""
    endpoint = brave_cfg.get("endpoint") or "https://api.search.brave.com/res/v1/web/search"
    if not api_key or api_key.startswith("${"):
        return _empty_search_result("Brave Search API key is not configured; competitors may be inferred.", provider="brave", query=query)

    try:
        results = _brave_search(query, api_key, endpoint, max_results)
    except Exception as exc:
        return _empty_search_result(f"Live competitor search failed: {exc}", provider="brave", query=query)

    limitations = [] if results else ["Live competitor search returned no results; competitors may be inferred."]
    return {"results": results, "provider": "brave", "query": query, "data_limitations": limitations}
