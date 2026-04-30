# ReconIQ Dataflow

How a URL goes from the text input to a finished report.

---

## 1. User Input → AnalysisRequest

```
┌─────────────────────────────────────────────────────────┐
│  app.py  —  Streamlit UI                                │
│                                                          │
│  User types URL, toggles modules, picks provider/model   │
│  Clicks [Analyze →]                                      │
│                                                          │
│  validate_url()  →  normalize_url()                      │
│       ↓                                                  │
│  build_analysis_request()                                │
│       ↓                                                  │
│  AnalysisRequest(                                        │
│      target_url="https://acme.com",                     │
│      enabled_modules={...},                              │
│      provider_override="deepseek",                       │
│      model_override=None,                                │
│      output_dir="reports",                               │
│      max_pages=5,                                        │
│      max_depth=2,                                        │
│  )                                                       │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
```

---

## 2. AnalysisRequest → run_analysis()

```
┌─────────────────────────────────────────────────────────┐
│  core/services.py  —  run_analysis()                     │
│                                                          │
│  1. Creates a closure over llm_complete() that injects   │
│     the provider/model overrides from the request        │
│                                                          │
│  2. Calls coordinator.run_all(                           │
│        target_url,                                       │
│        llm_complete=closure,                             │
│        enabled_modules,                                  │
│        progress_callback,                                 │
│     )                                                    │
│                                                          │
│  3. Writes the report: write_report(results, output_dir) │
│                                                          │
│  4. Returns AnalysisResult(results, report_path)           │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
```

---

## 3. Coordinator Orchestrates Module Execution

```
┌──────────────────────────────────────────────────────────────────┐
│  research/coordinator.py  —  run_all()                           │
│                                                                   │
│  Execution order:                                                 │
│                                                                   │
│  ┌─────────────────────┐                                          │
│  │ Module 1:            │                                          │
│  │ Company Profile      │  ← runs FIRST (scrapes the site)       │
│  │ (10% → 25%)         │                                          │
│  └────────┬────────────┘                                          │
│           │ company_profile dict                                   │
│           ▼                                                       │
│  ┌──────────────────────────────────────────────┐                 │
│  │ Modules 2-4 run IN PARALLEL (ThreadPoolExecutor)               │
│  │                                                │                │
│  │  ┌──────────────┐  ┌─────────────┐  ┌──────────────┐          │
│  │  │ Module 2:    │  │ Module 3:   │  │ Module 4:    │          │
│  │  │ SEO Keywords│  │ Competitors │  │ Social/Content│          │
│  │  │ (30%→65%)   │  │ (30%→65%)  │  │ (30%→65%)    │          │
│  │  └──────────────┘  └─────────────┘  └──────────────┘          │
│  │        │                  │                 │                  │
│  └────────┼──────────────────┼─────────────────┼──────────────────┘
│           │                  │                 │
│           ▼                  ▼                 ▼
│  ┌─────────────────────────────────────────────┐
│  │ Module 5: SWOT Synthesis                    │
│  │ (85% → 95%)                                │
│  │ Receives ALL upstream module outputs:        │
│  │   company_profile, seo_keywords,            │
│  │   competitors, social_content                │
│  └──────────────────────┬──────────────────────┘
│                         │
│                         ▼
│               results dict + metadata
│               {                                          │
│                 "metadata": {...},                        │
│                 "company_profile": {...},                │
│                 "seo_keywords": {...},                    │
│                 "competitor": {...},                      │
│                 "social_content": {...},                  │
│                 "swot": {...}                             │
│               }                                          │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
```

---

## 4. Module 1: Company Profile (Scraping Layer)

```
┌───────────────────────────────────────────────────────────┐
│  research/company_profile.py  —  run(url, llm_complete)   │
│                                                            │
│  1. Scrape the target URL                                  │
│     │                                                      │
│     ▼                                                      │
│  ┌─────────────────────────────────────────────────┐      │
│  │  scraper/scraper.py  —  scrape(url)              │      │
│  │                                                   │      │
│  │  a. normalize_url() → add https:// if missing    │      │
│  │  b. _scrape_with_requests()                       │      │
│  │     └─ GET the URL with custom User-Agent         │      │
│  │     └─ _clean_html() → strip scripts/styles,     │      │
│  │        unwrap nav/header/footer → plain text      │      │
│  │  c. If result is sparse (<200 chars) AND          │      │
│  │     Playwright fallback is enabled:               │      │
│  │     └─ scrape_with_playwright() → headless Chrome │      │
│  │                                                   │      │
│  │  Returns: raw text string (max 50,000 chars)      │      │
│  └─────────────────────────────────────────────────┘      │
│                                                            │
│  2. If scrape failed: use domain name as hint              │
│                                                            │
│  3. Build prompt with scraped text                         │
│     └─ LLM call: llm_complete(prompt, "company_profile")  │
│                                                            │
│  4. Parse JSON response → validate required keys            │
│                                                            │
│  Returns: {                                                │
│    "company_name": "...",                                  │
│    "what_they_do": "...",                                  │
│    "target_audience": "...",                               │
│    "value_proposition": "...",                             │
│    "brand_voice": "...",                                   │
│    "primary_cta": "...",                                   │
│    "services_products": [...],                             │
│    "marketing_channels": [...],                            │
│    "data_confidence": "..."                                │
│  }                                                         │
└───────────────────────────────────────────────────────────┘
```

### Scraping Subsystem (Phase 9J-1 and 9J-2)

```
┌─────────────────────────────────────────────────────────────────┐
│  scraper/scraper.py  —  scrape_structured(url)                  │
│                                                                  │
│  (Currently unused by company_profile, but available for 9J-3)  │
│                                                                  │
│  Same as scrape() but returns ScrapeResult with:                │
│    title, meta_description, meta_keywords, og_tags,            │
│    headings, internal_links, external_links, social_links,       │
│    phone_numbers, emails, json_ld, body_text, pages[]            │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  scraper/extractors.py                               │       │
│  │                                                       │       │
│  │  extract_meta(soup)         → title, desc, keywords  │       │
│  │  extract_links(soup, base)   → internal, external     │       │
│  │  extract_social_links(soup) → SocialLink[]            │       │
│  │  extract_contact_info(soup) → phones, emails          │       │
│  │  extract_json_ld(soup)      → structured data dicts  │       │
│  │  extract_headings(soup)     → {h1: [], h2: [], h3:[]}│      │
│  └──────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  scraper/crawler.py  —  crawl_site(url, max_pages, max_depth)   │
│                                                                  │
│  (Currently unused, ready for 9J-3 integration)                 │
│                                                                  │
│  1. Fetch homepage → extract all structured metadata             │
│  2. Check robots.txt for disallowed paths                        │
│  3. Try to fetch /sitemap.xml for seed URLs                     │
│  4. Discover subpages from <nav>, <footer>, internal links,     │
│     sitemap, and common paths (/about, /services, etc.)          │
│  5. BFS crawl subpages (requests only, 1s polite delay)          │
│  6. Merge emails, phones, social_links from subpages             │
│  7. Return ScrapeResult with pages[] for each subpage            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Modules 2-4: Parallel Research (LLM-Only)

Each receives `company_profile` + `target_url` and prompts the LLM.

```
┌────────────────────────────────────────────────────────────────┐
│  Module 2: research/seo_keywords.py                            │
│                                                                │
│  Input:  company_profile dict, target_url, llm_complete        │
│  Prompt: "You are an expert SEO analyst..."                    │
│  Output: {                                                     │
│    "top_keywords": [...],                                       │
│    "content_gaps": [...],                                       │
│    "seo_weaknesses": [...],                                     │
│    "quick_wins": [...],                                         │
│    "estimated_traffic_tier": "...",                             │
│    "local_seo_signals": "...",                                  │
│  }                                                              │
├────────────────────────────────────────────────────────────────┤
│  Module 3: research/competitors.py                              │
│                                                                │
│  Input:  company_profile dict, target_url, llm_complete        │
│  Prompt: "You are an expert competitive intelligence analyst…" │
│  Output: {                                                     │
│    "competitors": [                                             │
│      {name, url, positioning, pricing_tier,                    │
│       key_messaging, weaknesses, inferred_services},           │
│      ...                                                       │
│    ],                                                          │
│  }                                                              │
├────────────────────────────────────────────────────────────────┤
│  Module 4: research/social_content.py                          │
│                                                                │
│  Input:  company_profile dict, target_url, llm_complete        │
│  Prompt: "You are a content and social media analyst…"         │
│  Output: {                                                     │
│    "platforms": [...],                                          │
│    "content_quality": "...",                                    │
│    "content_frequency": "...",                                  │
│    "engagement_signals": "...",                                 │
│    "review_sites": [...],                                       │
│    "blog_or_resources": "...",                                  │
│    "content_gaps": [...],                                       │
│    "email_signals": "...",                                      │
│  }                                                              │
└────────────────────────────────────────────────────────────────┘
```

---

## 6. Module 5: SWOT Synthesis

```
┌────────────────────────────────────────────────────────────────┐
│  research/swot.py  —  run(all_results, target_url, llm)       │
│                                                                │
│  Input: ALL upstream module dicts + target_url                 │
│  Prompt: "You are a senior marketing strategist at an          │
│           AI automation agency..."                              │
│                                                                │
│  Output: {                                                     │
│    "swot": {                                                   │
│      "strengths": [...],     ← synthesized from profile + SEO │
│      "weaknesses": [...],    ← from SEO gaps, content audit    │
│      "opportunities": [...], ← from competitors' weaknesses    │
│      "threats": [...]        ← from competitor strengths       │
│    },                                                          │
│    "acquisition_angle": "...",                                 │
│    "talking_points": [...],                                    │
│    "recommended_next_steps": [...],                            │
│    "competitive_advantage": "...",                             │
│    "lead_generation_strategy": "...",                          │
│    "close_rate_strategy": "...",  ← AI-powered tactics        │
│    "data_confidence": "...",                                   │
│    "data_limitations": [...]                                   │
│  }                                                              │
└────────────────────────────────────────────────────────────────┘
```

---

## 7. LLM Router (Every Module Call Goes Through This)

```
┌──────────────────────────────────────────────────────────┐
│  llm/router.py  —  complete(prompt, module, ...)         │
│                                                           │
│  1. Resolve provider + model for this module              │
│     └─ config.yaml → modules.{module}.provider/model      │
│        or defaults.provider/model                         │
│     └─ Override if provider_override/model_override set    │
│                                                           │
│  2. Build messages:                                       │
│     [{role: "system", content: SYSTEM_PROMPT},            │
│      {role: "user",   content: prompt}]                   │
│                                                           │
│  3. Call LiteLLM completion()                              │
│     └─ Routes to: OpenAI, DeepSeek, Anthropic,            │
│        Groq, Ollama, etc.                                 │
│                                                           │
│  4. On failure: try next provider in fallback chain        │
│                                                           │
│  Returns: raw LLM text response                           │
└──────────────────────────────────────────────────────────┘
```

---

## 8. Report Generation

```
┌──────────────────────────────────────────────────────────────┐
│  report/writer.py  —  write_report(results, output_dir)      │
│                                                               │
│  1. Infer company name from profile dict                      │
│  2. Slugify → "acme-widgets"                                  │
│  3. Create reports/acme-widgets/ directory                     │
│  4. Build Markdown from results dict:                         │
│                                                               │
│     ┌──────────────────────────────────────────────────┐     │
│     │  # ReconIQ Report: Acme Widgets                    │     │
│     │                                                     │     │
│     │  ## 1. Company Overview                             │     │
│     │     _section_content(profile)  → key/value lines   │     │
│     │                                                     │     │
│     │  ## 2. SEO & Keyword Analysis                      │     │
│     │     _section_content(seo)                          │     │
│     │                                                     │     │
│     │  ## 3. Competitor Landscape                        │     │
│     │     _competitor_section(competitor)                │     │
│     │     └─ numbered list of competitor dicts          │     │
│     │                                                     │     │
│     │  ## 4. Social & Content Audit                     │     │
│     │     _section_content(social)                       │     │
│     │                                                     │     │
│     │  ## 5. SWOT Analysis                               │     │
│     │     ### Strengths (Internal, Helpful)              │     │
│     │     - item 1                                       │     │
│     │     - item 2                                       │     │
│     │     ### Weaknesses (Internal, Harmful)              │     │
│     │     ...                                            │     │
│     │     ### Opportunities (External, Helpful)           │     │
│     │     ...                                            │     │
│     │     ### Threats (External, Harmful)                │     │
│     │     ...                                            │     │
│     │                                                     │     │
│     │  ## 6. Client Acquisition Strategy                  │     │
│     │     **Recommended Angle:** ...                      │     │
│     │     **Your Competitive Edge:** ...                 │     │
│     │     **Lead Generation Strategy:** ...              │     │
│     │     **AI Close Rate Strategy:** ...                │     │
│     │     **Talking Points:**                             │     │
│     │     - ...                                           │     │
│     │                                                     │     │
│     │  ## 7. Next Steps                                  │     │
│     │     1. ...                                          │     │
│     │     2. ...                                          │     │
│     │                                                     │     │
│     │  ---                                                │     │
│     │  *Report generated by ReconIQ | timestamp*          │     │
│     └──────────────────────────────────────────────────┘     │
│                                                               │
│  5. Write to reports/acme-widgets/2026-04-30-143022.md        │
│  6. Return absolute file path                                 │
└──────────────────────────────────────────────────────────────┘
```

---

## 9. UI Renders the Report

```
┌──────────────────────────────────────────────────────────┐
│  app.py  —  Report Display                                │
│                                                           │
│  1. Read the .md file from disk                           │
│  2. Store in st.session_state.report_content              │
│  3. Render as Streamlit markdown in a styled card         │
│  4. Show download button (↓ Download .md)                 │
│  5. Show "Open Folder" button (opens in file manager)    │
│  6. Surface any failed/skipped modules as warnings        │
│  7. Progress bar → 100%                                   │
│  8. Status message: "Report saved to `reports/...`"      │
└──────────────────────────────────────────────────────────┘
```

---

## 10. End-to-End Flow (Condensed)

```
User clicks [Analyze →]
       │
       ▼
app.py: validate_url → build_analysis_request → AnalysisRequest
       │
       ▼
core/services.py: run_analysis()
       │
       ├─→ coordinator.run_all()
       │       │
       │       ├─→ Module 1: Company Profile
       │       │       └─→ scraper.scrape(url) → raw text
       │       │       └─→ LLM call → {company_name, what_they_do, ...}
       │       │
       │       ├─→ Module 2: SEO Keywords ───┐
       │       ├─→ Module 3: Competitors ─────┤  (parallel)
       │       └─→ Module 4: Social Content ──┘
       │               └─→ Each: LLM call with profile context
       │               └─→ Each returns structured dict
       │       │
       │       └─→ Module 5: SWOT Synthesis
       │               └─→ LLM call with ALL module outputs
       │               └─→ {swot, acquisition_angle, talking_points, ...
       │                    lead_generation_strategy, close_rate_strategy}
       │
       ├─→ report/writer.py: write_report(results)
       │       └─→ Markdown → reports/{slug}/{timestamp}.md
       │
       └─→ AnalysisResult(results, report_path)
               │
               ▼
app.py: Display report in Streamlit + download/open buttons
```

---

## Key Files Quick Reference

| File | Role |
|------|------|
| `app.py` | Streamlit UI — input, progress, report display |
| `core/models.py` | `AnalysisRequest` / `AnalysisResult` dataclasses |
| `core/services.py` | `run_analysis()` — wires request → coordinator → report |
| `core/settings.py` | `load_config()` — reads `config.yaml` |
| `llm/router.py` | `complete()` — LiteLLM routing to providers |
| `scraper/scraper.py` | `scrape()` / `scrape_structured()` — fetch + extract |
| `scraper/crawler.py` | `crawl_site()` — multi-page BFS crawler |
| `scraper/extractors.py` | Structured extraction from HTML (meta, links, contacts, etc.) |
| `scraper/models.py` | `ScrapeResult`, `PageData`, `LinkData`, `SocialLink` dataclasses |
| `research/coordinator.py` | `run_all()` — dependency-aware module orchestration |
| `research/company_profile.py` | Module 1 — scrape + LLM profile |
| `research/seo_keywords.py` | Module 2 — SEO analysis via LLM |
| `research/competitors.py` | Module 3 — competitor intelligence via LLM |
| `research/social_content.py` | Module 4 — social/content audit via LLM |
| `research/swot.py` | Module 5 — SWOT synthesis via LLM |
| `research/parsing.py` | `extract_json_object()`, `require_keys()` — LLM output parsing |
| `report/writer.py` | `write_report()` — results dict → Markdown file |
| `config.yaml` | Provider defaults, module overrides, scraper settings |