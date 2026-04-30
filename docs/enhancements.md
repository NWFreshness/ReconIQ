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

**Status:** Not started

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

**Status:** In progress — local implementation and verification complete; PR pending.

**Branch:** `feat/phase-9b-playwright`

**Local verification:** `108 passed`; focused Playwright checks `10 passed`; compile check passed; `git diff --check` passed.

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

**Status:** Not started

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

**Status:** Not started

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

**Status:** Not started

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

**Status:** Not started

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

**Status:** In progress — local implementation and verification complete; not yet committed/pushed.

**Branch:** `feat/phase-9g-ui-polish`

**Local verification:** `108 passed`; compile check passed; `git diff --check` passed.

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

**Status:** Not started

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

**Status:** Not started

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
| 9D | 9H (CLI) + 9I (Batch) | Power-user features |
| 9E | 9A (FastAPI migration) | Production readiness |

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

## Enhancement Quick Reference

| ID | Name | Status | PR | Branch |
|----|------|--------|-----|--------|
| 9A | FastAPI Migration | Not started | — | — |
| 9B | Playwright JS Rendering | In progress | — | `feat/phase-9b-playwright` |
| 9C | Competitor Search API | Not started | — | — |
| 9D | Pydantic Schemas | Not started | — | — |
| 9E | Cached Runs | Not started | — | — |
| 9F | Export Formats | Not started | — | — |
| 9G | UI Polish / Dark Mode | In progress | — | `feat/phase-9g-ui-polish` |
| 9H | CLI Interface | Not started | — | — |
| 9I | Batch Analysis | Not started | — | — |
