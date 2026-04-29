ReconIQ — Marketing Intelligence Platform

**Design v1.0 | 2026-04-29**

---

## Overview

ReconIQ is a local AI-powered marketing intelligence tool. Input a target company's URL and receive a structured report covering company overview, SEO/keywords, competitor landscape, social/content audit, and a synthesized SWOT with client acquisition strategy.

**Goal:** Surface weaknesses to exploit and the best angle to acquire the target company as a client.

---

## Architecture

```
URL Input (Streamlit UI)
       │
       ▼
┌──────────────────────────────────────────────┐
│  Coordinator (sequential trigger,            │
│  parallel module execution, then synthesis)   │
└────────────────────┬─────────────────────────┘
                     │
         ┌───────────┼───────────┬───────────┐
         ▼           ▼           ▼           ▼
    [Company   [SEO/       [Competitor [Social/
     Profile]  Keywords]   Analysis]  Content]
         │           │           │           │
         └───────────┴───────────┴───────────┘
                     │
                     ▼
              [SWOT Synthesis]
                     │
                     ▼
             Markdown Report
     (~/reconiq/reports/<company>/<ts>.md)
```

**Parallel Execution:** Modules 1–4 run concurrently via `ThreadPoolExecutor`. Module 5 (SWOT) runs only after 1–4 complete.

**Sequential Trigger:** Coordinator receives URL → fires modules 1–4 in parallel → waits for all → fires SWOT → writes report.

---

## UI (Streamlit)

```
┌────────────────────────────────────────────────────────┐
│  ReconIQ                               [Ollama: ●/○] │
├────────────────────────────────────────────────────────┤
│  Target URL: [https://example.com_______________]       │
│  [ Analyze Company ]                                   │
│                                                        │
│  LLM Provider: [OpenAI ▼]  Model: [gpt-4o-mini ▼]      │
│                                                        │
│  Modules (toggle on/off):                              │
│    [x] Company Profile    [x] SEO & Keywords          │
│    [x] Competitor Intel   [x] Social & Content         │
│    [x] SWOT Synthesis                                │
│                                                        │
├────────────────────────────────────────────────────────┤
│  Progress                                             │
│  [████████████░░░░░░░░] 75% — Running Competitor Intel │
│                                                        │
│  [Streaming log output per module]                     │
│                                                        │
├────────────────────────────────────────────────────────┤
│  Report: Acme Corp                         [Download ▼]│
│  ─────────────────────────────────────────────────────│
│  ## 1. Company Overview                               │
│  ...                                                   │
│  [Open in Folder]                                     │
└────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| UI | Streamlit | Fastest to build, Python-native |
| LLM routing | `litellm` | Single interface: OpenAI, DeepSeek, Anthropic, Groq, Ollama |
| HTML scraping | `requests` + `BeautifulSoup4` | Simple pages |
| JS rendering | `playwright` (optional) | For JS-heavy pages |
| Report output | Markdown files | Filesystem-only for now |
| Config | `config.yaml` | API keys, defaults |
| Async/parallel | `concurrent.futures.ThreadPoolExecutor` | Built-in, no extra deps |

---

## LLM Provider Routing

`litellm` handles all five providers via a unified `completion()` call. The model selection per module:

| Module | Default Provider | Model |
|--------|-----------------|-------|
| Company Profile | DeepSeek | deepseek-chat |
| SEO & Keywords | DeepSeek | deepseek-chat |
| Competitor Intel | Anthropic | claude-3-5-sonnet-latest |
| Social & Content | OpenAI | gpt-4o-mini |
| SWOT Synthesis | Anthropic | claude-3-5-sonnet-latest |

User can override the global provider/model via dropdown. Per-module overrides stored in `config.yaml`.

---

## Ollama Integration

- Endpoint: `http://localhost:11434` (configurable)
- Model name: user-specified (e.g., `llama3`, `mistral`)
- Health check on startup — if Ollama is unreachable, show indicator in UI and route to cloud provider
- If Ollama is the selected provider and unreachable, fall back to DeepSeek

---

## Research Modules

### Module 1: Company Profile
- Scrape target URL (HTML + JS if needed)
- Extract: business description, services/products, target audience, value proposition, brand voice, CTAs, nav structure
- Output: structured dict

### Module 2: SEO & Keywords
- Accepts: company description + target URL
- LLM infers: likely top keywords, content strategy gaps, SEO weaknesses, backlink opportunity
- (Note: no live traffic API — all inference-based from company profile)
- Output: structured dict

### Module 3: Competitor Intelligence
- Accepts: company profile + market context
- Auto-discovers 3–5 competitors via LLM reasoning about the market
- For each competitor: estimates their positioning, pricing tier, messaging, and weaknesses
- Output: list of competitor dicts with assessment

### Module 4: Social & Content
- Accepts: company name + URL
- LLM infers: likely social platforms, content quality/frequency, review site presence, engagement signals
- Output: structured dict

### Module 5: SWOT Synthesis
- Accepts: all four module outputs
- Synthesizes into: SWOT grid + recommended client acquisition angle + specific outreach talking points
- Output: structured dict fed into report writer

---

## Report Format

```markdown
# ReconIQ Report: [Company Name]

**Target URL:** https://...
**Generated:** 2026-04-29 14:32
**Provider:** Anthropic / claude-3-5-sonnet-latest

---

## 1. Company Overview
[What they do, who they serve, value prop, brand voice]

## 2. SEO & Keyword Analysis
[Top keywords, traffic signals, content gaps, quick wins]

## 3. Competitor Landscape
### Competitor 1: [Name]
- **Positioning:** ...
- **Estimated Pricing:** ...
- **Weaknesses:** ...
[Same for 3–5 competitors]

## 4. Social & Content Audit
[Platforms, content quality, engagement, review presence]

## 5. SWOT Analysis
| | Helpful | Harmful |
|---|---|---|
| **Internal** | Strengths | Weaknesses |
| **External** | Opportunities | Threats |

## 6. Client Acquisition Strategy
[Why THIS company is a good fit, what to offer, recommended outreach angle]

## 7. Next Steps
[Specific tactics: email hook, content angle, competitive undercut, etc.]
```

Reports saved to: `~/reconiq/reports/<slugified-company-name>/<YYYY-MM-DD-HHMMSS>.md`

---

## File Structure

```
~/reconiq/
├── app.py
├── config.yaml
├── requirements.txt
├── research/
│   ├── __init__.py
│   ├── coordinator.py      # Parallel orchestration + sequential synthesis
│   ├── company_profile.py  # Module 1
│   ├── seo_keywords.py     # Module 2
│   ├── competitors.py      # Module 3
│   ├── social_content.py   # Module 4
│   └── swot.py            # Module 5
├── scraper/
│   ├── __init__.py
│   └── scraper.py         # requests + BS4 + optional playwright
├── llm/
│   ├── __init__.py
│   └── router.py          # litellm wrapper + health checks
├── report/
│   ├── __init__.py
│   └── writer.py          # Markdown generation
└── reports/               # Output directory (gitignored)
```

---

## Error Handling

| Failure Mode | Response |
|-------------|----------|
| Scraping fails | Flag report, use LLM to infer company info from domain name alone |
| Provider API error | Retry once, then fall back to next cheapest available provider |
| Ollama unreachable | Show warning in UI, route to cloud provider, disable local option |
| Module produces no output | Skip module, note in report, continue with others |

---

## Config (`config.yaml`)

```yaml
providers:
  openai:
    api_key: "${OPENAI_API_KEY}"
    default_model: "gpt-4o-mini"
  deepseek:
    api_key: "${DEEPSEEK_API_KEY}"
    default_model: "deepseek-chat"
  anthropic:
    api_key: "${ANTHROPIC_API_KEY}"
    default_model: "claude-3-5-sonnet-latest"
  groq:
    api_key: "${GROQ_API_KEY}"
    default_model: "llama-3.3-70b-versatile"
  ollama:
    endpoint: "http://localhost:11434"
    default_model: "llama3"

defaults:
  provider: "deepseek"
  model: null  # null = provider default

report_output_dir: "~/reconiq/reports"
```

---

## Phase Tracker

- [x] Design
- [ ] Implementation Plan
- [ ] Build: Core infrastructure (config, llm router, scraper)
- [ ] Build: Research modules (1–4 in parallel, then 5)
- [ ] Build: Streamlit UI
- [ ] Build: Report writer
- [ ] Test end-to-end
