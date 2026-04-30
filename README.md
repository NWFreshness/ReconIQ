# ReconIQ — Marketing Intelligence

> AI-powered competitive analysis, SWOT breakdown, and client acquisition strategy from a single URL.

## What It Does

ReconIQ takes a company URL and produces a comprehensive marketing intelligence report covering:

- **Company Profile** — business model, target audience, value proposition, brand voice
- **SEO & Keywords** — top keywords, traffic estimates, content gaps
- **Competitor Analysis** — identified competitors, positioning, pricing, strengths/weaknesses
- **Social & Content** — marketing channels, content strategy, engagement signals
- **SWOT Synthesis** — cross-module strengths, weaknesses, opportunities, and threats

Reports are generated as Markdown files saved to the `reports/` directory.

## Quick Start

```bash
# Clone and enter
git clone https://github.com/NWFreshness/ReconIQ.git
cd ReconIQ

# Create virtual environment and install dependencies
python3 -m venv .venv  # or: uv venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Install Playwright browser (optional, for JS-heavy sites)
playwright install chromium

# Configure API keys
cp .env.example .env
# Edit .env with your API keys

# Run the app
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) and enter a company URL to analyze.

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and add your API keys:

| Variable | Required | Description |
|----------|----------|-------------|
| `DEEPSEEK_API_KEY` | Yes (default) | DeepSeek API key |
| `OPENAI_API_KEY` | No | OpenAI API key |
| `ANTHROPIC_API_KEY` | No | Anthropic API key |

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
```

You can override the provider and model per-run from the sidebar in the UI.

## Project Structure

```
ReconIQ/
├── app.py                    # Streamlit UI entry point
├── config.yaml               # LLM provider and model configuration
├── DESIGN.md                 # Design system tokens (Google DESIGN.md format)
├── requirements.txt           # Python dependencies
├── core/
│   ├── models.py             # Data models (AnalysisRequest, etc.)
│   ├── services.py            # Orchestration layer
│   └── settings.py            # Config loading
├── llm/
│   └── router.py              # Multi-provider LLM routing (LiteLLM)
├── research/
│   ├── coordinator.py         # Module execution coordinator
│   ├── parsing.py             # LLM response parsing and validation
│   ├── company_profile.py     # Company Profile module
│   ├── seo_keywords.py        # SEO & Keyword Analysis module
│   ├── competitors.py         # Competitor Analysis module
│   ├── social_content.py      # Social & Content module
│   └── swot.py                # SWOT Synthesis module
├── scraper/
│   └── scraper.py             # Web scraper (requests + Playwright fallback)
├── report/
│   └── writer.py              # Markdown report generation
├── tests/                     # Test suite (108 tests)
├── .streamlit/
│   ├── config.toml            # Streamlit theme configuration
│   └── style.css              # Custom CSS design system
└── docs/
    ├── enhancements.md        # Post-MVP enhancement roadmap
    ├── plan.md                # Original plan
    ├── plan-v2.md             # Revised plan
    └── design.md              # Design notes
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
pytest -q

# Run specific module
pytest tests/test_scraper.py -v
```

All 108 tests should pass.

## LLM Providers

ReconIQ uses [LiteLLM](https://github.com/BerriAI/litellm) to route prompts across providers:

| Provider | Default Model | Cost | Notes |
|----------|--------------|------|-------|
| DeepSeek | `deepseek-chat` | Low | Recommended default |
| OpenAI | `gpt-4o-mini` | Medium | Good quality |
| Anthropic | `claude-3-5-sonnet-latest` | Higher | Best analysis quality |
| Groq | `llama-3.3-70b-versatile` | Low | Fast inference |
| Ollama | `llama3` | Free | Requires local Ollama |

Switch providers from the sidebar or override the default model per-module in `config.yaml`.

## Scraping

The scraper uses `requests` + `BeautifulSoup` as the primary method. When a site requires JavaScript rendering, it falls back to Playwright with a headless Chromium browser (configurable in `config.yaml`).

## Architecture

```
URL → Scraper → Research Modules (parallel) → Coordinator → Report Writer → .md file
                  ├── company_profile
                  ├── seo_keywords
                  ├── competitor
                  ├── social_content
                  └── swot
```

Each research module:
1. Receives the scraped page content and analysis context
2. Constructs a targeted prompt for its domain
3. Sends the prompt to the configured LLM provider
4. Parses and validates the structured JSON response

The coordinator runs all enabled modules, aggregates results, and passes them to the report writer.

## Enhancement Roadmap

See [docs/enhancements.md](docs/enhancements.md) for the post-MVP roadmap including:

- **9A** — FastAPI migration for production deployment
- **9B** — Playwright JS rendering fallback (in progress)
- **9C** — Live search API for competitor discovery
- **9D** — Pydantic schemas for typed validation
- **9E** — LLM response caching
- **9F** — HTML and PDF export formats
- **9G** — UI polish and design system (in progress)
- **9H** — CLI interface
- **9I** — Batch / bulk analysis

## License

MIT
