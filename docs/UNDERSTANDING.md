# ReconIQ — Project Understanding

> Last regenerated: 2026-04-30. Comprehensive pass covering the full current state
> after the `llm_json_call` retry mechanism, `ScrapeCache`, and coordinator pre-scrape workflow.

---

## 1. What Is This?

ReconIQ is a **marketing intelligence pipeline** wrapped in a Streamlit web app. You give it a company URL; it scrapes the site, feeds content to LLM-powered research modules, and produces a structured Markdown report covering company profile, SEO gaps, competitor landscape, social/content audit, and a SWOT-based acquisition strategy. It's purpose-built for an AI automation agency that wants to research prospective clients and generate outreach strategies.

**Stack:** Python 3.12, Streamlit, LiteLLM (multi-provider LLM routing), BeautifulSoup + Playwright (web scraping), ThreadPoolExecutor (parallel research modules).

**Entry point:** `app.py` → Streamlit UI → `core/services.py` → `research/coordinator.py` → research modules → LLM → JSON parsing → `report/writer.py` → `.md` file.

---

## 2. Architecture

```
┌─────────────┐
│  Streamlit   │  app.py — UI, session state, progress bar, module toggles
│   (app.py)   │  Pure helpers: normalize_url, validate_url, build_analysis_request
└──────┬───────┘
       │ AnalysisRequest(target_url, enabled_modules, provider_override, model_override, max_pages, max_depth)
       ▼
┌──────────────┐    configured_llm_complete binds provider/model overrides from the request
│ core/         │
│  services.py  │──── run_analysis(): the single orchestration entry point
└──────┬────────┘
       │
       ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ research/                                                                   │
│  coordinator.py — run_all(): dependency-aware module execution            │
│                    │                                                       │
│                    │  Phase 0: Create ScrapeCache, pre-scrape the URL once │
│                    │  Phase 1: company_profile (sequential, gate for all)   │
│                    │           └─ receives pre-scraped content via param   │
│                    │  Phase 2: seo_keywords  ┐                              │
│                    │          competitor     ├─ parallel (ThreadPoolExecutor)│
│                    │          social_content ┘                              │
│                    │  Phase 3: swot (after all above, synthesizes everything)│
│                    │                                                       │
│                    │  Each module: llm_json_call(prompt, module, ...) → dict│
└──────┬──────────────────────────┬─────────────────────────────────────────┘
       │                          │
       ▼                          ▼
┌──────────────┐          ┌──────────────┐
│ scraper/      │          │ llm/router.py│
│  scraper.py   │          │              │
│  ┌──────────┐│          │  LiteLLM unified interface               │
│  │ScrapeCache││          │  5 providers: deepseek, openai,          │
│  │ .get_text()    │          │  anthropic, groq, ollama                 │
│  │ .get_structured()│           │  Automatic fallback → deepseek             │
│  └──────────┘│          │  Per-module provider/model override         │
│  crawler.py   │          └──────┬───────┘
│  extractors.py│                 │ raw LLM text response
│  models.py    │                 ▼
└──────────────┘          ┌──────────────────────┐
                          │ research/parsing.py   │
                          │  llm_json_call()      │── retry wrapper (≤3 attempts)
                          │  extract_json_object()│── finds first valid JSON
                          │  require_keys()       │── validates required fields
                          │  JsonParsingError     │── custom exception class
                          └──────┬───────────────┘
                                 │ parsed dict
                                 ▼
                          ┌──────────────┐
                          │ report/       │
                          │  writer.py    │── assembles Markdown sections
                          └──────────────┘
```

---

## 3. Core Abstractions (The Vocabulary)

| Concept | Where | What It Means |
|---------|-------|---------------|
| **AnalysisRequest** | `core/models.py:17` | Input contract: URL + module toggles + LLM overrides + crawler settings (`max_pages`, `max_depth`). |
| **AnalysisResult** | `core/models.py:30` | Output: a flat `results` dict (keyed by module name) + `report_path`. Module outputs are untyped dicts — the only schema enforcement is runtime `require_keys()`. |
| **ScrapeResult** | `scraper/models.py:30` | Structured scrape output: title, meta_description, meta_keywords, og_tags, headings, internal_links, external_links, social_links, phone_numbers, emails, json_ld, body_text, pages (list of PageData), raw_html_length, crawl_duration_s. |
| **PageData** | `scraper/models.py:22` | Content from a single crawled subpage: url, title, text, headings. |
| **LinkData** | `scraper/models.py:14` | A hyperlink: href + text. |
| **SocialLink** | `scraper/models.py:7` | A social media link: platform + url. |
| **ScrapeCache** | `scraper/scraper.py:35` | In-memory LRU-style cache scoped to a single `run_all()` call. Two methods: `get_text(url)` returns raw text, `get_structured(url)` returns ScrapeResult. Thread-safe for use with ThreadPoolExecutor. Prevents re-scraping the same URL across modules. |
| **llm_json_call** | `research/parsing.py:33` | Retry wrapper for all module LLM calls. Attempts up to 3 times (1 original + 2 retries). On failure: appends JSON reminder prompt, lowers temperature (0.7 → 0.4 → 0.3). Validates both JSON parsing and required keys. Raises `JsonParsingError` if all attempts fail. |
| **llm_complete** | `llm/router.py:62` | The LLM callable. Takes `prompt, module, system, max_tokens, temperature`. Returns raw text string. Handles provider routing, model resolution, and deepseek fallback. |
| **Module** | `research/*.py` | Each module has a `run()` function. All now use `llm_json_call()` instead of direct `llm_complete()` calls. Signatures vary: some take just `(url, llm_complete)`, others take `(profile, url, llm_complete)`, SWOT takes all prior outputs. |
| **ProgressCallback** | `core/services.py:11` | `(message: str, percent: float) → None`. Wires progress from deep modules up to the Streamlit progress bar. |
| **config.yaml** | Project root | Single source of truth for providers, models, scraper settings, and per-module overrides. Loaded via `core/settings.py` with `${ENV_VAR}` resolution. Cached at module import time. |

---

## 4. Data Flow Trace — URL to .md Report

A complete analysis run, with file:line references:

```
1. User enters URL in Streamlit UI
   app.py:204       → st.text_input("Target URL")
   app.py:210       → st.button("Analyze →")
   app.py:276       → build_analysis_request() creates AnalysisRequest
   app.py:285       → run_analysis(request, progress_callback)

2. core/services.py:14  run_analysis()
   services.py:17-32 → Creates configured_llm_complete closure that injects
                        provider_override and model_override from the request
   services.py:34     → run_all(target_url, llm_complete, enabled_modules, progress_callback)

3. research/coordinator.py:26  run_all()
   coordinator.py:40  → _initial_metadata() creates metadata dict
   coordinator.py:46  → ScrapeCache() created for this run
   coordinator.py:48  → Progress logging closure defined

   ── Phase 0: Pre-scrape ──────────────────────────────────────────────
   coordinator.py:74  → If company_profile is enabled:
   coordinator.py:77  → scrape_cache.get_text(target_url) — scrapes once
   coordinator.py:78-85 → If content is empty, falls back to domain-only hint

   ── Phase 1: Company Profile (must succeed) ────────────────────────
   coordinator.py:91  → log("Running Company Profile...", 12%)
   coordinator.py:93  → run_company_profile(target_url, llm_complete, scraped_content=scraped_content)
                        ↑ pre-scraped content passed via param
   company_profile.py:51 → Uses scraped_content if provided, else scrapes inline
   company_profile.py:71 → llm_json_call(llm_complete, prompt, "company_profile", ...)

   ── Phase 2: Downstream modules in parallel ─────────────────────────
   coordinator.py:146 → _run_downstream_modules()
   coordinator.py:171 → ThreadPoolExecutor(max_workers=len(tasks))
   Each downstream module calls llm_json_call() directly
   (seo_keywords, competitors, social_content — NOT company_profile)

   ── Phase 3: SWOT synthesis ──────────────────────────────────────────
   coordinator.py:122 → If profile succeeded and swot is enabled:
   coordinator.py:125 → run_swot(company_profile=..., seo_keywords=..., competitor=..., social_content=...)
   swot.py:76         → llm_json_call(llm_complete, prompt, "swot", ...)

   ── Results aggregation ───────────────────────────────────────────────
   coordinator.py:142 → Returns results dict with metadata, module outputs, errors

4. Back in core/services.py:40
   services.py:40     → write_report(results, output_dir) creates .md file

5. research/parsing.py:33  llm_json_call() — called by every module
   parsing.py:73       → Loop up to (1 + max_retries) attempts (default 3 total)
   parsing.py:74       → Temperature decreases: 0.7 → 0.4 → 0.3
   parsing.py:78-79    → On retries: appends _JSON_RETRY_REMINDER to prompt
   parsing.py:81-87    → Calls llm_complete() with current temperature
   parsing.py:90       → extract_json_object() on raw response
   parsing.py:97-103   → If required_keys provided: require_keys() validates
   parsing.py:108      → Raises last error if all attempts exhausted

6. scraper/scraper.py:35  ScrapeCache — created once per run_all()
   scraper.py:46       → get_text(url): normalizes URL, checks cache, calls scrape()
   scraper.py:56       → get_structured(url): normalizes URL, checks cache, calls scrape_structured()
   Both methods cache results and return cached values on subsequent calls

7. report/writer.py:10  write_report()
   writer.py:21        → _infer_company_name() from profile
   writer.py:22        → Slug generation from company name
   writer.py:25        → Directory creation: reports/{slug}/{timestamp}.md
   writer.py:29        → _build_markdown() assembles all sections
   writer.py:142-217   → _build_markdown() renders: metadata, company overview,
                        SEO, competitors, social, SWOT, acquisition strategy, next steps

8. Back in app.py:287-293 → Reads report file, stores in session_state
   app.py:339          → st.markdown(report_content) renders to user
```

---

## 5. Module-by-Module Summary

### `app.py` — Streamlit UI (342 lines)
- Entry point. Manages session state, URL validation, module toggles (5 checkboxes), progress bar, report display, download button.
- Pure helpers at lines 19-76: `normalize_url()`, `validate_url()`, `build_analysis_request()`, `open_folder()` — all testable without Streamlit.
- Lines 80-342: Streamlit rendering — sidebar (LLM provider/model, output dir), hero section, input, module toggles, progress, report card.
- Lines 95-124: JavaScript hack to force sidebar open via MutationObserver (fragile).

### `core/models.py` — Data contracts (35 lines)
- `AnalysisRequest`: URL, enabled_modules dict, provider_override, model_override, output_dir, max_pages (default 5), max_depth (default 2).
- `AnalysisResult`: flat `results: dict[str, Any]` + `report_path: str | None`.
- `DEFAULT_ENABLED_MODULES`: all 5 modules on by default.

### `core/services.py` — Orchestration bridge (41 lines)
- `run_analysis()`: Creates a closure (`configured_llm_complete`) that injects request-level provider/model overrides, then delegates to `coordinator.run_all()` and `report.write_report()`.
- This is the **single point** that ties the UI to the business logic.

### `core/settings.py` — Config loader (33 lines)
- `load_config()`: Loads `config.yaml`, resolves `${ENV_VAR}` strings via `resolve_env_values()`.
- Uses `python-dotenv` to load `.env` at import time.
- `PROJECT_ROOT` is computed relative to the file's location.

### `llm/router.py` — LLM abstraction (103 lines)
- `get_config()`: Returns loaded config dict (for UI display and tests).
- `get_module_provider_model()`: Per-module override from config.
- `resolve_model()`: Builds `provider/model` string for LiteLLM.
- `build_completion_kwargs()`: Assembles the LiteLLM call — includes `api_base` for Ollama.
- `complete()`: Main entry. Builds messages, tries primary provider, falls back to deepseek on failure.
- `_providers_to_try()`: Returns `[primary, "deepseek"]` unless primary IS deepseek.
- `check_ollama()`: Health check via `/api/tags` endpoint.
- **Config loaded at module import time** (line 11): `config = load_config()`. No hot-reload.

### `research/coordinator.py` — Dependency orchestrator (217 lines)
- `run_all()`: Creates ScrapeCache, pre-scrapes URL, then runs modules in dependency order.
  - Phase 0: Creates `ScrapeCache()`, calls `scrape_cache.get_text(target_url)` for the homepage.
  - Phase 1: `company_profile` must succeed before downstream modules. Receives `scraped_content` param.
  - Phase 2: SEO, Competitors, Social run in parallel via `ThreadPoolExecutor`.
  - Phase 3: SWOT synthesizes all available outputs.
- `_run_downstream_modules()`: Parallel execution with `ThreadPoolExecutor`. Each module gets `company_profile` output as input.
- `_initial_metadata()`: Tracks target_url, timestamp, modules_run/skipped/failed, data_limitations.
- `_collect_data_limitations()`: Aggregates limitation strings from module results.

### `research/parsing.py` — JSON extraction and LLM retry (174 lines)
- `JSON_RESPONSE_RULES`: Constant appended to every module's system prompt.
- `JsonParsingError`: Custom `ValueError` subclass for all parse failures.
- `extract_json_object()`: Scans raw LLM text for the first valid JSON object. Handles markdown fences, surrounding text, nested objects. Uses `json.JSONDecoder.raw_decode()` for incremental scanning.
- `extract_json_array()`: Same but for JSON arrays.
- `require_keys()`: Validates required keys exist; raises `JsonParsingError` with context.
- **`llm_json_call()`** (lines 33-108): The retry wrapper. Up to 3 total attempts. On retry: appends `_JSON_RETRY_REMINDER` to the prompt, lowers temperature (`_RETRY_TEMPERATURES = [0.7, 0.4, 0.3]`). Validates JSON parsing AND required keys. Raises last error on exhaustion.

### Research modules — the 5 analysis engines
All follow the pattern: build prompt → `llm_json_call()` → return dict. Each defines `SYSTEM_PROMPT` and `REQUIRED_KEYS`.

| Module | File | Input | Output |
|--------|------|-------|--------|
| company_profile | `company_profile.py:39` | URL + llm_complete + scraped_content (optional) | Dict with company_name, what_they_do, target_audience, value_proposition, brand_voice, primary_cta, services_products, marketing_channels, data_confidence, data_limitations |
| seo_keywords | `seo_keywords.py:32` | company_profile + URL + llm_complete | Dict with top_keywords, content_gaps, seo_weaknesses, quick_wins, estimated_traffic_tier, local_seo_signals |
| competitors | `competitors.py:35` | company_profile + URL + llm_complete | Dict with competitors list (name, url, positioning, estimated_pricing_tier, key_messaging, weaknesses, inferred_services) |
| social_content | `social_content.py:36` | company_profile + URL + llm_complete | Dict with platforms, content_quality, content_frequency, engagement_signals, review_sites, blog_or_resources, content_gaps, email_signals |
| swot | `swot.py:45` | all module outputs + URL + llm_complete | Dict with swot (strengths/weaknesses/opportunities/threats), acquisition_angle, talking_points, recommended_next_steps, competitive_advantage, lead_generation_strategy, close_rate_strategy |

**SWOT is unique**: receives all prior module outputs as input, not just the raw scrape. The `_format_dict()` helper (line 95) serializes nested data for the prompt.

**company_profile is the gate**: If it fails, all downstream modules are skipped, including SWOT.

### `scraper/scraper.py` — Web scraper (327 lines)
- `ScrapeCache`: In-memory cache with `get_text(url)` and `get_structured(url)` methods. URL-normalized, dictionary-backed. Thread-safe for ThreadPoolExecutor use.
- `scrape()`: requests + BeautifulSoup primary, Playwright fallback if content <200 chars. Returns raw text (max 50K chars).
- `scrape_structured()`: Returns `ScrapeResult` dataclass with typed fields. Same fallback strategy.
- `scrape_with_playwright()`: Headless Chromium via Playwright sync API. 3-second JS settle time.
- `_clean_html()`: Removes script/style/noscript tags, unwraps nav/header/footer/aside (keeps text content).
- `normalize_url()`: Adds `https://` to bare domains.
- `extract_domain_name()`: Extracts domain from URL for LLM fallback prompts.
- `_fetch_html()`: Raw HTML getter via requests (used by crawler and structured scrape).
- `should_use_playwright()`: Checks both config flag and Playwright availability.

### `scraper/crawler.py` — Multi-page site crawler (400 lines)
- `crawl_site()`: BFS crawler. Fetches homepage, discovers seed URLs (nav/footer links + internal links + sitemap.xml + common probe paths), then crawls subpages up to `max_pages`/`max_depth`.
- `fetch_robots_txt()`: Fetches and parses robots.txt. Returns `None` on failure (permissive fallback).
- `fetch_sitemap_urls()`: Tries `/sitemap.xml` for additional URLs.
- `_discover_seed_urls()`: Priority-ordered URL discovery from nav/footer, then internal links, then sitemap, then probe paths.
- `_scrape_subpage()`: Uses requests only (no Playwright) for speed. Returns `_SubpageResult`.
- Merges supplementary data (emails, phones, social links) from subpages into top-level `ScrapeResult`.
- **Politess delay**: 1-second `time.sleep()` between subpages.
- **Currently NOT wired into the research pipeline**. Exists but not called by coordinator or modules.

### `scraper/extractors.py` — HTML metadata extractors (268 lines)
- `extract_meta()`: title, meta_description, meta_keywords, og_tags.
- `extract_links()`: Separates internal vs external `LinkData` links.
- `extract_social_links()`: 16-platform pattern matching → `SocialLink` list.
- `extract_contact_info()`: Phone numbers (3 patterns) + emails from href and body text.
- `extract_json_ld()`: All `<script type="application/ld+json">` blocks → list of dicts.
- `extract_headings()`: h1, h2, h3 text → `dict[str, list[str]]`.

### `scraper/models.py` — Scrape data models (51 lines)
- `SocialLink(platform, url)`, `LinkData(href, text)`, `PageData(url, title, text, headings)`, `ScrapeResult(url, title, meta_description, ...)` — all `@dataclass(slots=True)`.

### `report/writer.py` — Markdown report generator (217 lines)
- `write_report()`: Creates `reports/{slug}/{timestamp}.md`.
- `_infer_company_name()`: From profile or fallback to "Unknown Company".
- `_section_content()`: Generic dict-to-markdown renderer.
- `_competitor_section()`: Renders list-of-dicts competitor format.
- `_swot_section()`: Renders S/W/O/T as nested bullet lists.
- `_acquisition_section()`: Renders outreach strategy fields (angle, advantage, lead gen, close rate, talking points).
- `_next_steps_section()`: Numbered list of tactical actions.
- `_build_markdown()`: Assembles full report: 7 sections (Overview, SEO, Competitors, Social, SWOT, Acquisition Strategy, Next Steps) + metadata header.

### `config.yaml` — Configuration
- 5 providers with default models: deepseek (deepseek-chat), openai (gpt-4o-mini), anthropic (claude-3-5-sonnet-latest), groq (llama-3.3-70b-versatile), ollama (llama3).
- Scraper config: `use_playwright_fallback: true`, `max_pages: 5`, `max_depth: 2`.
- Per-module provider/model overrides (currently all using deepseek defaults).

---

## 6. Invariants & Assumptions (The Rules)

1. **Company Profile is the gate.** If it fails, ALL downstream modules (SEO, Competitors, Social, SWOT) are skipped. The entire pipeline depends on a successful profile extraction. This is enforced in `coordinator.py:105-120`.

2. **LLM responses are now retried.** Every research module uses `llm_json_call()` (not raw `llm_complete()`). On JSON parse failure, the system retries up to 2 additional times with a JSON reminder prompt and decreasing temperature (0.7 → 0.4 → 0.3). If all 3 attempts fail, the module error propagates and the coordinator marks it as failed.

3. **Homepage is pre-scraped once per run.** The coordinator creates a `ScrapeCache` at the start of `run_all()` and scrapes the target URL once (coordinator.py:77). Company profile receives this content via the `scraped_content` parameter. Other modules currently still call `llm_json_call()` directly without explicitly using the cache, but the plumbing is in place for them to use `scrape_cache.get_text()` in future work.

4. **Provider fallback is always DeepSeek.** `llm/router.py:55-59` — if the chosen provider fails, it silently falls back to DeepSeek. No UI indication of which provider actually responded. The report metadata records provider/model only if the LLM callable has those attributes.

5. **Module toggles are per-run.** The user can disable modules in the UI. Disabled modules appear in `modules_skipped`. The coordinator checks `enabled_modules` before each module.

6. **Reports are append-only Markdown files.** Each run generates `reports/{slug}/{timestamp}.md`. No deduplication or overwriting.

7. **The UI is tightly coupled.** `app.py` is 342 lines of Streamlit logic mixing helpers with `st.` calls. The pure helpers are testable; the render logic is not.

8. **ScrapeResult is transitional.** `scrape_structured()` and `crawl_site()` return `ScrapeResult` dataclasses with typed fields. Company profile now receives text content from the cache. The crawler and structured scrapers exist but are not yet the primary path for all modules. The next step is to have modules use `ScrapeResult` body_text and typed fields instead of raw text strings.

9. **ScrapeCache is per-run, not persistent.** The `ScrapeCache` is created fresh at the start of each `run_all()` call (coordinator.py:46). It does not persist between analysis runs. This is by design — cached content could become stale.

---

## 7. Dangerous Curves (Non-Obvious Gotchas)

- **The llm_json_call retry costs LLM tokens.** Each retry is a full LLM call. With 3 attempts per module and 5 modules, a worst case could generate 15 calls. The temperature reduction strategy (0.4, 0.3) may produce more deterministic but less creative results on retry.

- **ScrapeCache only helps company_profile currently.** The pre-scraped content is passed to `company_profile` via `scraped_content` parameter, but the other 3 downstream modules (SEO, Competitors, Social) don't receive scraped content — they operate on the company_profile dict output. The cache object is created but not yet utilized by modules other than company_profile. If those modules were to scrape independently (which they currently don't), they'd bypass the cache.

- **Config is loaded at module import time.** `llm/router.py:11` does `config = load_config()` at the top level. Similarly, `scraper/scraper.py` lazily caches config in `_get_config()`. Changing `config.yaml` requires restarting the Streamlit app. No hot-reload.

- **Sidebar JS hack.** `app.py:95-124` injects JavaScript to force the sidebar open via DOM manipulation and a `MutationObserver`. This fights Streamlit's React internals and could break on Streamlit version upgrades.

- **`_providers_to_try` bypasses user intent.** If a user selects OpenAI and it fails, the router silently falls back to DeepSeek. The UI shows "Using openai/gpt-4o-mini" but the actual response may come from DeepSeek. No UI indication of fallback.

- **Streamlit `st.rerun()` in finally block.** `app.py:310` calls `st.rerun()` in the `finally` block after analysis. Error messages set in the `except` block may flash briefly before disappearing.

- **Crawler's `time.sleep(1.0)`.** `scraper/crawler.py:357` adds a 1-second delay between subpage requests. Not configurable. Crawling 5 subpages takes at least 5 seconds before LLM calls begin. But the crawler is not currently wired into the pipeline.

- **ScrapeCache URL normalization.** `ScrapeCache.get_text()` and `get_structured()` call `normalize_url()` before caching. If `scrape()` and `ScrapeCache.get_text()` receive the same URL with different normalization (e.g., with/without trailing slash), they could result in different cache keys. The `normalize_url()` function handles bare domains by adding `https://`, so this is generally safe, but URL fragments and query strings could theoretically cause double-caching.

- **`llm_json_call` temperature schedule is fixed.** The `_RETRY_TEMPERATURES = [0.7, 0.4, 0.3]` is a module-level constant. The initial call always uses 0.7 (matching the original `company_profile.run()` default), then drops on retries. This means if a module calls `llm_json_call()` with a different initial temperature intent, the first call will still use 0.7. Currently all modules use the default.

- **Downstream modules receive `company_profile` as a dict, not typed data.** The company_profile output is an untyped dict. If the LLM returns unexpected keys or nested structures, downstream modules access them with `.get()` and `/.join()`, which is fragile.

---

## 8. Change Hotspots

Based on git history (most-changed files):

1. `research/parsing.py` — Recently added `llm_json_call()`, the retry wrapper that all modules now use. This is the highest-impact recent change — every module call flows through it.

2. `scraper/scraper.py` — Recently added `ScrapeCache`. The crawler and structured extraction features were added in prior phases. This file changes whenever scraping behavior needs adjustment.

3. `research/coordinator.py` — Recently modified to create ScrapeCache and pass `scraped_content` to company_profile. This is the orchestration nexus — any module dependency change affects this file.

4. `docs/plan-v2.md` — Plan doc churns most.
5. `app.py` — UI changes and bug fixes.
6. `config.yaml` — Provider/model tuning.
7. `report/writer.py` — Report format iterations.
8. `.streamlit/style.css` — Design system polish.

---

## 9. Test Coverage Summary

194 tests, all passing as of 2026-04-30.

| Test file | Focus |
|-----------|-------|
| `test_parsing.py` | `extract_json_object()`, `extract_json_array()`, `require_keys()` — plain JSON, fenced markdown, surrounding text, invalid input |
| `test_research_parsing.py` | `llm_json_call()` — valid JSON parsing, retry on bad JSON, retry on missing keys, raises after max retries; also `extract_json_object()` with module-style data, `require_keys()` edge cases |
| `test_research_modules.py` | All 5 modules: correct module name, correct prompt structure; `company_profile` pre-scraped content path and fallback; competitor structure validation; SWOT nested key validation |
| `test_coordinator.py` | `run_all()` — execution order, parallel downstream, SWOT receives all outputs, failure recording, disabled modules, progress callback, metadata, ScrapeCache prevents duplicate scrapes |
| `test_scraper.py` | `scrape()`, `normalize_url()`, `extract_domain_name()` — HTML extraction, noise removal, network failures, URL normalization, user agent |
| `test_crawler.py` | Multi-page crawling, robots.txt, sitemap, BFS, subpage merging |
| `test_core_services.py` | `run_analysis()` end-to-end with mocked LLM |
| `test_end_to_end_mocked.py` | Full pipeline: report generation, scrape failure handling, disabled modules, progress callbacks |
| `test_llm_router.py` | LLM provider routing, model resolution, fallback logic |
| `test_report_writer.py` | Markdown generation, section rendering, slug creation |
| `test_app.py` | `normalize_url()`, `validate_url()`, `build_analysis_request()` |
| `test_playwright.py` | Playwright availability detection |
| `test_structured_extraction.py` | `ScrapeResult`, `extract_meta()`, `extract_links()`, `extract_social_links()`, `extract_contact_info()`, `extract_json_ld()`, `extract_headings()` |

---

## 10. Open Questions

1. **The crawler isn't wired in.** `crawl_site()` in `scraper/crawler.py` exists and returns `ScrapeResult`, but no research module calls it. The multi-page crawler was built for Phase 9J-2 but the research modules still operate on single-page content. The next step is to integrate `crawl_site()` output into the analysis pipeline — likely via ScrapeCache's `get_structured()` method.

2. **ScrapeCache is underutilized.** Only `company_profile` receives pre-scraped content. The ScrapeCache object is created in the coordinator but not passed to downstream modules. They work entirely from the company_profile dict output and don't need the raw scrape. If future modules want to scrape competitor URLs or social profiles, the cache is ready for that expansion.

3. **`AnalysisResult.results` is untyped.** Module outputs are dicts with no schema beyond runtime `require_keys()` validation. Pydantic models would add type safety and IDE support (mentioned in Phase 9D of enhancements.md).

4. **Fallback is invisible.** When the LLM router falls back from OpenAI to DeepSeek, the user sees no indication. The report metadata doesn't record which provider actually responded.

5. **The `close_rate_strategy` field is AI-agency-specific.** The SWOT prompt tells the LLM to recommend AI-powered processes for closing deals. This is not a generic SWOT analysis — it's an agency outreach tool. Worth knowing if ReconIQ is ever made generic.

6. **llm_json_call temperature interaction with per-module configs.** Currently, `llm_json_call()` always starts at temperature 0.7 (the `_RETRY_TEMPERATURES` schedule). If a future module wanted a different initial temperature, the retry wrapper would override it. The `llm_json_call()` signature doesn't expose an initial temperature parameter — this could be a limiting factor.

7. **Thread safety of ScrapeCache.** The `ScrapeCache` class is documented as "Thread-safe for use with ThreadPoolExecutor" but uses simple Python dicts (`_text_cache`, `_structured_cache`) without locking. In CPython, dict operations are thread-safe due to the GIL for individual operations, but concurrent writes could theoretically cause issues. In practice, each URL is likely accessed by only one thread, so this is safe but not formally protected.

8. **ScrapeCache has no size limit or eviction policy.** An analysis run scraping many pages could accumulate a large cache. Since the cache is per-run and short-lived (created and destroyed within `run_all()`), this is unlikely to cause memory issues in practice.