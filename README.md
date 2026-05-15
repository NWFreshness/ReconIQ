# ReconIQ — Marketing Intelligence

> AI-powered competitive analysis, SWOT breakdown, and client acquisition strategy from a single URL.

## What It Does

ReconIQ takes a company URL and produces a comprehensive marketing intelligence report covering:

- **Company Profile** — business model, target audience, value proposition, brand voice
- **SEO & Keywords** — top keywords, traffic estimates, content gaps
- **Competitor Analysis** — identified competitors with side-by-side comparison matrix
- **Social & Content** — marketing channels, content strategy, engagement signals
- **SWOT Synthesis** — cross-module strengths, weaknesses, opportunities, and threats
- **Outreach Pack** — cold emails, LinkedIn DMs, call openers, proposal outlines, follow-up sequences
- **Prospect Score** — deterministic 7-dimension scoring (0–100, A+ to F) for agency opportunity quality
- **Evidence & Citations** — every major claim traceable to scraped pages or search results

Reports are generated as Markdown files saved to the `reports/` directory, with a full web dashboard and API for managing analyses.

## Quick Start

```bash
# Clone and enter
git clone https://github.com/NWFreshness/ReconIQ.git
cd ReconIQ

# Create virtual environment and install dependencies
uv venv .venv
source .venv/bin/activate
.venv/bin/python -m ensurepip
.venv/bin/pip3 install -r requirements.txt

# Install Playwright browser (optional, for JS-heavy sites)
playwright install chromium

# Configure API keys
cp .env.example .env
# Edit .env with your API keys (at least DEEPSEEK_API_KEY and FIRECRAWL_API_KEY)
```

### Mode 1: FastAPI + Next.js (recommended)

```bash
# Terminal 1 — FastAPI backend (port 8000)
.venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Next.js frontend (port 3000)
cd web && npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### Mode 2: Streamlit standalone (port 8501)

```bash
.venv/bin/streamlit run app.py --server.port 8501 --server.headless true
```

Open [http://localhost:8501](http://localhost:8501).

### Mode 3: CLI

```bash
.venv/bin/python cli.py https://example.com
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and add your API keys:

| Variable | Required | Description |
|----------|----------|-------------|
| `DEEPSEEK_API_KEY` | Yes (default) | DeepSeek API key |
| `FIRECRAWL_API_KEY` | Yes (for competitor discovery) | Firecrawl search API key |
| `OPENAI_API_KEY` | No | OpenAI API key |
| `ANTHROPIC_API_KEY` | No | Anthropic API key |
| `GROQ_API_KEY` | No | Groq API key |

**Without `FIRECRAWL_API_KEY`, the competitor module falls back to homepage-only scraping and finds zero competitors.**

### config.yaml

LLM provider and model settings live in `config.yaml`:

```yaml
defaults:
  provider: "deepseek"
  model: null  # null = use provider default

providers:
  deepseek:
    default_model: "deepseek-chat"
  openai:
    default_model: "gpt-4o-mini"
  anthropic:
    default_model: "claude-3-5-sonnet-latest"
  groq:
    default_model: "llama-3.3-70b-versatile"
  ollama:
    endpoint: "http://localhost:11434"
    default_model: "llama3"

scraper:
  use_playwright_fallback: true  # Enable headless browser for JS-heavy sites
  max_pages: 5                    # Max subpages to crawl
  max_depth: 2                    # Max crawl depth from homepage
```

You can override the provider and model per-run from the sidebar in the UI or via CLI flags.

## Project Structure

```
ReconIQ/
├── app.py                    # Streamlit UI entry point
├── cli.py                    # CLI interface
├── config.yaml               # LLM provider, model, and scraper configuration
├── DESIGN.md                 # Design system tokens (Google DESIGN.md format)
├── requirements.txt          # Python dependencies
├── api/                      # FastAPI backend (port 8000)
│   ├── main.py               # App entry, CORS, routes
│   ├── worker.py             # Background job runner (ThreadPoolExecutor)
│   ├── schemas.py            # Pydantic request/response models
│   ├── auth.py               # X-API-Key authentication
│   ├── db.py                 # SQLite job database
│   └── routes/               # analyses.py, reports.py
├── web/                      # Next.js frontend (port 3000)
│   └── src/
│       ├── app/              # Dashboard + analysis detail pages
│       ├── components/       # AnalysisCard, CompetitorMatrix, EvidenceList, OutreachBlock, etc.
│       └── lib/api.ts        # Typed API client
├── core/                     # Framework-neutral shared code
│   ├── models.py             # AnalysisRequest, AnalysisResult dataclasses
│   ├── services.py           # Orchestration layer
│   ├── settings.py           # Config loading
│   └── batch.py              # Batch/multi-URL analysis
├── research/                 # Research modules (7 total)
│   ├── coordinator.py        # Dependency-aware module orchestration
│   ├── schemas.py            # Pydantic output schemas + field coercion
│   ├── company_profile.py    # Company Profile module
│   ├── seo_keywords.py       # SEO & Keyword Analysis module
│   ├── competitors.py        # Competitor Analysis module
│   ├── competitor_matrix.py  # Competitor comparison matrix formatting
│   ├── social_content.py     # Social & Content module
│   ├── swot.py               # SWOT Synthesis module
│   ├── outreach.py           # Outreach Pack generator
│   ├── prospect_score.py     # Deterministic prospect scoring (7 dimensions)
│   ├── evidence.py           # Evidence & citations helpers
│   ├── parsing.py            # LLM response parsing and validation
│   └── search.py             # Firecrawl search integration
├── scraper/                  # Web scraping layer
│   ├── scraper.py            # Primary scraper (requests + BeautifulSoup)
│   ├── crawler.py            # Multi-page crawler with depth control
│   ├── extractors.py         # Structured data extraction
│   └── models.py             # ScrapeResult, PageData dataclasses
├── report/
│   └── writer.py             # Markdown/HTML report generation
├── llm/
│   ├── router.py             # Multi-provider LLM routing via LiteLLM
│   └── cache.py              # LLM response caching
├── tests/                    # Test suite (349 tests)
├── .streamlit/
│   ├── config.toml           # Streamlit theme configuration
│   └── style.css             # Custom CSS design system
└── docs/                     # Architecture, plans, design notes
```

## Design System

The UI follows a formal design system defined in `DESIGN.md` using Google's open-source token spec format. Key principles:

- **Vercel-inspired light theme** — near-black ink on warm white canvas, indigo accent
- **Shadow-as-border depth** — cards use `box-shadow` instead of traditional borders
- **Inter + JetBrains Mono** — geometric sans-serif for UI, monospace for technical labels
- **Single accent color** — indigo (#5e6ad2) for all interactive elements, no gradients
- **Locked sidebar** — LLM provider and model selection always visible

Lint the design tokens:

```bash
npx @google/design.md lint DESIGN.md
```

## Testing

```bash
# Run all tests
.venv/bin/python -m pytest tests/ -v

# Run specific module
.venv/bin/python -m pytest tests/test_scraper.py -v

# Quick summary
.venv/bin/python -m pytest tests/ -q
```

349 tests pass in ~51 seconds.

## LLM Providers

ReconIQ uses [LiteLLM](https://github.com/BerriAI/litellm) to route prompts across providers with automatic fallback to DeepSeek:

| Provider | Default Model | Cost | Notes |
|----------|--------------|------|-------|
| DeepSeek | `deepseek-chat` | Low | Recommended default |
| OpenAI | `gpt-4o-mini` | Medium | Good quality |
| Anthropic | `claude-3-5-sonnet-latest` | Higher | Best analysis quality |
| Groq | `llama-3.3-70b-versatile` | Low | Fast inference |
| Ollama | `llama3` | Free | Requires local Ollama |

Switch providers from the sidebar, CLI flags, or override the default model per-module in `config.yaml`.

## Scraping

The scraper uses `requests` + `BeautifulSoup` as the primary method. When a site requires JavaScript rendering, it falls back to Playwright with a headless Chromium browser (configurable in `config.yaml`). The multi-page crawler supports configurable depth and page limits (Phase 9J).

## Architecture

```
URL → Structured Crawl → Research Modules → Coordinator → Report Writer → .md file
                     └→ Company Profile (sequential, must succeed)
                        ├→ SEO Keywords ─┐
                        ├→ Competitors    ├→ (parallel via ThreadPoolExecutor)
                        └→ Social Content ┘
                           ├→ SWOT Synthesis (sequential, depends on above)
                           ├→ Outreach Pack (sequential, depends on SWOT)
                           └→ Prospect Score (deterministic, no LLM call)
```

Each research module:
1. Receives the scraped page content and analysis context
2. Constructs a targeted prompt for its domain
3. Sends the prompt to the configured LLM provider
4. Parses and validates the structured JSON response
5. Attaches evidence items for claim traceability

The coordinator runs all enabled modules in dependency order, aggregates results, and passes them to the report writer.

## API

The FastAPI backend exposes REST endpoints for programmatic access:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/analyses` | POST | Start a new analysis (returns 202) |
| `/analyses` | GET | List analyses (supports filters: status, provider, date range, min_score, error_only) |
| `/analyses/{id}` | GET | Get analysis status and metadata |
| `/analyses/{id}/results` | GET | Get full analysis results |
| `/analyses/{id}` | DELETE | Delete an analysis |
| `/reports/{id}/download/{fmt}` | GET | Download report in md/html/pdf format |

Authentication via `X-API-Key` header (default dev key: `reconiq-dev-key-change-in-production`).

## Enhancement Roadmap

See [docs/enhancements.md](docs/enhancements.md) and [FEATURE_PHASES.md](FEATURE_PHASES.md) for the full roadmap.

### Completed Phases (1–14)

| Phase | Feature | Status |
|-------|---------|--------|
| 1–8 | Core pipeline (LLM router, scraper, modules, coordinator, report, UI, tests) | Done |
| 9A–9J | FastAPI, Playwright, Pydantic schemas, caching, exports, CLI, batch, structured extraction, multi-page crawler | Done |
| 10 | Evidence & Citations Viewer | Done |
| 11 | Competitor Comparison Matrix | Done |
| 12 | Outreach Pack Generator | Done |
| 13 | Prospect Scoring (7-dimension deterministic scoring) | Done |
| 14 | Dashboard Filters (status, provider, date, score, error-only) | Done |

### Upcoming Phases (15–21)

| Phase | Feature | Description |
|-------|---------|-------------|
| 15 | Saved Prospect Lists | Group analyses into named lists (e.g. "Vancouver HVAC companies") |
| 16 | Local-First Auth | Password-based local user ownership without cloud auth |
| 17 | Monitoring & Scheduled Re-runs | Re-analyze on a schedule, show what changed |
| 18 | Cost Controls | Budget caps, per-run estimates, local-only hard block |
| 19 | Better Local Mode | Ollama-only preset, no cloud dependencies |
| 20 | CRM & Export Integrations | CSV, Airtable, HubSpot exports |
| 21 | Visual Report Builder | SWOT quadrants, radar charts, client-ready visuals |

## License

MIT
