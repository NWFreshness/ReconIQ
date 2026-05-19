"""Strategy Pattern: Pluggable search providers for competitor and social discovery.

Before this refactor, research/search.py hard-coded Firecrawl as the only
search backend. Adding a local search provider (DuckDuckGo, SearXNG, Bing)
required modifying core search logic, violating the Open/Closed Principle.

With the Strategy Pattern, search providers are interchangeable. The concrete
provider is selected via config and injected — no module code changes when a new
backend is added.

Usage:
    from research.search_provider import get_search_provider

    provider = get_search_provider(config)
    results = provider.discover_competitors(company_profile, target_url)
"""

from __future__ import annotations

import abc
from typing import Any
from urllib.parse import urlparse

from research.competitor_query import CompetitorQueryBuilder

# Re-export _build_competitor_query for backward compatibility with search.py
from research.competitor_query import _build_competitor_query

MAJOR_SOCIAL_PLATFORMS = (
    ("linkedin", "LinkedIn"),
    ("facebook", "Facebook"),
    ("instagram", "Instagram"),
    ("twitter", "Twitter OR X"),
)


# ── Abstract Strategy ──────────────────────────────────────────────────────


class SearchProvider(abc.ABC):
    """Strategy interface for search backends.

    Concrete implementations must provide discover_competitors() and
    discover_social_accounts(). The factory function get_search_provider()
    selects the right strategy based on config.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Human-readable provider name (e.g. 'firecrawl', 'duckduckgo')."""
        ...

    @abc.abstractmethod
    def discover_competitors(
        self, company_profile: dict[str, Any], target_url: str
    ) -> dict[str, Any]:
        """Search for competitor companies and return structured results.

        Returns:
            dict with keys: results, accounts, provider, query, data_limitations
        """
        ...

    @abc.abstractmethod
    def discover_social_accounts(
        self, company_name: str, target_url: str
    ) -> dict[str, Any]:
        """Search for verified social media accounts.

        Returns:
            dict with keys: results, accounts, provider, query, data_limitations
        """
        ...


# ── Shared helpers ─────────────────────────────────────────────────────────


def _empty_search_result(
    reason: str, provider: str = "disabled", query: str = ""
) -> dict[str, Any]:
    return {
        "results": [],
        "accounts": [],
        "provider": provider,
        "query": query,
        "data_limitations": [reason],
    }


# ── Concrete Strategy: Firecrawl ───────────────────────────────────────────


class FirecrawlSearchProvider(SearchProvider):
    """Firecrawl-powered search via their v2 API."""

    def __init__(self, api_key: str, api_url: str = "https://api.firecrawl.dev"):
        self._api_key = api_key
        self._api_url = api_url

    @property
    def name(self) -> str:
        return "firecrawl"

    def discover_competitors(
        self, company_profile: dict[str, Any], target_url: str
    ) -> dict[str, Any]:
        builder = CompetitorQueryBuilder(company_profile, target_url)
        queries = builder.build_query_set()
        all_results: list[dict[str, str]] = []
        all_limitations: list[str] = []
        used_urls: set[str] = set()

        for query in queries:
            try:
                results = self._search(query, limit=5)
            except Exception as exc:
                all_limitations.append(f"Query '{query}' failed: {exc}")
                continue

            if not results:
                all_limitations.append(f"Query '{query}' returned no results.")
                continue

            # Deduplicate by URL across all query attempts
            for r in results:
                if r["url"] not in used_urls:
                    used_urls.add(r["url"])
                    all_results.append(r)

            # Stop once we have enough verified competitors
            if len(all_results) >= 5:
                break

        if not all_results:
            return _empty_search_result(
                "No competitors found across any query variant. "
                f"Tried: {', '.join(queries) if queries else 'no queries'}.",
                provider="firecrawl",
                query=builder.primary_query() or "",
            )

        return {
            "results": all_results,
            "accounts": [],
            "provider": "firecrawl",
            "query": builder.primary_query() or queries[0] if queries else "",
            "data_limitations": all_limitations if all_limitations else [],
        }

    def discover_social_accounts(
        self, company_name: str, target_url: str
    ) -> dict[str, Any]:
        if not company_name:
            return _empty_search_result(
                "No company name available for social search.",
                provider="firecrawl",
            )
        accounts: list[dict[str, str]] = []
        limitations: list[str] = []
        target_netloc = urlparse(target_url).netloc.lower()
        for platform_name, label in MAJOR_SOCIAL_PLATFORMS:
            query = f"{company_name} {label}"
            try:
                results = self._search(query, limit=3)
                for r in results:
                    url = r["url"].lower()
                    if target_netloc and target_netloc in url:
                        continue
                    if platform_name in url:
                        accounts.append({"platform": platform_name, "url": r["url"]})
                        break
            except Exception as exc:
                limitations.append(f"Social search for {platform_name} failed: {exc}")
        if not accounts:
            limitations.append("No verified social media accounts found via search.")
        return {
            "results": [],
            "accounts": accounts,
            "provider": "firecrawl",
            "query": company_name,
            "data_limitations": limitations,
        }

    def _search(self, query: str, limit: int = 5) -> list[dict[str, str]]:
        from firecrawl import FirecrawlApp

        app = FirecrawlApp(api_key=self._api_key, api_url=self._api_url)
        response = app.v2.search(query=query, limit=limit)
        results: list[dict[str, str]] = []
        web_results = getattr(response, "web", None) or []
        for item in web_results[:limit]:
            url = getattr(item, "url", None) or ""
            if url:
                results.append(
                    {
                        "title": getattr(item, "title", "") or "",
                        "url": url,
                        "snippet": getattr(item, "description", "")
                        or getattr(item, "snippet", "")
                        or "",
                    }
                )
        return results


# ── Concrete Strategy: Disabled (local-only) ───────────────────────────────


class DisabledSearchProvider(SearchProvider):
    """No-op provider for local-only mode — returns empty results cleanly."""

    @property
    def name(self) -> str:
        return "disabled"

    def discover_competitors(
        self, company_profile: dict[str, Any], target_url: str
    ) -> dict[str, Any]:
        builder = CompetitorQueryBuilder(company_profile, target_url)
        query = builder.primary_query() or ""
        return _empty_search_result(
            "Live competitor search is disabled.", query=query
        )

    def discover_social_accounts(
        self, company_name: str, target_url: str
    ) -> dict[str, Any]:
        return _empty_search_result("Live social search is disabled.")


# ── Concrete Strategy: SerpAPI ───────────────────────────────────────────────


class SerpAPISearchProvider(SearchProvider):
    """SerpAPI-powered competitor and social search.

    Free-tier friendly: no credits model, fixed-cost API calls.
    Docs: https://serpapi.com/search-api
    """

    def __init__(self, api_key: str):
        self._api_key = api_key

    @property
    def name(self) -> str:
        return "serpapi"

    def discover_competitors(
        self, company_profile: dict[str, Any], target_url: str
    ) -> dict[str, Any]:
        builder = CompetitorQueryBuilder(company_profile, target_url)
        queries = builder.build_query_set()
        all_results: list[dict[str, str]] = []
        all_limitations: list[str] = []
        used_urls: set[str] = set()

        for query in queries:
            try:
                results = self._search(query, limit=5)
            except Exception as exc:
                all_limitations.append(f"Query '{query}' failed: {exc}")
                continue

            if not results:
                all_limitations.append(f"Query '{query}' returned no results.")
                continue

            for r in results:
                if r["url"] not in used_urls:
                    used_urls.add(r["url"])
                    all_results.append(r)

            if len(all_results) >= 5:
                break

        if not all_results:
            return _empty_search_result(
                "No competitors found across any query variant. "
                f"Tried: {', '.join(queries) if queries else 'no queries'}.",
                provider="serpapi",
                query=builder.primary_query() or "",
            )

        return {
            "results": all_results,
            "accounts": [],
            "provider": "serpapi",
            "query": builder.primary_query() or queries[0] if queries else "",
            "data_limitations": all_limitations if all_limitations else [],
        }

    def discover_social_accounts(
        self, company_name: str, target_url: str
    ) -> dict[str, Any]:
        if not company_name:
            return _empty_search_result(
                "No company name available for social search.",
                provider="serpapi",
            )
        accounts: list[dict[str, str]] = []
        limitations: list[str] = []
        target_netloc = urlparse(target_url).netloc.lower()

        for platform_name, label in MAJOR_SOCIAL_PLATFORMS:
            query = f"{company_name} {label}"
            try:
                results = self._search(query, limit=3)
                for r in results:
                    url = r["url"].lower()
                    if target_netloc and target_netloc in url:
                        continue
                    if platform_name in url:
                        accounts.append({"platform": platform_name, "url": r["url"]})
                        break
            except Exception as exc:
                limitations.append(
                    f"Social search for {platform_name} failed: {exc}"
                )

        if not accounts:
            limitations.append(
                "No verified social media accounts found via search."
            )
        return {
            "results": [],
            "accounts": accounts,
            "provider": "serpapi",
            "query": company_name,
            "data_limitations": limitations,
        }

    def _search(self, query: str, limit: int = 5) -> list[dict[str, str]]:
        import urllib.request
        import urllib.parse
        import json

        params = {
            "q": query,
            "api_key": self._api_key,
            "num": limit,
            "engine": "google",
        }
        url = f"https://serpapi.com/search?{urllib.parse.urlencode(params)}"
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode())

        results: list[dict[str, str]] = []
        # SerpAPI nests organic results under search_results.organic_results
        organic = (
            data.get("search_results", {})
            .get("organic_results", [])
            if isinstance(data.get("search_results"), dict)
            else data.get("organic_results", [])
        )
        for item in organic[:limit]:
            link = item.get("link") or ""
            if link:
                results.append({
                    "title": item.get("title", "") or "",
                    "url": link,
                    "snippet": item.get("snippet", "") or "",
                })
        return results


# ── Chain of Responsibility: Fallback Provider ───────────────────────────────


class FallbackSearchProvider(SearchProvider):
    """Chain-of-Responsibility: try primary, fall back to secondary on failure.

    A "failure" is any condition that makes results unusable:
      - zero results returned
      - API error / insufficient credits
      - exception raised

    When the primary fails the fallback is tried. The fallback itself may also
    declare a fallback, making this a composable chain of N providers.

    This decouples the "which provider runs when" logic from individual
    SearchProvider implementations — adding a new fallback only requires
    adding it to the config chain, not changing any provider class.
    """

    def __init__(self, primary: SearchProvider, fallback: SearchProvider):
        self._primary = primary
        self._fallback = fallback

    @property
    def name(self) -> str:
        return f"{self._primary.name}+{self._fallback.name}"

    def _is_fallback_worthy(self, result: dict[str, Any]) -> bool:
        """Return True when the result is empty/broken enough to warrant fallback."""
        if not result.get("results") and not result.get("accounts"):
            return True
        limitations = result.get("data_limitations") or []
        for msg in limitations:
            lower = msg.lower()
            # Treat billing / API errors as fallback triggers
            if any(
                kw in lower
                for kw in (
                    "insufficient credits",
                    "payment required",
                    "api error",
                    "rate limit",
                    "unauthorized",
                    "timeout",
                )
            ):
                return True
        return False

    def discover_competitors(
        self, company_profile: dict[str, Any], target_url: str
    ) -> dict[str, Any]:
        primary_result = self._primary.discover_competitors(
            company_profile, target_url
        )
        if not self._is_fallback_worthy(primary_result):
            return primary_result

        fallback_result = self._fallback.discover_competitors(
            company_profile, target_url
        )
        # Merge limitations from both, primary first
        merged_limitations = (
            (primary_result.get("data_limitations") or [])
            + (fallback_result.get("data_limitations") or [])
        )
        fallback_result["data_limitations"] = merged_limitations
        fallback_result["provider"] = f"{self._primary.name}+{self._fallback.name}"
        return fallback_result

    def discover_social_accounts(
        self, company_name: str, target_url: str
    ) -> dict[str, Any]:
        primary_result = self._primary.discover_social_accounts(
            company_name, target_url
        )
        if not self._is_fallback_worthy(primary_result):
            return primary_result

        fallback_result = self._fallback.discover_social_accounts(
            company_name, target_url
        )
        merged_limitations = (
            (primary_result.get("data_limitations") or [])
            + (fallback_result.get("data_limitations") or [])
        )
        fallback_result["data_limitations"] = merged_limitations
        fallback_result["provider"] = f"{self._primary.name}+{self._fallback.name}"
        return fallback_result


# ── Provider Factory ───────────────────────────────────────────────────────


def _is_missing_api_key(api_key: str) -> bool:
    return not api_key or api_key.startswith("${")


def get_search_provider(config: dict[str, Any] | None = None) -> SearchProvider:
    """Factory: select and instantiate the right SearchProvider from config.

    Reads config['search'] to determine the active provider. Falls back to
    DisabledSearchProvider if search is not enabled or the API key is missing.

    This is the single point of change when adding a new search backend.
    """
    if config is None:
        from core.settings import load_config

        config = load_config()

    search_cfg = config.get("search", {})
    if not search_cfg.get("enabled", False):
        return DisabledSearchProvider()

    provider_name = search_cfg.get("provider", "firecrawl")

    if provider_name == "firecrawl":
        firecrawl_cfg = search_cfg.get("firecrawl", {})
        api_key = firecrawl_cfg.get("api_key") or ""
        api_url = firecrawl_cfg.get("api_url") or "https://api.firecrawl.dev"
        if _is_missing_api_key(api_key):
            return DisabledSearchProvider()
        primary: SearchProvider = FirecrawlSearchProvider(
            api_key=api_key, api_url=api_url
        )
        # Check if a fallback is configured for this provider
        fallback_chains = search_cfg.get("fallback_chains", {})
        fallback_names = fallback_chains.get("firecrawl", [])
        fallback_provider: SearchProvider | None = None
        for fb_name in fallback_names:
            fb = _build_individual_provider(search_cfg, fb_name)
            if fb is not None:
                if fallback_provider is None:
                    fallback_provider = fb
                else:
                    fallback_provider = FallbackSearchProvider(fallback_provider, fb)
        if fallback_provider is not None:
            return FallbackSearchProvider(primary, fallback_provider)
        return primary

    if provider_name == "serpapi":
        serpapi_cfg = search_cfg.get("serpapi", {})
        api_key = serpapi_cfg.get("api_key") or ""
        if _is_missing_api_key(api_key):
            return DisabledSearchProvider()
        return SerpAPISearchProvider(api_key=api_key)

    # Unknown provider — fall back to disabled
    return DisabledSearchProvider()


def _build_individual_provider(
    search_cfg: dict[str, Any], provider_name: str
) -> SearchProvider | None:
    """Instantiate a single named provider without fallback chaining."""
    if provider_name == "firecrawl":
        firecrawl_cfg = search_cfg.get("firecrawl", {})
        api_key = firecrawl_cfg.get("api_key") or ""
        api_url = firecrawl_cfg.get("api_url") or "https://api.firecrawl.dev"
        if _is_missing_api_key(api_key):
            return None
        return FirecrawlSearchProvider(api_key=api_key, api_url=api_url)
    if provider_name == "serpapi":
        serpapi_cfg = search_cfg.get("serpapi", {})
        api_key = serpapi_cfg.get("api_key") or ""
        if _is_missing_api_key(api_key):
            return None
        return SerpAPISearchProvider(api_key=api_key)
    return None
