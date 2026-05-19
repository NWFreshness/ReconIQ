"""Optional live search helpers for competitor and social discovery.

This module now delegates to the Strategy Pattern in search_provider.py.
Existing callers (competitors.py, social_content.py) continue to work
unchanged, but new code should use search_provider.get_search_provider().

When adding a new search backend (DuckDuckGo, SearXNG, Bing), implement the
SearchProvider interface and register it in search_provider.py — no changes
needed here.
"""

from __future__ import annotations

from typing import Any

from research.search_provider import (
    DisabledSearchProvider,
    FirecrawlSearchProvider,
    SerpAPISearchProvider,
    FallbackSearchProvider,
    MAJOR_SOCIAL_PLATFORMS,
    SearchProvider,
    _build_competitor_query,
    get_search_provider,
)

# Re-export the provider classes for direct use
__all__ = [
    "DisabledSearchProvider",
    "FallbackSearchProvider",
    "FirecrawlSearchProvider",
    "MAJOR_SOCIAL_PLATFORMS",
    "SerpAPISearchProvider",
    "discover_competitors",
    "discover_social_accounts",
    "get_search_provider",
]


def discover_competitors(
    company_profile: dict, target_url: str, config: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Discover competitors via the configured search provider.

    Delegates to the Strategy Pattern — the caller doesn't need to know
    whether Firecrawl, DuckDuckGo, or SearXNG is handling the request.
    """
    provider = get_search_provider(config)
    return provider.discover_competitors(company_profile, target_url)


def discover_social_accounts(
    company_name: str, target_url: str, config: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Search for verified social media accounts for a company.

    Delegates to the Strategy Pattern — transparent to callers.
    """
    provider = get_search_provider(config)
    return provider.discover_social_accounts(company_name, target_url)
