# ReconIQ Enhancement Roadmap

> **For Hermes:** This is the durable tracker for post-MVP enhancements. Do not start these until Phases 0-8 are complete and merged to main. Work one sub-phase at a time with the user. Update this file when a sub-phase changes state.

**Prerequisites:** All MVP phases (0-8) merged to main. `uv run python -m pytest -q` should pass before starting any enhancement.

---

## Enhancement Status and Source of Truth

Update rules for future agents/models:
1. Before starting an enhancement, confirm the previous enhancement status here.
2. Mark a phase `[x]` only after code is implemented, committed, pushed, and merged or opened as a PR with passing local verification.
3. If a PR is open, keep checkbox checked when local verification passed and record `Status: PR open`.
4. Record PR URL, branch, latest commit, and local verification summary.
5. If an enhancement needs follow-up after review, revert status and add a note.
6. Do not rely only on chat history; this file is the project-level progress tracker for enhancements.

---

## Sub-Phase 9A: Production Web App Migration Path

**Goal:** Convert the MVP architecture into a production-grade web app without rewriting the research engine.

**Status:** Complete — merged to main.

**Branch:** `feat/phase-9a-fastapi`

**Files Created:**
- `api/main.py` — FastAPI app with CORS, health check
- `api/schemas.py` — Pydantic request/response models
- `api/db.py` — SQLite persistence layer with SQLAlchemy
- `api/auth.py` — API key authentication
- `api/worker.py` — background analysis runner
- `api/routes/analyses.py` — POST/GET analysis endpoints
- `api/routes/reports.py` — report download endpoint
- `tests/test_api.py` — 17 API tests

**Endpoints:**
- `POST /analyses` — create analysis job (returns 202 Accepted)
- `GET /analyses` — list recent analyses
- `GET /analyses/{id}` — get analysis status
- `GET /analyses/{id}/results` — get analysis results
- `GET /reports/{id}` — download report file
- `GET /health` — health check

**Verification:**
- `240 passed`; API tests pass; Playwright UI test passes.

### Recommended Future Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI |
| Frontend | Next.js or React |
| Database | Postgres |
| Job Queue | Celery / RQ / Arq / Dramatiq |
| Cache | Redis |
| File Storage | S3-compatible |
| Auth | Clerk / Auth0 / Supabase Auth |
| Deployment | Docker + Render / Fly.io / Railway |
| Observability | Structured logs, error tracking, metrics |

### Future File Structure

```text
api/
  main.py
  routes/
    analyses.py
    reports.py
  dependencies.py
  schemas.py
workers/
  analysis_worker.py
web/
  <frontend app>
core/
research/
llm/
scraper/
report/
```

### Migration Strategy

1. Keep `core.services.run_analysis()` as the canonical entry point.
2. Add `api/main.py` with a FastAPI app.
3. Add `POST /analyses` to validate input and enqueue a background job.
4. Add `GET /analyses/{id}` for status polling.
5. Add `GET /reports/{id}` for report retrieval.
6. Move long-running LLM work out of request/response into a worker.
7. Store analysis status, metadata, and report paths in Postgres.
8. Store report files in S3-compatible object storage.
9. Add user accounts and per-user report ownership.
10. Add rate limits, cost controls, provider quotas, and audit logs.

### Design Requirements Already Preserved

- No Streamlit imports outside `app.py`.
- No direct filesystem assumptions inside research modules.
- No UI state inside coordinator.
- No provider secrets passed through frontend-visible data.
- Report generation accepts structured results and returns a path or storage handle.
- Coordinator progress events are serializable.

---

## Sub-Phase 9B: Playwright JS Rendering

**Goal:** Add fallback scraping for JS-heavy sites that `requests + BeautifulSoup` cannot handle.

**Status:** Complete — merged to main.

**Branch:** `feat/phase-9b-playwright`

**Local verification:** `108 passed`; focused Playwright checks `10 passed`; compile check passed; `git diff --check` passed.

**PR:** Merged.

### Files to Modify

- `requirements.txt` — add `playwright>=1.40.0`
- `scraper/scraper.py` — add Playwright fallback path
- `tests/test_scraper.py` — add Playwright tests

### Implementation Plan

1. Install Playwright: `uv pip install playwright`
2. Download browser: `uv run python -m playwright install chromium`
3. Add `scrape_with_playwright(url, timeout)` function.
4. Modify `scrape()` to try `requests` first, fall back to Playwright on empty result or explicit `js_render=True` flag.
5. Keep Playwright off the critical path — only use when `requests` returns empty or insufficient text.
6. Add config toggle: `scraper.use_playwright_fallback: true/false` in `config.yaml`.

### Verification Checklist

- [ ] `scrape()` returns non-empty text from a known JS-rendered site.
- [ ] Playwright path only triggers when enabled and requests fails.
- [ ] No Playwright dependency imported at module load time (lazy import).
- [ ] Tests mock Playwright if not installed.
- [ ] Full test suite still passes.

---

## Sub-Phase 9C: Better Competitor Discovery

**Goal:** Use live search APIs instead of pure LLM inference for competitor data.

**Status:** Complete — merged to main. Brave Search API support added with graceful fallback when disabled or unconfigured.

**Branch:** `feat/phase-9j3-9c-9d-9e-integration`

**Files Created:**
- `research/search.py` — Brave Search wrapper with fallback/no-op behavior

**Files Modified:**
- `research/competitors.py` — integrates live search results into prompt and labels scraped vs inferred competitors

### Possible Tools

| Service | Notes |
|---------|-------|
| SerpAPI | Google search results API |
| Tavily | Search API built for AI apps |
| Brave Search API | Privacy-focused, generous free tier |
| Bing Web Search API | Microsoft ecosystem |

### Implementation Plan

1. Add a `research/competitor_search.py` module that wraps the chosen search API.
2. Modify `research/competitors.py` to:
   - Call the search API for live competitor URLs
   - Scrape top result pages for positioning/messaging data
   - Fall back to pure LLM inference if the API is unavailable or rate-limited
3. Add API key to `.env` (e.g. `SERPAPI_API_KEY=***`).
4. Add config section: `search_api.provider` and `search_api.api_key_env`.

### Verification Checklist

- [ ] Competitor module returns real URLs when search API is available.
- [ ] Graceful fallback to LLM-only when API key is missing or rate-limited.
- [ ] Data limitations clearly label live vs. inferred competitor data.

---

## Sub-Phase 9D: Pydantic Schemas

**Goal:** Replace lightweight JSON validation with typed Pydantic schemas for stronger guarantees and IDE support.

**Status:** Complete — merged to main.

**Branch:** `feat/phase-9j3-9c-9d-9e-integration`

**Files Created:**
- `research/schemas.py` — Pydantic v2 models for all module outputs

**Files Modified:**
- All `research/*.py` modules validate via `validate_module_output()` and return plain dicts for backward compatibility
- `requirements.txt` — added `pydantic>=2.0.0`

### Files to Create / Modify

- Create: `research/schemas.py` — Pydantic models for all module outputs
- Modify: All `research/*.py` modules to return/validate against schemas
- Modify: `tests/` to use schema instances instead of raw dicts
- Modify: `core/models.py` to use Pydantic if desired

### Schema Targets

- `CompanyProfileSchema`
- `SEOKeysSchema`
- `CompetitorSchema` (with nested `CompetitorItem`)
- `SocialContentSchema`
- `SWOTSchema`

### Verification Checklist

- [ ] All module outputs pass Pydantic validation before returning.
- [ ] Invalid LLM JSON raises a clear validation error with field details.
- [ ] No performance regression in mocked tests.
- [ ] Full test suite passes.

---

## Sub-Phase 9E: Cached Runs

**Goal:** Avoid repeating expensive LLM calls for the same URL + module + prompt.

**Status:** Complete — merged to main.

**Branch:** `feat/phase-9j3-9c-9d-9e-integration`

**Files Created:**
- `llm/cache.py` — local raw-response cache with SHA256 keys

**Files Modified:**
- `llm/router.py` — reads/writes cache around provider calls
- `config.yaml` — added `llm_cache` section
- `.gitignore` — added `.reconiq-cache/`

### Files to Create / Modify

- Create: `cache/` or `.reconiq-cache/` directory (gitignored)
- Create: `research/cache.py` — cache key generation, store/load, TTL
- Modify: `research/coordinator.py` — check cache before calling modules
- Modify: `llm/router.py` — optional response caching layer

### Design

- Cache key: hash of `(target_url, module_name, prompt, provider, model)`
- Storage: JSON files on disk (simple) or SQLite (if many entries)
- TTL: 24 hours default, configurable in `config.yaml`
- Invalidation: manual clear via CLI or UI button
- Scope: cache LLM raw responses, not final parsed dicts

### Verification Checklist

- [ ] Second run for same URL returns cached results instantly.
- [ ] Cache respects TTL — expired entries trigger fresh LLM calls.
- [ ] Cache can be cleared via a function call.
- [ ] Full test suite passes (tests should use a temp cache dir).

---

## Sub-Phase 9F: Export Formats

**Goal:** Add HTML and PDF exports after Markdown is stable.

**Status:** Complete — merged to main.

**Branch:** `feat/phase-9f-9h-9i-exports-cli-batch`

**Files Modified:**
- `report/writer.py` — added `write_html_report()`, `write_pdf_report()`, and `fmt` parameter to `write_report()`
- `app.py` — added export format dropdown in sidebar
- `requirements.txt` — added `markdown` and `weasyprint`

**Verification:**
- `223 passed`; HTML and PDF export tests pass; Playwright UI test passes.

### Files to Create / Modify

- Modify: `report/writer.py` — add `write_html()` and `write_pdf()` functions
- Modify: `app.py` — add format selection in UI
- Add dependency: `markdown` (for HTML) and `weasyprint` or `pdfkit` (for PDF)

### Implementation Plan

1. `write_html(results, output_dir)`:
   - Convert Markdown report to HTML with a clean stylesheet
   - Embed company name, date, ReconIQ branding
2. `write_pdf(results, output_dir)`:
   - Convert HTML to PDF
   - Keep it simple — no complex layouts needed for v1
3. UI: add radio or dropdown in Streamlit for format selection (Markdown / HTML / PDF)

### Verification Checklist

- [ ] HTML export renders correctly in a browser.
- [ ] PDF export opens in a PDF reader with readable text.
- [ ] Markdown export continues to work unchanged.
- [ ] Full test suite passes.

---

## Sub-Phase 9G: Dark Mode / UI Polish

**Goal:** Improve the Streamlit UI beyond the MVP barebones look.

**Status:** Complete — merged to main.

**Branch:** `feat/phase-9g-ui-polish`

**Local verification:** `108 passed`; compile check passed; `git diff --check` passed.

**PR:** Merged.

### Ideas

- Custom CSS injection for dark-mode-friendly report preview
- Collapsible sections for each research module result
- Charts for SWOT (quadrant plot) or competitor comparison
- Export history sidebar — list previously generated reports

### Verification Checklist

- [ ] UI remains functional and accessible.
- [ ] No Streamlit imports leak into core/research modules.
- [ ] Full test suite passes.

---

## Sub-Phase 9H: CLI Interface

**Goal:** Run ReconIQ from the command line without launching Streamlit.

**Status:** Complete — merged to main.

**Branch:** `feat/phase-9f-9h-9i-exports-cli-batch`

**Files Created:**
- `cli.py` — argparse CLI with single-URL and batch modes

**Verification:**
- `223 passed`; CLI tests pass; Playwright UI test passes.

### Interface

```bash
python cli.py https://example.com --modules company_profile,swot --provider deepseek --format pdf
python cli.py --batch urls.txt --format html --quiet
```

### Files to Create

- Create: `cli.py` — argument parsing with `argparse`

### Interface Sketch

```bash
uv run python cli.py https://example.com \
  --modules company_profile,seo_keywords,swot \
  --provider deepseek \
  --output reports/
```

### Verification Checklist

- [ ] CLI produces the same report as the Streamlit UI.
- [ ] `--help` shows all options clearly.
- [ ] Exit code 0 on success, non-zero on failure.
- [ ] Full test suite passes.

---

## Sub-Phase 9I: Batch / Bulk Analysis

**Goal:** Analyze multiple URLs in one run (e.g. a list of prospects).

**Status:** Complete — merged to main.

**Branch:** `feat/phase-9f-9h-9i-exports-cli-batch`

**Files Created:**
- `core/batch.py` — `run_batch()` with sequential and parallel execution

**Files Modified:**
- `cli.py` — `--batch` flag reads CSV/text files of URLs

**Verification:**
- `223 passed`; batch tests pass; Playwright UI test passes.

### Ideas

- Accept a CSV or text file of URLs
- Run analyses sequentially or with limited parallelism
- Produce one combined report or one report per URL
- Useful for agency prospecting workflows

---

## Suggested Work Sessions

| Session | Enhancements | Outcome |
|---------|--------------|---------|
| 9A | 9D (Pydantic) + 9E (Cache) | Type safety + speed |
| 9B | 9B (Playwright) + 9C (Search API) | Better data quality |
| 9C | 9F (Exports) + 9G (UI polish) | Better deliverables |
| 9D | 9J (Deep Scraping) | Real data, not inference |
| 9E | 9H (CLI) + 9I (Batch) | Power-user features |
| 9F | 9A (FastAPI migration) | Production readiness |

---

## Definition of Done for Each Enhancement

An enhancement is complete when:

- Code is implemented and tested.
- `uv run python -m pytest -q` passes.
- `python -m py_compile` passes for all modified files.
- `git diff --check` passes.
- Documentation (this file or README) is updated.
- PR is opened and reviewed.
- Enhancement status below is updated.

---

## Sub-Phase 9J: Deep Scraping — Multi-Page Crawling & Structured Extraction

**Goal:** Replace the current single-page text dump with a structured, multi-page crawl so research modules work from real data — not LLM guesswork. The core problems this solves:

1. **Single-page scraping** — The scraper only fetches the top-level URL. Footer content (service area zip codes, social links, review site links) gets flattened into 50K chars of undifferentiated text and can be truncated or missed by the LLM.
2. **No subpage crawling** — Interior pages (Services, About, Contact, Blog) are never scraped. The LLM only sees one page's worth of content.
3. **Social media is pure inference** — The `social_content` module doesn't scrape; it asks the LLM to "infer" platforms. This produces wrong results (e.g. listing "Social Media" as a channel when the business has none).
4. **Competitor URLs are made up** — The competitor module prompt says "use plausible URLs if unknown" — these are not real competitor sites.
5. **Content truncation** — `company_profile.py` truncates scraped text to 8000 chars. Rich footer content (zips, service areas, social links) can be cut off.

**Status:** Complete — 9J-1 (Structured Extraction), 9J-2 (Multi-Page Crawler), and 9J-3 (Integration) all merged to main.

**Branch:** `feat/phase-9j3-9c-9d-9e-integration`

**Local verification:** `198 passed`; Playwright UI smoke test passed; compile check passed; `git diff --check` passed.

### Implementation — Phase 9J-1: Structured Extraction

**Status:** Complete — local verification passed; PR pending.

**Branch:** `feat/phase-9j1-structured-extraction`

**Local verification:** `158 passed`; compile check passed; `git diff --check` passed.

**Files Created:**
- `scraper/models.py` — `ScrapeResult`, `PageData`, `LinkData`, `SocialLink` dataclasses
- `scraper/extractors.py` — `extract_meta()`, `extract_links()`, `extract_social_links()`, `extract_contact_info()`, `extract_json_ld()`, `extract_headings()`
- `tests/test_structured_extraction.py` — 50 tests covering all six extractors and all four dataclasses

**Files Modified:**
- `scraper/scraper.py` — Added `scrape_structured()` and `_fetch_html()`; added imports for extractors and models

### Architecture: Two-Layer Scraper

Replace the current flat `scrape()` → text dump approach with a structured crawler that:

1. **Fetches the target URL's HTML** (using existing requests + Playwright fallback)
2. **Parses structured metadata** from the HTML before flattening to text:
   - `<title>`, `<meta>` description/keywords, Open Graph tags
   - `<a>` links (internal + external) with link text
   - Social media links (detected from URLs, not inferred)
   - Phone numbers, email addresses (regex extraction)
   - Structured data / JSON-LD (if present)
3. **Discovers and queues subpages** (internal links from `<nav>`, footer, sitemap)
4. **Crawls up to N subpages** (configurable, default 5) with depth limit
5. **Returns a structured `ScrapeResult`** with separate fields instead of a raw string

### Files to Create / Modify

| File | Action | Description |
|------|--------|-------------|
| `scraper/models.py` | Create | `ScrapeResult`, `PageData`, `LinkData`, `SocialLink` dataclasses |
| `scraper/crawler.py` | Create | `crawl_site(url, max_pages=5, max_depth=2) -> ScrapeResult` |
| `scraper/extractors.py` | Create | Structured extractors: `extract_meta()`, `extract_links()`, `extract_social_links()`, `extract_contact_info()`, `extract_json_ld()` |
| `scraper/scraper.py` | Modify | Add `scrape_structured(url) -> ScrapeResult` alongside existing `scrape()` for backward compat |
| `research/company_profile.py` | Modify | Use `ScrapeResult` instead of raw text; pass structured data to LLM prompt |
| `research/social_content.py` | Modify | Use extracted social links instead of pure LLM inference; only infer what wasn't found |
| `research/competitors.py` | Modify | Scrape discovered competitor URLs (from links or search API); mark scraped vs. inferred |
| `research/seo_keywords.py` | Modify | Use `<meta>` keywords, `<title>`, and `<h1>`-`<h3>` headings as real SEO signals |
| `research/swot.py` | Modify | No major changes; benefits from richer upstream data |
| `core/services.py` | Modify | Pass `ScrapeResult` through the coordinator |
| `core/models.py` | Modify | Add `max_pages` and `max_depth` to `AnalysisRequest` |

### Implementation Plan

**Phase 9J-1: Structured Extraction (scraper/models.py + scraper/extractors.py)**

1. Create `ScrapeResult` dataclass in `scraper/models.py`:
   ```python
   @dataclass
   class ScrapeResult:
       url: str
       title: str
       meta_description: str = ""
       meta_keywords: list[str] = field(default_factory=list)
       og_tags: dict[str, str] = field(default_factory=dict)
       headings: dict[str, list[str]] = field(default_factory=dict)  # h1, h2, h3
       internal_links: list[LinkData] = field(default_factory=list)
       external_links: list[LinkData] = field(default_factory=list)
       social_links: list[SocialLink] = field(default_factory=list)
       phone_numbers: list[str] = field(default_factory=list)
       emails: list[str] = field(default_factory=list)
       json_ld: list[dict] = field(default_factory=list)
       body_text: str = ""
       pages: list[PageData] = field(default_factory=list)  # subpages
       raw_html_length: int = 0
       crawl_duration_s: float = 0.0
   ```
2. Create `extractors.py` with functions:
   - `extract_meta(soup) -> dict` — pulls title, description, keywords, OG tags
   - `extract_links(soup, base_url) -> tuple[list[LinkData], list[LinkData]]` — sorts internal vs. external
   - `extract_social_links(soup) -> list[SocialLink]` — matches `<a href>` against known social URL patterns (linkedin.com, facebook.com, instagram.com, x.com/twitter.com, yelp.com, google.com/maps, etc.)
   - `extract_contact_info(soup) -> tuple[list[str], list[str]]` — regex for phone and email
   - `extract_json_ld(soup) -> list[dict]` — pulls `<script type="application/ld+json">` blocks
   - `extract_headings(soup) -> dict[str, list[str]]` — h1, h2, h3 text

**Phase 9J-2: Multi-Page Crawler (scraper/crawler.py)**

1. Create `crawl_site(url, max_pages=5, max_depth=2, timeout=15) -> ScrapeResult`
2. Use `requests` to fetch pages (no Playwright for subpages by default — too slow)
3. Seed queue from:
   - Links found in `<nav>`, `<footer>`, and sitemap.xml (if `/sitemap.xml` is reachable)
   - Common subpage patterns: `/about`, `/services`, `/contact`, `/blog`
4. Deduplicate URLs, respect `max_pages` limit
5. Each subpage contributes its own `PageData(text, url, headings, links)`
6. Incremental progress via existing `progress_callback` mechanism

**Phase 9J-3: Integrate ScrapeResult into Research Modules**

1. `company_profile.py`:
   - Replace raw text with structured context in the LLM prompt
   - Include: title, meta description, headings, contact info, social links, JSON-LD
   - Increase truncation limit to 12K chars (we now know what's important)
   - Still pass body_text but now with structured metadata prepended

2. `social_content.py`:
   - If `social_links` list is non-empty, pass real found social accounts to LLM
   - LLM's job shifts from "infer which platforms they use" to "analyze presence on these verified accounts + identify any gaps"
   - Add `verified_social_accounts` and `inferred_platforms` as separate fields in output

3. `competitors.py`:
   - If external links contain competitor-looking domains, verify them
   - Separate `scraped_competitors` (verified URLs found on the target site) from `inferred_competitors` (LLM-only)
   - Add a future hook for Phase 9C (search API) to discover real competitors

4. `seo_keywords.py`:
   - Include `<title>`, `<meta keywords>`, `<meta description>`, and `<h1>`-`<h3>` headings in the prompt
   - LLM now works from actual on-page SEO signals, not just company profile text

### Verification Checklist

- [ ] `ScrapeResult` dataclass round-trips correctly through all research modules
- [ ] Social links extracted from actual `<a>` tags (not LLM-inferred)
- [ ] Footer content (zips, service areas) included in structured output
- [ ] Subpage content visible to research modules
- [ ] Existing `scrape()` function still works (backward compat)
- [ ] `crawl_site()` respects `max_pages` and `max_depth` limits
- [ ] Report output clearly labels `scraped` vs. `inferred` data
- [ ] All 108 existing tests still pass
- [ ] New extractor functions have unit tests

### Design Decisions

- **Backward compat**: Keep `scrape(url) -> str` working. Add `scrape_structured(url) -> ScrapeResult` as the new path. Research modules can call either.
- **Playwright for subpages**: Off by default. Subpage crawling uses `requests` for speed. Playwright only for the initial target URL if the primary requests path returns sparse content.
- **Rate limiting**: 1-second delay between subpage requests to be polite.
- **Robots.txt**: Check `robots.txt` before crawling subpages. Skip disallowed paths.
- **Sitemap discovery**: If `/sitemap.xml` exists, use it to prioritize important subpages instead of guessing.

---

## Enhancement Quick Reference

| ID | Name | Status | PR | Branch |
|----|------|--------|-----|--------|
| 9A | FastAPI Migration | Complete — merged | Merged | `feat/phase-9a-fastapi` |
| 9B | Playwright JS Rendering | Complete — merged | Merged | `feat/phase-9b-playwright` |
| 9C | Competitor Search API | Complete — merged | Merged | `feat/phase-9j3-9c-9d-9e-integration` |
| 9D | Pydantic Schemas | Complete — merged | Merged | `feat/phase-9j3-9c-9d-9e-integration` |
| 9E | Cached Runs | Complete — merged | Merged | `feat/phase-9j3-9c-9d-9e-integration` |
| 9F | Export Formats | Complete — merged | Merged | `feat/phase-9f-9h-9i-exports-cli-batch` |
| 9G | UI Polish / Dark Mode | Complete — merged | Merged | `feat/phase-9g-ui-polish` |
| 9H | CLI Interface | Complete — merged | Merged | `feat/phase-9f-9h-9i-exports-cli-batch` |
| 9I | Batch Analysis | Complete — merged | Merged | `feat/phase-9f-9h-9i-exports-cli-batch` |
| 9J | Deep Scraping | Complete — merged | Merged | `feat/phase-9j3-9c-9d-9e-integration` |
