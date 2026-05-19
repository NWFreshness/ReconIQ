# Design Patterns — Streamlit Removal

## Overview

Streamlit was removed from the project. It had been superseded by the Next.js frontend. The removal required updating documentation, tests, and dependencies.

---

## What Changed

### 1. Removed: `app.py` (365 lines)

**Old code:** A full Streamlit application with URL input forms, module toggles, provider selection, and a results display. It called the FastAPI backend directly.

**New code:** File deleted entirely. The Next.js frontend at `web/src/app/page.tsx` handles all UI.

**Why:** The Next.js frontend is the primary UI. Streamlit was pre-existing scaffolding that had never been removed, despite Next.js being the production frontend. Maintaining two UIs was redundant and caused confusion about which one to run.

---

### 2. Removed: `.streamlit/` directory

**Old code:** A directory containing:
- `.streamlit/config.toml` — Streamlit theme configuration (dark mode, font settings)
- `.streamlit/style.css` — Custom CSS design system (card styles, color tokens)

**New code:** Directory deleted.

**Why:** These were Streamlit-specific UI assets. The Next.js frontend uses its own design system defined in `DESIGN.md` and implemented in Tailwind CSS within `web/`.

---

### 3. Removed: `tests/test_streamlit_ui.py`

**Old code:** Playwright-based end-to-end test that launched Streamlit, navigated to it, and verified the page loaded.

**New code:** File deleted.

**Why:** The test was a UI smoke test for a UI that no longer exists. Next.js has its own integration tests in the `web/` directory.

---

### 4. Updated: `requirements.txt`

**Old code:**
```
streamlit>=1.40.0
```

**New code:** Line removed entirely.

**Why:** Streamlit was the only consumer of this dependency. The Python backend (FastAPI), scraper, and research modules do not depend on it.

---

### 5. Updated: `README.md`

**Old code:**
```markdown
### Mode 2: Streamlit standalone (port 8501)

```bash
.venv/bin/streamlit run app.py --server.port 8501 --server.headless true
```

Open [http://localhost:8501](http://localhost:8501).

### Mode 3: CLI
```

**New code:**
```markdown
### Mode 2: CLI
```

**Also removed** the `.streamlit/` entry from the project tree listing.

**Why:** The README was documenting how to run a UI that no longer exists.

---

### 6. Updated: `FEATURE_PHASES.md`

**Old code:**
```markdown
- `DESIGN.md`
- `.streamlit/style.css` if Streamlit remains supported
```

**New code:** The `.streamlit/style.css` line removed.

**Why:** The file no longer exists, so the conditional reference is outdated.

---

### 7. Updated: `tests/test_app.py`

**Old code:**
```python
"""Tests for Streamlit app helpers and wiring."""
from app import build_analysis_request, normalize_url, validate_url
```

**New code:**
```python
"""Tests for URL normalization helpers."""
from scraper.scraper import normalize_url
```

**Why:** The test file was named for Streamlit but tested URL helpers (`normalize_url`) that live in `scraper/scraper.py`. The `validate_url` and `build_analysis_request` functions were Streamlit-only helpers defined in `app.py` — they no longer exist and the tests for them were removed. The `normalize_url` tests were preserved, pointing at the actual implementation.

---

## Summary of Files Deleted

| File | Lines | Reason |
|------|-------|--------|
| `app.py` | 365 | Entire Streamlit UI deleted |
| `.streamlit/config.toml` | ~25 | Streamlit-specific config |
| `.streamlit/style.css` | ~60 | Streamlit-specific CSS |
| `tests/test_streamlit_ui.py` | ~50 | Playwright test for deleted UI |
| `tests/test_app.py` (old) | 114 | Replaced with cleaned version |

## Summary of Files Modified

| File | Change |
|------|--------|
| `requirements.txt` | Removed `streamlit>=1.40.0` |
| `README.md` | Removed Streamlit run instructions and directory listing |
| `FEATURE_PHASES.md` | Removed `.streamlit/style.css` reference |
| `tests/test_app.py` | Removed Streamlit-only tests, preserved `normalize_url` tests |

---

## Design Principles Applied

Following Karpathy Guidelines and Zen of Python:

1. **Surgical changes only** — Every edit traces directly to the removal of Streamlit. No adjacent code touched.

2. **No orphaned references** — All documentation and tests that referenced Streamlit were updated in the same pass.

3. **One obvious way** — The codebase now has one frontend (Next.js). No ambiguity about which UI to run.

4. **Explicit over implicit** — Tests that were misnamed ("test_app.py" testing Streamlit helpers from `app`) were corrected to import from the actual source (`scraper/scraper.py`).

5. **Flat over nested** — Removed a layer of indirection (Streamlit as a second UI) that added complexity without adding value.

---

## Report UI Improvements

Three new React components were added to render structured research data with readable layouts instead of raw JSON dumps.

### Components Added

#### `CompanyProfileCard` — `web/src/components/report/CompanyProfileCard.tsx`

Renders `company_profile` module output as a structured card with named fields, tag lists, and data limitations.

**Old code (default rendering):**
```tsx
<pre>{JSON.stringify(value, null, 2)}</pre>
```

**New code:**
```tsx
<CompanyProfileCard data={data} />
```

Renders: company name, what they do, target audience, value proposition, brand voice, CTA, services/products as tags, marketing channels as tags, service area, location, and data limitations — all with appropriate icons and spacing.

**Design rationale:** Company profile data is the anchor of the entire report. Rendering it as plain JSON buried years of structured intelligence under an opaque blob. The card surfaces the most important fields first using the same surface/border/accent system as the rest of the UI. Following the Zen of Python principle of "explicit over implicit" — each field is labelled rather than rendered as an anonymous key-value pair.

---

#### `SEOKeywordsCard` — `web/src/components/report/SEOKeywordsCard.tsx`

Renders `seo_keywords` module output with colour-coded tag groups.

**Old code (chart-only, no card):**
```tsx
<ContentGapChart items={[...gaps, ...weaknesses]} />
```

**New code:**
```tsx
<SEOKeywordsCard data={data} />
```

Renders: top keywords (accent tags), quick wins (emerald tags), content gaps (yellow tags), SEO weaknesses (yellow tags), local SEO signals as text, and data limitations — with a dedicated card. The chart was removed because it was a synthetic bar chart derived from keyword index positions (arbitrary values), not actual data. The keywords themselves are the signal; the chart was noise.

**Design rationale:** Keywords are inherently a list, not a chart. Tags communicate "these are the keywords" more clearly than bars. Quick wins get a distinct emerald colour to make them visually scannable. SEO weaknesses and content gaps share a yellow category to show they're related findings.

---

#### `SocialContentCard` — `web/src/components/report/SocialContentCard.tsx`

Renders `social_content` module output with verified accounts, platform tags, and engagement signals.

**Old code (default rendering):**
```tsx
<pre>{JSON.stringify(value, null, 2)}</pre>
```

**New code:**
```tsx
<SocialContentCard data={data} />
```

Renders: active platforms as tags, verified social accounts as linked platform names, inferred platforms as muted tags, content quality/frequency/engagement as a signal table, review sites, blog/resources, content gaps as a list, email signals, and data limitations.

**Design rationale:** Social content has many sub-fields of varying types (platform lists, account objects, free text, string lists). The card groups related fields and uses icons to visually differentiate categories. Verified accounts are rendered as real links so the user can click through to check them.

---

### `analysis/[id]/page.tsx` — Updated

**Old code:** All three modules (`company_profile`, `social_content`, `seo_keywords`) fell through to the default raw-JSON renderer:
```tsx
<pre>{JSON.stringify(value, null, 2)}</pre>
```

**New code:** Each module now routes to its dedicated card:
```tsx
if (key === "company_profile") {
  return <CompanyProfileCard data={...} />;
}
if (key === "social_content") {
  return <SocialContentCard data={...} />;
}
if (key === "seo_keywords") {
  return <SEOKeywordsCard data={...} />;
}
```

All three cards are exported from `web/src/components/report/index.ts`.

---

### Error Display Fix

Fixed a TypeScript type error in the error display path. The old code used a type assertion that was too narrow for all error shapes:
```tsx
// Old — TypeScript error
{(value as Record<string, string>).error}

// New — handles any error shape
String((value as Record<string, unknown>).error || "Unknown error")
```

---

## Competitor Search Improvements

The competitor search was returning empty results too often. The root cause was a single, under-specified query string.

### Problem: `_build_competitor_query()` (old)

**Old code (`search_provider.py`):**
```python
def _build_competitor_query(company_profile, target_url):
    domain = urlparse(target_url).netloc.replace("www.", "") or target_url
    parts = []
    city = company_profile.get("location_city", "")
    state = company_profile.get("location_state", "")
    if city and state:
        parts.append(f"{city} {state}")
    elif city:
        parts.append(city)
    for item in company_profile.get("services_products", [])[:3]:
        parts.append(str(item))
    name = company_profile.get("company_name", "")
    if name:
        parts.append(f"companies like {name}")
    if not parts:
        parts = [str(company_profile.get("company_name") or domain), "competitors"]
    return " ".join(part for part in parts if part).strip()
```

**Failure modes:**
1. No industry signal — "companies like Acme" doesn't tell the search engine what type of business. Results were dominated by national brands and Wikipedia pages.
2. No location narrowing — without a location term, searches return global results, not local competitors.
3. Single query — if the query returned nothing, the competitor module had no fallback and returned empty results.

### Solution: `CompetitorQueryBuilder` (`research/competitor_query.py`)

A new class that extracts four independent signals from `company_profile` and builds five prioritized query variants:

**New code — signal extraction:**
```python
def _extract_industry_signals(profile):
    signals = []
    if profile.get("what_they_do"):
        signals.append(profile["what_they_do"])
    if profile.get("target_audience"):
        signals.append(profile["target_audience"])
    for svc in profile.get("services_products", []):
        if svc and len(svc) > 2:
            signals.append(svc)
    return signals

def _extract_location_signals(profile):
    signals = []
    city = profile.get("location_city", "")
    state = profile.get("location_state", "")
    service_area = profile.get("service_area", [])
    if city and state:
        signals.append(f"{city} {state}")
    # ... service_area and zip code
    return signals
```

**Five query strategies — prioritized fallback chain:**
```python
# 1. Industry + location — "hvac contractor Seattle WA"
q = _build_industry_location_query(industry_signals, location_signals)
# 2. Specific services + location — "SEO agency, web design Portland OR"
q2 = _build_service_location_query(service_terms, location_signals)
# 3. "Companies like X" with industry context
q3 = _build_name_plus_competitors_query(name, industry_signals, location_signals)
# 4. Directory-style — "top seo agencies in Portland OR"
q4 = _build_vertical_directory_query(industry_signals, location_signals)
# 5. Industry only — last resort
q5 = _build_broader_industry_query(industry_signals)
```

**New code — `FirecrawlSearchProvider.discover_competitors()`:**
```python
builder = CompetitorQueryBuilder(company_profile, target_url)
queries = builder.build_query_set()
all_results = []
used_urls = set()

for query in queries:
    results = self._search(query, limit=5)
    # Deduplicate by URL across all query attempts
    for r in results:
        if r["url"] not in used_urls:
            used_urls.add(r["url"])
            all_results.append(r)
    if len(all_results) >= 5:
        break

if not all_results:
    return _empty_search_result(
        "No competitors found across any query variant. "
        f"Tried: {', '.join(queries)}.",
        query=builder.primary_query(),
    )
```

**Design patterns applied:**

1. **Strategy Pattern** — `_build_industry_location_query()`, `_build_service_location_query()`, etc. are encapsulated query-building strategies. The `CompetitorQueryBuilder.build_query_set()` method combines them without needing to know the internals of each strategy. Adding a new query variant is a matter of adding one function and registering it in `build_query_set()`.

2. **Builder Pattern** — Signals are accumulated lazily via `@property` accessors (`industry_signals`, `location_signals`, etc.) and only assembled into queries when `build_query_set()` is called. This allows the caller to inspect individual signals or the full query set without recomputing.

3. **Template Method** — `build_query_set()` defines a fixed ordering (most specific → least specific) that callers rely on. Subclasses or extensions can override the query list without changing the calling code.

**Files added:**
- `research/competitor_query.py` — `CompetitorQueryBuilder` class + all query strategy functions + `_build_competitor_query()` backward-compat wrapper
- `tests/test_competitor_query.py` — 23 tests covering signal extraction, query strategies, and integration

**Files modified:**
- `research/search_provider.py` — `FirecrawlSearchProvider.discover_competitors()` now tries multiple queries with deduplication
- `tests/test_research_modules.py` — `COMPETITOR_RESULT` data_limitations updated to match new error message

**Why this is better for local business intelligence:**
A local HVAC contractor in Vancouver WA searching for "companies like Acme" gets HVAC companies from the entire Pacific Northwest, not just competitors serving the same geographic area. The new query "hvac contractor Vancouver WA" returns only companies actually serving that market. The five-variant fallback chain means that even if the primary query is too narrow (e.g., a very specific niche service), the fourth or fifth variant will still return relevant local competitors.

---

## 6. Added: SerpAPI Search Provider + Chain of Responsibility Fallback

**Problem:** `FirecrawlSearchProvider` ran out of credits during competitor search, returning an empty array with `"Insufficient credits to perform this request"`. The entire competitor module failed because there was no fallback — one provider, one shot.

**Solution:** Added `SerpAPISearchProvider` as a free-search alternative and wrapped it in a `FallbackSearchProvider` chain so that when Firecrawl fails for any reason (credits, rate limits, errors), SerpAPI is tried automatically.

---

### 6a. New: `SerpAPISearchProvider`

A new concrete Strategy implementing the `SearchProvider` interface, calling the SerpAPI REST endpoint directly with no external library dependency.

**Old code:** No SerpAPI provider existed.

**New code:**
```python
class SerpAPISearchProvider(SearchProvider):
    def __init__(self, api_key: str):
        self._api_key = api_key

    @property
    def name(self) -> str:
        return "serpapi"

    def _search(self, query: str, limit: int = 5) -> list[dict[str, str]]:
        import urllib.request, urllib.parse, json
        params = {"q": query, "api_key": self._api_key, "num": limit, "engine": "google"}
        url = f"https://serpapi.com/search?{urllib.parse.urlencode(params)}"
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode())
        organic = (
            data.get("search_results", {}).get("organic_results", [])
            if isinstance(data.get("search_results"), dict)
            else data.get("organic_results", [])
        )
        return [
            {"title": item.get("title", "") or "", "url": item.get("link", "") or "", "snippet": item.get("snippet", "") or ""}
            for item in organic[:limit]
            if item.get("link")
        ]
```

**Why SerpAPI:** SerpAPI uses a fixed-cost model (not a credits model). $10/month gets 5,000 searches — enough for hundreds of competitor analyses. It returns real Google results including local map listings, which is exactly what local business competitor discovery needs. It is also fallback-friendly: any API error or empty result triggers the next provider in the chain.

---

### 6b. New: `FallbackSearchProvider` (Chain of Responsibility)

A composite `SearchProvider` that tries a primary, then a fallback on failure. Failures that trigger fallback include: zero results, billing errors, rate limits, or API errors.

**Old code:** Single-provider dispatch in `get_search_provider()` with no fallback.

```python
# Old factory — one shot only
if provider_name == "firecrawl":
    if _is_missing_api_key(api_key):
        return DisabledSearchProvider()
    return FirecrawlSearchProvider(api_key=api_key, api_url=api_url)
return DisabledSearchProvider()
```

**New code:**
```python
class FallbackSearchProvider(SearchProvider):
    def __init__(self, primary: SearchProvider, fallback: SearchProvider):
        self._primary = primary
        self._fallback = fallback

    def _is_fallback_worthy(self, result: dict[str, Any]) -> bool:
        if not result.get("results") and not result.get("accounts"):
            return True
        for msg in result.get("data_limitations") or []:
            lower = msg.lower()
            if any(kw in lower for kw in (
                "insufficient credits", "payment required",
                "api error", "rate limit", "unauthorized", "timeout",
            )):
                return True
        return False

    def discover_competitors(self, company_profile, target_url):
        primary_result = self._primary.discover_competitors(company_profile, target_url)
        if not self._is_fallback_worthy(primary_result):
            return primary_result
        fallback_result = self._fallback.discover_competitors(company_profile, target_url)
        fallback_result["data_limitations"] = (
            (primary_result.get("data_limitations") or [])
            + (fallback_result.get("data_limitations") or [])
        )
        fallback_result["provider"] = f"{self._primary.name}+{self._fallback.name}"
        return fallback_result
```

---

### 6c. Updated: `config.yaml` — fallback chain declaration

**Old code:**
```yaml
search:
  enabled: true
  provider: "firecrawl"
  firecrawl:
    api_key: "${FIRECRAWL_API_KEY}"
```

**New code:**
```yaml
search:
  enabled: true
  provider: "firecrawl"
  firecrawl:
    api_url: "https://api.firecrawl.dev"
    api_key: "${FIRECRAWL_API_KEY}"
  serpapi:
    api_key: "${SERPAPI_API_KEY}"
  fallback_chains:
    firecrawl:
      - serpapi
```

---

### 6d. Updated: `.env` and `.env.example`

Added `SERPAPI_API_KEY=` to both files so users can fill in their key without editing config.

---

### Design patterns applied

1. **Strategy Pattern** — `SerpAPISearchProvider` is a pluggable backend identical in interface to `FirecrawlSearchProvider`. The `get_search_provider()` factory decides which one to instantiate based on config. Adding a new backend (Bing, DuckDuckGo) requires only adding the class and a branch in the factory — no caller changes.

2. **Chain of Responsibility** — `FallbackSearchProvider` wraps a primary and a fallback. When the primary fails, the request propagates to the fallback. The chain is composable: `FallbackSearchProvider(Firecrawl, FallbackSearchProvider(SerpAPI, DuckDuckGo))` would work if three providers were configured. The trigger condition (`_is_fallback_worthy`) is centralized in one place, not scattered across provider classes.

3. **Factory Pattern** — `get_search_provider()` is a centralized factory that reads config and constructs the correct object graph. Callers (`run_all`, `competitors.py`, `social_content.py`) never instantiate providers directly — they call `get_search_provider(config)` and get back a fully-wired provider or chain.

**Files added:**
- `tests/test_search_provider.py` — 22 tests for SerpAPI provider and fallback chain

**Files modified:**
- `research/search_provider.py` — added `SerpAPISearchProvider`, `FallbackSearchProvider`, updated `get_search_provider()` factory
- `research/search.py` — re-exports new provider classes
- `config.yaml` — added `serpapi` section and `fallback_chains` configuration
- `.env` and `.env.example` — added `SERPAPI_API_KEY` field

---

*Generated after Streamlit removal from ReconIQ.*