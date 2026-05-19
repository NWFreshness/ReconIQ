"""Query builder for competitor search.

Problem: The previous _build_competitor_query() was a single flat function that
built one query string. It had three failure modes:

  1. Empty fallback — when company_profile had no services_products or location,
     it fell back to "{name} competitors" which is too vague for local businesses.
  2. No industry signal — "companies like Acme" doesn't tell the search engine
     WHAT kind of companies. Acme could be a restaurant, a SaaS, or a law firm.
  3. No location narrowing — a search without location returns national brands
     and Wikipedia pages, not local competitors.

Solution: A CompetitorQueryBuilder class that:

  1. Extracts four independent signals from company_profile:
       - industry (from what_they_do, target_audience, services_products)
       - location (from location_city, location_state, service_area)
       - company name
       - service keywords
  2. Builds multiple query variants (Strategy Pattern) so if the primary query
     returns nothing, alternative queries can be tried without re-scraping.
  3. Uses a prioritized fallback chain instead of a single query.

Design patterns used:
  - Strategy: query construction strategies are encapsulated in methods that
    can be swapped or combined. The caller doesn't need to know which variant works.
  - Builder: signals are accumulated incrementally, with the final query assembled
    only when all signals have been collected.
  - Template Method: build_query_set() defines the ordering; callers can override
    or extend the strategy list without rewriting the assembly logic.

Usage:
    builder = CompetitorQueryBuilder(company_profile, target_url)
    queries = builder.build_query_set()   # returns all variants, primary first
    for query in queries:
        results = provider.discover_competitors(query=query)
        if results:
            return results  # use the first that returns results
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse


# ── Signal extraction helpers ───────────────────────────────────────────────


def _extract_industry_signals(profile: dict[str, Any]) -> list[str]:
    """Pull all text that describes the industry or business type."""
    signals: list[str] = []

    # Direct industry description — highest priority
    if profile.get("what_they_do"):
        signals.append(profile["what_they_do"])

    # Target audience often contains the vertical (e.g. "dental practices")
    if profile.get("target_audience"):
        signals.append(profile["target_audience"])

    # Services/products are the clearest industry indicator
    for svc in profile.get("services_products", []):
        if svc and len(svc) > 2:
            signals.append(svc)

    return signals


def _extract_location_signals(profile: dict[str, Any]) -> list[str]:
    """Pull all location variants from the profile.

    Handles two schemas:
      - Flat:  {"location_city": "Ridgefield", "location_state": "WA", ...}
      - Nested: {"location": {"city": "Ridgefield", "state": "WA", ...}}
    """
    # Resolve whichever schema is present
    loc = profile.get("location", {})
    if not isinstance(loc, dict):
        loc = {}
    city = loc.get("city", "") or profile.get("location_city", "") or ""
    state = loc.get("state", "") or profile.get("location_state", "") or ""
    service_area = loc.get("service_area", []) or profile.get("service_area", []) or []
    zip_code = loc.get("zip", "") or profile.get("location_zip", "") or ""

    signals: list[str] = []
    if city and state:
        signals.append(f"{city} {state}")
    elif city:
        signals.append(city)

    if service_area:
        # Build the full city+state string for proper deduplication
        city_state = f"{city} {state}" if (city and state) else (city or "")
        for area in service_area:
            if not area:
                continue
            # Skip items that match city or city+state exactly (avoid dupes)
            if area == city or area == city_state:
                continue
            if state:
                signals.append(f"{area}, {state}")
            else:
                signals.append(area)

    if zip_code:
        signals.append(zip_code)

    return signals


def _company_name(profile: dict[str, Any]) -> str:
    return profile.get("company_name", "") or ""


def _domain_name_from_url(target_url: str) -> str:
    parsed = urlparse(target_url)
    return parsed.netloc.replace("www.", "") or target_url


# ── Backward-compatible query builder (single query) ───────────────────────


def _build_competitor_query(
    company_profile: dict[str, Any], target_url: str
) -> str:
    """Build a single best-effort competitor query string from company profile data.

    This is a backward-compatibility wrapper around CompetitorQueryBuilder.
    New code should use CompetitorQueryBuilder.build_query_set() directly to
    get multiple query variants with fallback support.
    """
    builder = CompetitorQueryBuilder(company_profile, target_url)
    return builder.primary_query() or ""


# ── Individual query strategy functions ─────────────────────────────────────


def _build_industry_location_query(
    industry_signals: list[str],
    location_signals: list[str],
    max_industry_terms: int = 2,
) -> str | None:
    """Primary query: industry terms + location together.

    This is the strongest signal for local competitor discovery. Example:
    "hvac contractor Seattle WA" returns local HVAC companies, not Wikipedia.

    Returns None if either signal is missing.
    """
    industry_terms = [t.strip() for t in industry_signals[:max_industry_terms] if t.strip()]
    location = location_signals[0] if location_signals else None

    if not industry_terms or not location:
        return None

    return f"{', '.join(industry_terms[:2])} {location}"


def _build_service_location_query(
    service_terms: list[str],
    location_signals: list[str],
) -> str | None:
    """Fallback: specific services + location, no general industry term.

    For when what_they_do is vague but services_products is specific.
    Example: "SEO agency, web design Vancouver WA"
    """
    location = location_signals[0] if location_signals else None
    if not service_terms or not location:
        return None

    services = ", ".join(service_terms[:2])
    return f"{services} {location}"


def _build_name_plus_competitors_query(
    company_name: str,
    industry_signals: list[str],
    location_signals: list[str],
) -> str | None:
    """Try to find competitors of the target company using "companies like X".

    Works well for named companies with an established market position.
    We add industry context so the search engine doesn't interpret "companies
    like Acme" as literally just the company named Acme.
    """
    if not company_name:
        return None
    parts = [f"companies like {company_name}"]
    if industry_signals:
        parts.append(industry_signals[0])
    if location_signals:
        parts.append(location_signals[0])
    return " ".join(parts)


def _build_vertical_directory_query(
    industry_signals: list[str],
    location_signals: list[str],
) -> str | None:
    """Directory/listing style query: "top [industry] in [location]".

    Good when the company offers a common service in a local market where
    there are likely directory listings or "best of" roundups.
    Example: "top seo agencies in Portland OR"
    """
    industry = industry_signals[0] if industry_signals else None
    location = location_signals[0] if location_signals else None
    if not industry or not location:
        return None
    return f"top {industry} in {location}"


def _build_broader_industry_query(industry_signals: list[str]) -> str | None:
    """Last resort: industry term without location.

    Returns national/regional players. Better than returning no results.
    """
    if not industry_signals:
        return None
    return industry_signals[0]


# ── Main builder class ──────────────────────────────────────────────────────


class CompetitorQueryBuilder:
    """Builds a prioritized set of competitor search queries from company profile data.

    The builder extracts independent signals (industry, location, name, services)
    and combines them into multiple query variants. The first query in the set
    is the most specific; each subsequent query relaxes one constraint.

    Callers should try queries in order and use the first that returns results.

    Attributes:
        profile: The company_profile dict from the research pipeline.
        target_url: The URL of the target company.
    """

    def __init__(
        self,
        company_profile: dict[str, Any],
        target_url: str,
    ):
        self.profile = company_profile
        self.target_url = target_url

        self._industry_signals: list[str] | None = None
        self._location_signals: list[str] | None = None
        self._service_terms: list[str] | None = None
        self._name: str | None = None
        self._domain_name: str | None = None

    # ── Lazy signal extraction ──────────────────────────────────────────────

    @property
    def industry_signals(self) -> list[str]:
        if self._industry_signals is None:
            self._industry_signals = _extract_industry_signals(self.profile)
        return self._industry_signals

    @property
    def location_signals(self) -> list[str]:
        if self._location_signals is None:
            self._location_signals = _extract_location_signals(self.profile)
        return self._location_signals

    @property
    def service_terms(self) -> list[str]:
        """Service/product keywords — a subset of industry signals, more specific."""
        if self._service_terms is None:
            self._service_terms = [
                s for s in self.profile.get("services_products", []) if s and len(s) > 2
            ]
        return self._service_terms

    @property
    def name(self) -> str:
        if self._name is None:
            self._name = _company_name(self.profile)
        return self._name

    @property
    def domain_name(self) -> str:
        if self._domain_name is None:
            self._domain_name = _domain_name_from_url(self.target_url)
        return self._domain_name

    @property
    def has_location(self) -> bool:
        return bool(self.location_signals)

    @property
    def has_industry(self) -> bool:
        return bool(self.industry_signals)

    # ── Query assembly ─────────────────────────────────────────────────────

    def build_query_set(self) -> list[str]:
        """Return all query variants, ordered by priority.

        The first query is the most specific (highest intent signal + location).
        Later queries progressively relax constraints.

        Returns an empty list only if no meaningful signal can be extracted.
        """
        queries: list[str] = []

        # 1. Industry + location — strongest local competitor signal
        q = _build_industry_location_query(self.industry_signals, self.location_signals)
        if q:
            queries.append(q)

        # 2. Specific services + location — for when what_they_do is vague
        q2 = _build_service_location_query(self.service_terms, self.location_signals)
        if q2 and q2 not in queries:
            queries.append(q2)

        # 3. "Companies like X" with industry context
        q3 = _build_name_plus_competitors_query(
            self.name, self.industry_signals, self.location_signals
        )
        if q3 and q3 not in queries:
            queries.append(q3)

        # 4. Directory-style: "top [industry] in [location]"
        q4 = _build_vertical_directory_query(self.industry_signals, self.location_signals)
        if q4 and q4 not in queries:
            queries.append(q4)

        # 5. Broader industry without location — last resort
        q5 = _build_broader_industry_query(self.industry_signals)
        if q5 and q5 not in queries:
            queries.append(q5)

        return queries

    def primary_query(self) -> str | None:
        """Return the single best query, or None if no signal exists."""
        queries = self.build_query_set()
        return queries[0] if queries else None