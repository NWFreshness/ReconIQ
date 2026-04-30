# ReconIQ Dataflow — Every Function Call

Trace of every function call from button click to finished report.

---

## Stage 1: User Clicks [Analyze →]

```
app.py
│
├─ st.text_input("Target URL")  →  "https://acme.com"
├─ st.button("Analyze →")       →  True
├─ st.checkbox toggles          →  {"company_profile": True, "seo_keywords": True, ...}
│
├─ validate_url("https://acme.com")
│   └─ normalize_url("https://acme.com")  →  "https://acme.com"
│   └─ urlparse("https://acme.com")
│   └─ returns (True, "https://acme.com")
│
├─ build_analysis_request(
│      target_url="https://acme.com",
│      enabled_modules={"company_profile": True, "seo_keywords": True, ...},
│      provider="deepseek",
│      model="",
│      output_dir="/home/user/ReconIQ/reports",
│  )
│  └─ returns AnalysisRequest(
│         target_url="https://acme.com",
│         enabled_modules={...},
│         provider_override=None,        # "deepseek" is default, so None
│         model_override=None,
│         output_dir="/home/user/ReconIQ/reports",
│         max_pages=5,
│         max_depth=2,
│     )
```

---

## Stage 2: run_analysis()

```
core/services.py  —  run_analysis(request, progress_callback)

│
├─ configured_llm_complete(prompt, module, system, max_tokens, temperature)
│   │  └─ wraps llm_router.complete() with request.provider_override and model_override
│   │
│   │   llm/router.py  —  complete(prompt, module, system, max_tokens, temperature,
│   │                            provider_override=None, model_override=None)
│   │
│   │   ├─ get_module_provider_model(module, config)
│   │   │   └─ e.g. module="company_profile" → ("deepseek", None)
│   │   │   └─ checks config.yaml → modules.company_profile.provider/model
│   │   │
│   │   ├─ resolve_model(provider="deepseek", model=None, config)
│   │   │   └─ config["providers"]["deepseek"]["default_model"]  →  "deepseek-chat"
│   │   │   └─ returns "deepseek/deepseek-chat"
│   │   │
│   │   ├─ build_completion_kwargs(provider, model, messages, config)
│   │   │   └─ {"model": "deepseek/deepseek-chat", "messages": [...]}
│   │   │
│   │   ├─ litellm.completion(model="deepseek/deepseek-chat", messages=[...])
│   │   │   └─ HTTP POST to DeepSeek API
│   │   │   └─ returns LLM response text
│   │   │
│   │   └─ returns str  (raw LLM text)
│
├─ run_all(
│      target_url="https://acme.com",
│      llm_complete=configured_llm_complete,
│      enabled_modules={"company_profile": True, ...},
│      progress_callback=progress_callback,
│  )
│   │  (see Stage 3)
│   └─ returns results dict
│
├─ write_report(results, output_dir="/home/user/ReconIQ/reports")
│   │  (see Stage 8)
│   └─ returns "/home/user/ReconIQ/reports/acme/2026-04-30-143022.md"
│
└─ returns AnalysisResult(
       results={...},
       report_path="/home/user/ReconIQ/reports/acme/2026-04-30-143022.md"
   )
```

---

## Stage 3: coordinator.run_all()

```
research/coordinator.py  —  run_all(target_url, llm_complete, enabled_modules, progress_callback)

│
├─ _initial_metadata("https://acme.com", llm_complete)
│   └─ returns {"target_url": "https://acme.com",
│               "timestamp": "2026-04-30 14:30:22",
│               "modules_run": [],
│               "modules_skipped": [],
│               "modules_failed": [],
│               "data_limitations": []}
│
├─ progress_callback("Running Company Profile...", 10.0)
│
│  ─── MODULE 1: Company Profile (sequential, must finish first) ───
│
├─ company_profile.run("https://acme.com", llm_complete)
│   │  (see Stage 4)
│   └─ returns {"company_name": "Acme Corp", "what_they_do": "...", ...}
│
├─ progress_callback("✓ Company Profile complete", 25.0)
│
│  ─── MODULES 2-4: Parallel via ThreadPoolExecutor ───
│
├─ ThreadPoolExecutor(max_workers=3)
│   │
│   ├─ Future 1: seo_keywords.run(profile, "https://acme.com", llm_complete)
│   │   │  (see Stage 5)
│   │   └─ returns {"top_keywords": [...], "seo_weaknesses": [...], ...}
│   │
│   ├─ Future 2: competitors.run(profile, "https://acme.com", llm_complete)
│   │   │  (see Stage 6)
│   │   └─ returns {"competitors": [{name, url, ...}, ...], ...}
│   │
│   └─ Future 3: social_content.run(profile, "https://acme.com", llm_complete)
│       │  (see Stage 7)
│       └─ returns {"platforms": [...], "content_quality": "...", ...}
│
├─ progress_callback("✓ SEO Keywords complete", ~55%)
├─ progress_callback("✓ Competitor Intel complete", ~70%)
├─ progress_callback("✓ Social Content complete", ~75%)
│
│  ─── MODULE 5: SWOT (after all upstream modules) ───
│
├─ swot.run(profile, seo, competitor, social, "https://acme.com", llm_complete)
│   │  (see Stage 8)
│   └─ returns {"swot": {...}, "acquisition_angle": "...", ...}
│
├─ progress_callback("✓ SWOT Synthesis complete", 95.0)
├─ progress_callback("All modules complete!", 100.0)
│
└─ returns {
      "metadata": {...},
      "company_profile": {...},
      "seo_keywords": {...},
      "competitor": {...},
      "social_content": {...},
      "swot": {...}
   }
```

---

## Stage 4: Module 1 — company_profile.run()

```
research/company_profile.py  —  run("https://acme.com", llm_complete)

│
├─ scraper.scraper.scrape("https://acme.com")
│   │
│   ├─ normalize_url("https://acme.com")  →  "https://acme.com"
│   │
│   ├─ _scrape_with_requests("https://acme.com", timeout=15)
│   │   ├─ requests.get("https://acme.com", headers={...}, timeout=15)
│   │   │   └─ HTML response (e.g. 50KB of HTML)
│   │   ├─ response.encoding = response.apparent_encoding or "utf-8"
│   │   └─ _clean_html(response.text)
│   │       ├─ BeautifulSoup(html, "html.parser")
│   │       ├─ decompose <script>, <style>, <noscript> tags
│   │       ├─ unwrap <nav>, <header>, <footer>, <aside> tags
│   │       ├─ soup.get_text(separator="\n", strip=True)
│   │       └─ truncate to MAX_LENGTH (50,000 chars)
│   │       └─ returns "Welcome to Acme Corp\nWe build widgets...\nContact us..."
│   │
│   ├─ IF text is sparse (<200 chars) AND should_use_playwright():
│   │   └─ scrape_with_playwright("https://acme.com", timeout=25)
│   │       ├─ sync_playwright().chromium.launch(headless=True)
│   │       ├─ page.goto(url, wait_until="domcontentloaded")
│   │       ├─ page.wait_for_timeout(3000)
│   │       ├─ html = page.content()
│   │       ├─ browser.close()
│   │       └─ _clean_html(html)
│   │       └─ returns richer text or ""
│   │
│   └─ returns str  (cleaned text, or "" on failure)
│
├─ IF content is empty:
│   └─ extract_domain_name("https://acme.com")
│       ├─ urlparse("https://acme.com")
│       └─ "acme.com"
│       └─ fallback prompt: "Could not access https://acme.com. The company's domain is: acme.com..."
│
├─ llm_complete(
│      prompt=f"TARGET URL: https://acme.com\n\nWEBSITE CONTENT:\n{text}\n\nExtract company profile...",
│      module="company_profile",
│      system=SYSTEM_PROMPT,
│      max_tokens=1500,
│  )
│  └─ returns raw LLM text containing JSON
│
├─ _parse_response(raw)
│   ├─ extract_json_object(raw)
│   │   └─ finds first {...} in LLM text → parses with json.JSONDecoder
│   │   └─ returns dict
│   └─ require_keys(data, REQUIRED_KEYS, context="Company profile")
│       ├─ REQUIRED_KEYS = ["company_name", "what_they_do", "target_audience", ...]
│       └─ raises JsonParsingError if any key missing
│
└─ returns {
       "company_name": "Acme Corp",
       "what_they_do": "Builds durable widgets for local businesses",
       "target_audience": "Small to mid-size businesses",
       "value_proposition": "Affordable, long-lasting widgets",
       "brand_voice": "Professional, friendly",
       "primary_cta": "Request a Quote",
       "services_products": ["Custom Widgets", "Widget Repair", ...],
       "marketing_channels": ["website", "Facebook", "Google Ads"],
       "data_confidence": "medium",
       "data_limitations": ["Single-page scrape only"],
   }
```

---

## Stage 5: Module 2 — seo_keywords.run()

```
research/seo_keywords.py  —  run(company_profile, "https://acme.com", llm_complete)

│
├─ _format_profile(company_profile)
│   └─ "- company_name: Acme Corp\n- what_they_do: Builds widgets..."
│
├─ llm_complete(
│      prompt=f"TARGET URL: https://acme.com\nCOMPANY PROFILE:\n{profile_text}\nInfer the SEO landscape...",
│      module="seo_keywords",
│      system=SYSTEM_PROMPT,
│      max_tokens=1200,
│  )
│
├─ _parse_response(raw)
│   ├─ extract_json_object(raw)  →  dict
│   └─ require_keys(data, REQUIRED_KEYS, context="SEO keywords")
│       └─ REQUIRED_KEYS = ["top_keywords", "content_gaps", "seo_weaknesses", ...]
│
└─ returns {
       "top_keywords": ["widgets", "custom widgets", "affordable widgets", ...],
       "content_gaps": ["comparison pages", "case studies", ...],
       "seo_weaknesses": ["thin service pages", "no blog", ...],
       "quick_wins": ["add local landing pages", "optimize title tags", ...],
       "estimated_traffic_tier": "low",
       "local_seo_signals": "weak",
       "data_confidence": "low",
       "data_limitations": ["Keywords inferred from profile, not verified"],
   }
```

---

## Stage 6: Module 3 — competitors.run()

```
research/competitors.py  —  run(company_profile, "https://acme.com", llm_complete)

│
├─ _format_profile(company_profile)
│   └─ "- company_name: Acme Corp\n- what_they_do: Builds widgets..."
│
├─ llm_complete(
│      prompt=f"TARGET URL: https://acme.com\nCOMPANY PROFILE:\n{profile_text}\nIdentify direct competitors...",
│      module="competitor",
│      system=SYSTEM_PROMPT,
│      max_tokens=2500,
│  )
│
├─ _parse_response(raw)
│   ├─ extract_json_object(raw)  →  dict
│   ├─ require_keys(data, ["competitors", "data_confidence", "data_limitations"])
│   └─ for each competitor in data["competitors"]:
│       └─ require_keys(comp, REQUIRED_COMPETITOR_KEYS)
│           └─ ["name", "url", "positioning", "estimated_pricing_tier", ...]
│
└─ returns {
       "competitors": [
           {
               "name": "WidgetWorld",
               "url": "https://widgetworld.com",
               "positioning": "Premium widget supplier for enterprise",
               "estimated_pricing_tier": "premium",
               "key_messaging": "Enterprise-grade widgets",
               "weaknesses": ["Expensive", "No local focus"],
               "inferred_services": ["Enterprise widgets", "Consulting", ...],
           },
           ...
       ],
       "data_confidence": "low",
       "data_limitations": ["Competitors inferred, not scraped"],
   }
```

---

## Stage 7: Module 4 — social_content.run()

```
research/social_content.py  —  run(company_profile, "https://acme.com", llm_complete)

│
├─ _format_profile(company_profile)
│
├─ llm_complete(
│      prompt=f"TARGET URL: https://acme.com\nCOMPANY PROFILE:\n{profile_text}\nInfer social presence...",
│      module="social_content",
│      system=SYSTEM_PROMPT,
│      max_tokens=1200,
│  )
│
├─ _parse_response(raw)
│   ├─ extract_json_object(raw)  →  dict
│   └─ require_keys(data, REQUIRED_KEYS)
│       └─ ["platforms", "content_quality", "content_frequency", ...]
│
└─ returns {
       "platforms": ["Facebook", "Instagram"],
       "content_quality": "low",
       "content_frequency": "sporadic",
       "engagement_signals": "weak",
       "review_sites": ["Google Reviews"],
       "blog_or_resources": "none",
       "content_gaps": ["Video content", "Case studies"],
       "email_signals": "newsletter signup present",
       "data_confidence": "low",
       "data_limitations": ["Inferred from limited signals"],
   }
```

---

## Stage 8: Module 5 — swot.run()

```
research/swot.py  —  run(company_profile, seo_keywords, competitor, social_content, target_url, llm_complete)

│
├─ _format_dict(company_profile)
│   └─ "- company_name: Acme Corp\n  - what_they_do: Builds widgets..."
│
├─ _format_dict(seo_keywords)
│   └─ "- top_keywords:\n  - widgets\n  - custom widgets..."
│
├─ _format_dict(competitor)
│   └─ "- competitors:\n  - {\"name\": \"WidgetWorld\", ...}"
│
├─ _format_dict(social_content)
│   └─ "- platforms:\n  - Facebook\n  - Instagram..."
│
├─ llm_complete(
│      prompt=f"TARGET URL: https://acme.com\n\n--- COMPANY PROFILE ---\n...\n\n"
│               f"--- SEO & KEYWORDS ---\n...\n\n"
│               f"--- COMPETITOR INTELLIGENCE ---\n...\n\n"
│               f"--- SOCIAL & CONTENT ---\n...\n\n"
│               f"Synthesize into an acquisition strategy as instructed.",
│      module="swot",
│      system=SYSTEM_PROMPT,   # "You are a senior marketing strategist at an AI automation agency..."
│      max_tokens=2000,
│  )
│
├─ _parse_response(raw)
│   ├─ extract_json_object(raw)  →  dict
│   ├─ require_keys(data, REQUIRED_KEYS)
│   │   └─ ["swot", "acquisition_angle", "talking_points", "recommended_next_steps",
│   │       "competitive_advantage", "lead_generation_strategy", "close_rate_strategy",
│   │       "data_confidence", "data_limitations"]
│   ├─ require_keys(data["swot"], ["strengths", "weaknesses", "opportunities", "threats"])
│   └─ returns validated dict
│
└─ returns {
       "swot": {
           "strengths": ["clear niche", "strong local presence"],
           "weaknesses": ["thin content", "no blog"],
           "opportunities": ["local SEO expansion", "content marketing"],
           "threats": ["larger regional competitors", "price undercutting"],
       },
       "acquisition_angle": "Lead with a free local SEO audit...",
       "talking_points": ["Your service pages could capture more intent", ...],
       "recommended_next_steps": ["Build a local landing page plan", ...],
       "competitive_advantage": "A focused AI automation agency can move faster...",
       "lead_generation_strategy": "Target local businesses via Google Ads...",
       "close_rate_strategy": "Use AI lead scoring to prioritize high-intent prospects...",
       "data_confidence": "medium",
       "data_limitations": ["Strategy inferred from module outputs"],
   }
```

---

## Stage 9: Report Generation

```
report/writer.py  —  write_report(results, output_dir="reports")

│
├─ _infer_company_name(results["company_profile"])
│   └─ profile.get("company_name", "Unknown Company")  →  "Acme Corp"
│
├─ re.sub(r"[^a-z0-9]+", "-", "acme corp".lower()).strip("-")
│   └─ "acme-corp"
│
├─ time.strftime("%Y-%m-%d-%H%M%S")
│   └─ "2026-04-30-143022"
│
├─ Path("reports/acme-corp").mkdir(parents=True, exist_ok=True)
│   └─ creates reports/acme-corp/ directory
│
├─ _build_markdown(results, "Acme Corp")
│   │
│   ├─ _section_content(company_profile)
│   │   └─ "**Company Name:** Acme Corp\n**What They Do:** Builds widgets..."
│   │
│   ├─ _section_content(seo_keywords)
│   │   └─ "**Top Keywords:**\n- widgets\n- custom widgets..."
│   │
│   ├─ _competitor_section(competitor)
│   │   └─ "### 1. WidgetWorld\n- **Positioning:** Premium...\n- **Pricing Tier:** premium..."
│   │
│   ├─ _section_content(social_content)
│   │   └─ "**Platforms:**\n- Facebook\n- Instagram..."
│   │
│   ├─ _swot_section(swot)
│   │   └─ "### Strengths (Internal, Helpful)\n- clear niche\n..."
│   │
│   ├─ _acquisition_section(swot)
│   │   └─ "**Recommended Angle:** ...\n**Your Competitive Edge:** ...\n"
│   │      "**Lead Generation Strategy:** ...\n**AI Close Rate Strategy:** ...\n"
│   │      "**Talking Points:**\n- ..."
│   │
│   ├─ _next_steps_section(swot)
│   │   └─ "1. Build a local landing page plan\n2. ..."
│   │
│   └─ returns full Markdown string
│
├─ report_path.write_text(markdown, encoding="utf-8")
│   └─ writes to reports/acme-corp/2026-04-30-143022.md
│
└─ returns "/home/user/ReconIQ/reports/acme-corp/2026-04-30-143022.md"
```

---

## Stage 10: UI Renders the Report

```
app.py  (back in the Streamlit callback)

│
├─ open(report_path).read()  →  full Markdown string
├─ st.session_state.report_path = report_path
├─ st.session_state.report_content = markdown_string
│
├─ progress_bar.progress(100.0, text="Analysis complete")
├─ status_container.success("Report saved to `reports/acme-corp/2026-04-30-143022.md`")
│
├─ IF modules_failed:
│   └─ st.warning("Modules that failed: **competitor**")
├─ IF modules_skipped:
│   └─ st.info("Modules skipped: **social_content**")
│
├─ st.rerun()  ← triggers re-render with report_content available
│
│  ─── On re-render: ───
│
├─ st.markdown("---")
├─ st.download_button("↓ Download .md", data=report_content, ...)
├─ st.button("📁 Open Folder")  →  open_folder(reports/acme-corp/)
├─ st.markdown(report_content)  ← renders the full report as Markdown
```

---

## The Scraping Subsystem (Currently Unused by Main Flow, Available for 9J-3)

These are called only if a module switches from `scrape()` to `scrape_structured()` or `crawl_site()`:

```
scraper/scraper.py  —  scrape_structured("https://acme.com")

│
├─ normalize_url("https://acme.com")
├─ _fetch_html("https://acme.com", timeout=15)
│   └─ requests.get(...)  →  raw HTML string
│
├─ IF html is empty AND should_use_playwright():
│   └─ scrape_with_playwright("https://acme.com", timeout=25)
│       └─ Playwright headless Chrome  →  JS-rendered HTML
│
├─ BeautifulSoup(html, "html.parser")  →  soup
│
├─ extract_meta(soup)
│   └─ {"title": "Acme Corp", "meta_description": "...", "meta_keywords": [...], "og_tags": {...}}
│
├─ extract_links(soup, "https://acme.com")
│   └─ (internal_links=[LinkData(href="/about", text="About Us"), ...],
│       external_links=[LinkData(href="https://vendor.com", text="Vendor"), ...])
│
├─ extract_social_links(soup)
│   └─ [SocialLink(platform="facebook", url="https://facebook.com/acme"), ...]
│
├─ extract_contact_info(soup)
│   └─ (phones=["(555) 123-4567"], emails=["info@acme.com"])
│
├─ extract_json_ld(soup)
│   └─ [{"@type": "LocalBusiness", "name": "Acme Corp", ...}]
│
├─ extract_headings(soup)
│   └─ {"h1": ["Welcome to Acme"], "h2": ["Our Services", "Contact"]}
│
├─ _clean_html(html)  →  body_text string
│
└─ returns ScrapeResult(
       url="https://acme.com",
       title="Acme Corp",
       meta_description="...",
       meta_keywords=[...],
       og_tags={...},
       headings={...},
       internal_links=[...],
       external_links=[...],
       social_links=[...],
       phone_numbers=[...],
       emails=[...],
       json_ld=[...],
       body_text="Welcome to Acme Corp...",
       pages=[],
       raw_html_length=50000,
       crawl_duration_s=1.2,
   )
```

```
scraper/crawler.py  —  crawl_site("https://acme.com", max_pages=5, max_depth=2)

│
├─ normalize_url("https://acme.com")
├─ _fetch_html("https://acme.com", timeout=15)  →  homepage_html
│
├─ [if homepage sparse AND should_use_playwright()]
│   └─ scrape_with_playwright(...)
│
├─ BeautifulSoup(homepage_html)  →  homepage_soup
├─ extract_meta(homepage_soup)  →  {...}
├─ extract_links(homepage_soup, url)  →  (internal, external)
├─ extract_social_links(homepage_soup)  →  [SocialLink(...), ...]
├─ extract_contact_info(homepage_soup)  →  (phones, emails)
├─ extract_json_ld(homepage_soup)  →  [...]
├─ extract_headings(homepage_soup)  →  {...}
├─ _clean_html(homepage_html)  →  body_text
│
├─ ScrapeResult(...)  ← homepage data assembled
│
├─ fetch_robots_txt("https://acme.com")
│   └─ requests.get("https://acme.com/robots.txt")
│   └─ RobotFileParser.parse()  →  parser or None
│
├─ fetch_sitemap_urls("https://acme.com")
│   └─ requests.get("https://acme.com/sitemap.xml")
│   └─ BeautifulSoup(xml, "xml").find_all("loc")  →  [url1, url2, ...]
│
├─ _discover_seed_urls(soup, url, robots_parser, sitemap_urls)
│   ├─ soup.find_all(["nav", "footer"])  →  nav/footer links
│   ├─ extract_links(soup, url)  →  all internal links
│   ├─ sitemap URLs added
│   └─ common paths: /about, /services, /contact, /blog probed
│   └─ is_allowed_by_robots(parser, url) checked for each
│   └─ returns prioritized list of subpage URLs
│
├─ FOR each subpage URL (BFS, max_pages=5, max_depth=2):
│   ├─ _scrape_subpage(url, base_url, timeout=10)
│   │   ├─ _fetch_html(url, timeout=10)  →  html
│   │   ├─ BeautifulSoup(html)  →  soup
│   │   ├─ extract_meta(soup)  →  {title, ...}
│   │   ├─ extract_headings(soup)  →  {...}
│   │   ├─ extract_contact_info(soup)  →  (phones, emails)
│   │   ├─ extract_social_links(soup)  →  [SocialLink(...), ...]
│   │   └─ returns _SubpageResult(page_data, emails, phones, social_links, ...)
│   │
│   ├─ time.sleep(1.0)  ← polite delay
│   │
│   ├─ merge emails into result.emails (dedup)
│   ├─ merge phones into result.phone_numbers (dedup)
│   ├─ merge social_links into result.social_links (dedup by URL)
│   │
│   └─ IF depth < max_depth:
│       ├─ BeautifulSoup(sub_html)  →  sub_soup
│       ├─ extract_links(sub_soup, url)  →  more internal links
│       └─ append to BFS queue
│
├─ result.pages = [PageData(...), PageData(...), ...]
├─ result.crawl_duration_s = elapsed time
│
└─ returns ScrapeResult (with pages populated + merged contact data)
```

---

## Key Files Quick Reference

| File | Key Functions | Called By |
|------|--------------|-----------|
| `app.py` | `validate_url()`, `build_analysis_request()` | Streamlit runtime |
| `core/services.py` | `run_analysis()` | app.py |
| `core/models.py` | `AnalysisRequest`, `AnalysisResult` | services, app |
| `llm/router.py` | `complete()`, `resolve_model()` | all research modules |
| `scraper/scraper.py` | `scrape()`, `scrape_structured()`, `_fetch_html()`, `_clean_html()` | company_profile |
| `scraper/crawler.py` | `crawl_site()`, `_discover_seed_urls()`, `fetch_robots_txt()`, `fetch_sitemap_urls()` | (9J-3 integration) |
| `scraper/extractors.py` | `extract_meta()`, `extract_links()`, `extract_social_links()`, `extract_contact_info()`, `extract_json_ld()`, `extract_headings()` | scraper, crawler |
| `scraper/models.py` | `ScrapeResult`, `PageData`, `LinkData`, `SocialLink` | scraper, crawler |
| `research/coordinator.py` | `run_all()` | services |
| `research/company_profile.py` | `run()`, `_parse_response()` | coordinator |
| `research/seo_keywords.py` | `run()`, `_parse_response()` | coordinator |
| `research/competitors.py` | `run()`, `_parse_response()` | coordinator |
| `research/social_content.py` | `run()`, `_parse_response()` | coordinator |
| `research/swot.py` | `run()`, `_parse_response()` | coordinator |
| `research/parsing.py` | `extract_json_object()`, `require_keys()` | all modules |
| `report/writer.py` | `write_report()`, `_build_markdown()`, `_swot_section()`, `_acquisition_section()` | services |
| `config.yaml` | Provider/model/scraper settings | router, scraper |