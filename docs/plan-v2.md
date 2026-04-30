# ReconIQ Implementation Plan v2

> **For Hermes:** This is a collaborative implementation plan. Work one phase at a time with the user. Do not skip checkpoints. When executing, use `subagent-driven-development` for coding phases if the user wants autonomous implementation.

**Goal:** Build ReconIQ, a local Streamlit marketing intelligence app that accepts a company URL, researches the company, competitors, SEO/content signals, synthesizes SWOT and acquisition strategy, and writes a Markdown report.

**Architecture:** A Streamlit UI calls a coordinator. The coordinator runs Company Profile first because downstream modules depend on it, then runs SEO/Keywords, Competitors, and Social/Content in parallel, then runs SWOT synthesis, then writes a Markdown report. LLM calls route through a small LiteLLM wrapper with explicit provider/model resolution and testable fallback behavior.

**Tech Stack:** Python 3.11+, Streamlit, LiteLLM, requests, BeautifulSoup4, PyYAML, python-dotenv, pytest, pytest-mock, responses or requests-mock. Playwright is deferred unless we decide JS-heavy scraping is required.

**Project Root:** `/Users/tylermayfield/Documents/projects/ReconIQ`

---

## Phase Status and Source of Truth

This section is the durable source of truth for implementation progress. Future agents/models must read this section before starting work, update it when a phase changes state, and keep it synchronized with GitHub PR status and local verification results.

Update rules for future agents/models:
1. Before starting a phase, confirm the previous phase status here and verify the referenced PR/branch state when applicable.
2. Mark a phase `[x]` only after the code is implemented, committed, pushed, and either merged or opened as a PR with passing local verification.
3. If a phase is implemented but the PR is still open, keep the checkbox checked only when local verification passed and record `Status: PR open`.
4. Record the PR URL, branch, latest commit, and local verification summary for completed/in-progress phases.
5. If a phase needs follow-up after review, change the status back to an explicit non-complete state and add a short note.
6. Do not rely only on chat history or transient todo state; this file is the project-level progress tracker.

- [x] Phase 0 — Baseline and Environment
  - Status: Complete
  - Evidence: uv environment created, dependencies installed, dependency import check passed, compile check passed.

- [x] Phase 1 — Configuration, Core Boundaries, and LLM Router
  - Status: Merged
  - PR: https://github.com/NWFreshness/ReconIQ/pull/1
  - Branch: `feat/phase-1-core-llm-router`
  - Merge commit: `683eb8d6c1f4ad47940748dd558585b7d579554e`
  - Local verification: `13 passed`; compile check passed; `git diff --check` passed.

- [x] Phase 2 — Shared JSON Parsing Utilities
  - Status: Merged
  - PR: https://github.com/NWFreshness/ReconIQ/pull/2
  - Branch: `feat/phase-2-json-parser`
  - Merge commit: `54f6f45 Merge pull request #2 from NWFreshness/feat/phase-2-json-parser`
  - Local verification: `28 passed`; compile check passed; `git diff --check` passed.

- [x] Phase 3 — Scraper
  - Status: Merged
  - PR: https://github.com/NWFreshness/ReconIQ/pull/4
  - Branch: `feat/phase-3-scraper`
  - Merge commit: `5da68ee Merge pull request #4 from NWFreshness/feat/phase-3-scraper`
  - Local verification: `37 passed`; scraper example.com smoke check passed; compile check passed; `git diff --check` passed.

- [ ] Phase 4 — Research Modules
  - Status: In progress — local implementation and verification complete; not yet committed/pushed.
  - Branch: `feat/phase-4-research-modules`
  - Local verification: `61 passed`; focused research module checks `29 passed`; compile check passed; `git diff --check` passed.

- [ ] Phase 5 — Coordinator
  - Status: Not started

- [ ] Phase 6 — Report Writer
  - Status: In progress — local implementation and verification complete; not yet committed/pushed.
  - Branch: `feat/phase-6-report-writer`
  - Local verification: `70 passed`; focused report writer checks `9 passed`; compile check passed; `git diff --check` passed.

- [ ] Phase 7 — Streamlit UI
  - Status: Not started

- [ ] Phase 8 — End-to-End Test Path
  - Status: Not started

- [ ] Phase 9 — Optional Enhancements After MVP
  - Status: Not started

---

## Guiding Principles

1. Work in small phases we can review together.
2. Use the existing project root, not `~/reconiq`.
3. Prefer relative paths in commands after `cd /Users/tylermayfield/Documents/projects/ReconIQ`.
4. Use a virtual environment; do not use `--break-system-packages`.
5. Add tests before or alongside implementation for non-trivial logic.
6. Keep provider/model routing explicit and testable.
7. Require strict JSON from LLM prompts; do not ask for “JSON-like” output.
8. Avoid fake precision. If data is inferred rather than measured, label it as inferred.
9. Preserve useful parallelism, but respect dependencies.
10. End each phase with a checkpoint before moving on.
11. Keep business logic independent from Streamlit so the app can later become a production web app.
12. Treat Streamlit as an MVP presentation layer, not the core application architecture.
13. Put orchestration, schemas, report generation, provider routing, and persistence behind framework-neutral service functions.
14. Avoid global mutable UI state in core modules.
15. Design interfaces that can later be called from FastAPI, a background worker, or a frontend app without rewriting the research engine.

---

## Target File Structure

```text
/Users/tylermayfield/Documents/projects/ReconIQ/
├── app.py
├── config.yaml
├── requirements.txt
├── .env.example
├── .gitignore
├── docs/
│   ├── design.md
│   ├── plan.md
│   └── plan-v2.md
├── core/
│   ├── __init__.py
│   ├── models.py          # Framework-neutral dataclasses/Pydantic-style schemas
│   ├── services.py        # Main application service API used by Streamlit now, FastAPI later
│   └── settings.py        # Config loading independent from UI framework
├── llm/
│   ├── __init__.py
│   └── router.py
├── report/
│   ├── __init__.py
│   └── writer.py
├── research/
│   ├── __init__.py
│   ├── company_profile.py
│   ├── coordinator.py
│   ├── competitors.py
│   ├── parsing.py
│   ├── seo_keywords.py
│   ├── social_content.py
│   └── swot.py
├── scraper/
│   ├── __init__.py
│   └── scraper.py
└── tests/
    ├── test_coordinator.py
    ├── test_llm_router.py
    ├── test_parsing.py
    ├── test_report_writer.py
    ├── test_research_modules.py
    └── test_scraper.py
```

---

# Phase 0: Baseline and Environment

**Goal:** Establish a safe, repeatable local development setup.

## Tasks

### Task 0.1: Confirm repository root and current state

**Files:** none

**Commands:**

```bash
cd /Users/tylermayfield/Documents/projects/ReconIQ
pwd
git status --short
python3 --version
```

**Expected:**
- Working directory is `/Users/tylermayfield/Documents/projects/ReconIQ`.
- Python is 3.11+ or we decide whether the current version is acceptable.
- Git status is understood before edits.

### Task 0.2: Create or refresh virtual environment instructions

**Files:**
- Modify: `requirements.txt`
- Create/modify: `.env.example`
- Create/modify: `.gitignore`

**Implementation notes:**
- Keep runtime dependencies in `requirements.txt`.
- Add test dependencies either to `requirements.txt` for simplicity or to a later `requirements-dev.txt` if we want separation.
- Do not include Playwright unless Phase 9 is selected.

**Recommended dependencies:**

```text
streamlit>=1.40.0
litellm>=1.50.0
requests>=2.32.0
beautifulsoup4>=4.12.0
pyyaml>=6.0.0
python-dotenv>=1.0.0
pytest>=8.0.0
pytest-mock>=3.14.0
responses>=0.25.0
```

**Commands with uv:**

```bash
cd /Users/tylermayfield/Documents/projects/ReconIQ
uv venv --python 3.14
uv pip install -r requirements.txt
```

**Alternative commands without uv:**

```bash
cd /Users/tylermayfield/Documents/projects/ReconIQ
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

**Verification:**

```bash
uv run python -m pytest --version
uv run python -c "import streamlit, litellm, requests, bs4, yaml, dotenv; print('deps ok')"
```

## Checkpoint 0

Review together:
- Python version
- Dependency list
- Whether Playwright should stay deferred
- Whether to use one `requirements.txt` or split dev dependencies

---

# Phase 1: Configuration, Core Boundaries, and LLM Router

**Goal:** Make provider/model selection deterministic, testable, and usable from Streamlit now and a production web app later.

**Production-readiness goal:** Establish a framework-neutral core layer so Streamlit is only a UI shell. Future FastAPI, background jobs, authentication, teams, billing, and database persistence should call the same core service functions rather than duplicating logic.

## Tasks

### Task 1.0: Create framework-neutral core package

**Files:**
- Create: `core/__init__.py`
- Create: `core/settings.py`
- Create: `core/models.py`
- Create: `core/services.py`

**Design:**

`core/settings.py` owns config loading and environment resolution.

`core/models.py` defines shared request/result shapes. Start lightweight with dataclasses or TypedDicts; consider Pydantic in Phase 9C if we want stronger validation.

Suggested initial shapes:

```python
@dataclass
class AnalysisRequest:
    target_url: str
    enabled_modules: dict[str, bool]
    provider_override: str | None = None
    model_override: str | None = None
    output_dir: str | None = None

@dataclass
class AnalysisResult:
    results: dict[str, Any]
    report_path: str | None
```

`core/services.py` exposes the main app workflow:

```python
def run_analysis(request: AnalysisRequest, progress_callback=None) -> AnalysisResult:
    ...
```

**Important:**
- `core/services.py` may call coordinator and report writer.
- `app.py` should call `core.services.run_analysis()` instead of directly wiring coordinator/report writer logic.
- No Streamlit imports are allowed inside `core/`, `research/`, `llm/`, `scraper/`, or `report/`.

**Verification:**

```bash
source .venv/bin/activate
python -m py_compile core/*.py
python -c "from core.services import run_analysis; print('core service import ok')"
```

### Task 1.1: Normalize `config.yaml`

**Files:**
- Modify: `config.yaml`

**Design:**

```yaml
providers:
  openai:
    default_model: "gpt-4o-mini"
  deepseek:
    default_model: "deepseek-chat"
  anthropic:
    default_model: "claude-3-5-sonnet-latest"
  groq:
    default_model: "llama-3.3-70b-versatile"
  ollama:
    endpoint: "http://localhost:11434"
    default_model: "llama3"

defaults:
  provider: "deepseek"
  model: null

report_output_dir: "reports"

modules:
  company_profile:
    provider: "deepseek"
    model: null
  seo_keywords:
    provider: "deepseek"
    model: null
  competitor:
    provider: "anthropic"
    model: null
  social_content:
    provider: "openai"
    model: null
  swot:
    provider: "anthropic"
    model: null
```

**Notes:**
- Keep API keys in environment variables, not config.
- LiteLLM can read provider env vars such as `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.
- Use project-relative `reports` by default, not `~/reconiq/reports`.

### Task 1.2: Add tests for provider/model resolution

**Files:**
- Create: `tests/test_llm_router.py`

**Test cases:**
- Module-specific provider is used when present.
- Default provider is used for unknown module.
- `model: null` resolves to provider default model.
- UI override provider/model wins over config when supplied.
- Ollama model builds with `ollama/<model>` and `api_base`.
- DeepSeek fallback is selected on first provider failure.

### Task 1.3: Implement LLM router fixes

**Files:**
- Modify: `llm/router.py`

**Required public functions:**

```python
def load_config(path: str | None = None) -> dict: ...
def resolve_model(provider: str, model: str | None, config: dict) -> str: ...
def build_completion_kwargs(provider: str, model: str | None, messages: list[dict], config: dict) -> dict: ...
def complete(prompt: str, module: str, system: str | None = None, max_tokens: int = 2048, temperature: float = 0.7, provider_override: str | None = None, model_override: str | None = None) -> str: ...
def check_ollama() -> bool: ...
```

**Model resolution rules:**
- If `model_override` is supplied, use it.
- Else if module config has a model, use it.
- Else use provider default model.
- Never produce `provider/default`.

**Verification:**

```bash
source .venv/bin/activate
python -m pytest tests/test_llm_router.py -v
python -m py_compile llm/router.py
```

## Checkpoint 1

Review together:
- Provider/model override behavior
- Whether fallback should always be DeepSeek or configurable
- Whether config should include API-key variable names for UI diagnostics

---

# Phase 2: Shared JSON Parsing Utilities

**Goal:** Make LLM response parsing robust and reusable across modules.

## Tasks

### Task 2.1: Write parser tests

**Files:**
- Create: `tests/test_parsing.py`

**Test cases:**
- Extracts a JSON object from plain JSON.
- Extracts a JSON object from fenced markdown.
- Extracts a JSON array from plain JSON.
- Raises a clear error for invalid JSON.
- Does not silently turn bad nested JSON into misleading flat key/value output.

### Task 2.2: Implement `research/parsing.py`

**Files:**
- Create: `research/parsing.py`

**Required functions:**

```python
def extract_json_object(raw: str) -> dict: ...
def extract_json_array(raw: str) -> list: ...
def require_keys(data: dict, keys: list[str], context: str) -> dict: ...
```

**Prompt standard for every module:**

```text
Return valid JSON only.
Use double quotes for all keys and string values.
Do not wrap the JSON in markdown.
Do not include comments, explanations, or trailing commas.
```

**Verification:**

```bash
source .venv/bin/activate
python -m pytest tests/test_parsing.py -v
```

## Checkpoint 2

Review together:
- Whether invalid LLM JSON should fail the module or store raw output with an error
- Whether to add Pydantic now or keep lightweight validation

---

# Phase 3: Scraper

**Goal:** Provide reliable basic HTML scraping with graceful failure and test coverage.

## Tasks

### Task 3.1: Add scraper tests

**Files:**
- Create: `tests/test_scraper.py`

**Test cases:**
- `scrape()` extracts visible text from a simple HTML response.
- `scrape()` removes script/style/nav/header/footer/aside text.
- `scrape()` returns `""` on network failure.
- `extract_domain_name()` handles `https://www.example.com/path`.
- `normalize_url()` adds `https://` if we decide to support bare domains.

### Task 3.2: Implement scraper improvements

**Files:**
- Modify: `scraper/scraper.py`

**Required behavior:**
- Use `requests.get()` with a clear user agent.
- Set timeout.
- Return clean text capped at `MAX_LENGTH`.
- Return empty string on failure.
- Keep Playwright out of v1 unless selected in Phase 9.

**Verification:**

```bash
source .venv/bin/activate
python -m pytest tests/test_scraper.py -v
python -c "from scraper.scraper import scrape; txt = scrape('https://example.com'); print(len(txt)); print(txt[:200])"
```

## Checkpoint 3

Review together:
- Whether bare domains should be accepted
- Whether scraper failure should be visible in report metadata
- Whether JS rendering is needed for the target use cases

---

# Phase 4: Research Modules

**Goal:** Implement each module with strict JSON prompts, reusable parsing, and tests using mocked LLM responses.

## Tasks

### Task 4.1: Add research module tests

**Files:**
- Create: `tests/test_research_modules.py`

**Test cases:**
- Company Profile uses scraped content when available.
- Company Profile falls back to domain-only context when scraping fails.
- Each module calls `llm_complete` with the correct module name.
- Each module parses strict JSON successfully.
- Bad JSON returns a controlled error or raises a controlled exception, based on Checkpoint 2 decision.

### Task 4.2: Update Company Profile module

**Files:**
- Modify: `research/company_profile.py`

**Required output keys:**
- `company_name`
- `what_they_do`
- `target_audience`
- `value_proposition`
- `brand_voice`
- `primary_cta`
- `services_products`
- `marketing_channels`
- `data_confidence`
- `data_limitations`

### Task 4.3: Update SEO & Keywords module

**Files:**
- Modify: `research/seo_keywords.py`

**Important:** Label outputs as inferred unless backed by measurable data.

**Required output keys:**
- `top_keywords`
- `content_gaps`
- `seo_weaknesses`
- `quick_wins`
- `estimated_traffic_tier`
- `local_seo_signals`
- `data_confidence`
- `data_limitations`

### Task 4.4: Update Competitor module

**Files:**
- Modify: `research/competitors.py`

**Required output shape:**

```json
{
  "competitors": [
    {
      "name": "...",
      "url": "...",
      "positioning": "...",
      "estimated_pricing_tier": "...",
      "key_messaging": "...",
      "weaknesses": ["..."],
      "inferred_services": ["..."]
    }
  ],
  "data_confidence": "low|medium|high",
  "data_limitations": ["..."]
}
```

### Task 4.5: Update Social & Content module

**Files:**
- Modify: `research/social_content.py`

**Required output keys:**
- `platforms`
- `content_quality`
- `content_frequency`
- `engagement_signals`
- `review_sites`
- `blog_or_resources`
- `content_gaps`
- `email_signals`
- `data_confidence`
- `data_limitations`

### Task 4.6: Update SWOT module

**Files:**
- Modify: `research/swot.py`

**Required output keys:**
- `swot`
  - `strengths`
  - `weaknesses`
  - `opportunities`
  - `threats`
- `acquisition_angle`
- `talking_points`
- `recommended_next_steps`
- `competitive_advantage`
- `data_confidence`
- `data_limitations`

**Verification:**

```bash
source .venv/bin/activate
python -m pytest tests/test_research_modules.py -v
python -m py_compile research/*.py
```

## Checkpoint 4

Review together:
- Module output schemas
- Prompt tone and whether it fits intended users
- Whether “client acquisition strategy” should be aggressive, consultative, or neutral

---

# Phase 5: Coordinator

**Goal:** Fix orchestration so dependencies are correct, failures are isolated, and progress reporting is meaningful.

## Correct Execution Order

```text
1. Company Profile
2. SEO + Competitors + Social/Content in parallel
3. SWOT synthesis
4. Report writer
```

## Tasks

### Task 5.1: Add coordinator tests

**Files:**
- Create: `tests/test_coordinator.py`

**Test cases:**
- Company Profile runs before downstream modules.
- SEO, Competitors, and Social receive the populated company profile.
- Downstream modules can run in parallel after profile is ready.
- SWOT receives all available module outputs.
- If one downstream module fails, the coordinator records the error and continues.
- Disabled modules are marked skipped.
- Progress callback receives sensible messages and percentages.

### Task 5.2: Implement corrected coordinator

**Files:**
- Modify: `research/coordinator.py`

**Required behavior:**
- Do not pass extra positional arguments to module `run()` functions.
- Use a safe wrapper only if it does not alter call signatures incorrectly.
- Store metadata:
  - `target_url`
  - `timestamp`
  - `modules_run`
  - `modules_skipped`
  - `modules_failed`
  - `data_limitations`
  - provider/model metadata if available
- Continue if a non-critical module fails.
- Only run SWOT if it is enabled and at least Company Profile succeeded.

**Verification:**

```bash
source .venv/bin/activate
python -m pytest tests/test_coordinator.py -v
python -m py_compile research/coordinator.py
```

## Checkpoint 5

Review together:
- Whether SWOT should run if Company Profile fails
- Whether failed modules should appear in report sections or only metadata
- Whether progress percentages feel right for Streamlit

---

# Phase 6: Report Writer

**Goal:** Generate readable Markdown reports that accurately label inferred data and partial failures.

## Tasks

### Task 6.1: Add report writer tests

**Files:**
- Create: `tests/test_report_writer.py`

**Test cases:**
- Writes report to configured output directory.
- Slugifies company name safely.
- Includes target URL, timestamp, modules run, skipped, and failed.
- Renders competitor list cleanly.
- Renders SWOT without broken Markdown tables.
- Handles missing module data gracefully.

### Task 6.2: Fix report writer

**Files:**
- Modify: `report/writer.py`

**Required improvements:**
- Use project-relative `reports/` by default.
- Avoid raw multiline lists inside Markdown table cells; use `<br>` or non-table sections.
- Include data confidence and limitations where available.
- Include failed/skipped modules in the report metadata.
- Do not crash if `company_name` is missing or not a string.

**Verification:**

```bash
source .venv/bin/activate
python -m pytest tests/test_report_writer.py -v
python -m py_compile report/writer.py
```

## Checkpoint 6

Review together:
- Report format and section order
- Whether SWOT should be a table or four separate sections
- Whether reports should go under `reports/<company>/<timestamp>.md` or `reports/<timestamp>-<company>.md`

---

# Phase 7: Streamlit UI

**Goal:** Build a UI that exposes only controls that actually work.

**Production-readiness goal:** Keep Streamlit thin. It should collect user input, render progress, and display/download the report. It should not contain business logic that would need to be rewritten for FastAPI, React, Next.js, background workers, or hosted deployment.

## Tasks

### Task 7.1: Decide provider override behavior

**Options:**

A. Simple v1:
- Remove provider/model controls from UI.
- Use `config.yaml` only.

B. Configurable v1:
- Keep provider/model controls.
- Pass `provider_override` and `model_override` through coordinator to `llm.complete`.

**Recommended:** Option B, because the design explicitly promises provider selection.

### Task 7.2: Update core service/coordinator/router call path for overrides

**Files:**
- Modify: `core/models.py`
- Modify: `core/services.py`
- Modify: `research/coordinator.py`
- Modify: `llm/router.py` if needed
- Modify: research module call signatures only if necessary

**Recommended design:**
- Streamlit builds an `AnalysisRequest`.
- Streamlit calls `core.services.run_analysis(request, progress_callback=...)`.
- `core.services.run_analysis()` creates a preconfigured completion callable and passes it into the coordinator.
- The coordinator remains UI-agnostic.
- The report writer remains UI-agnostic.

Example service-level callable:

```python
def configured_llm_complete(prompt, module, system=None, max_tokens=2048, temperature=0.7):
    return llm_complete(
        prompt=prompt,
        module=module,
        system=system,
        max_tokens=max_tokens,
        temperature=temperature,
        provider_override=request.provider_override,
        model_override=request.model_override,
    )
```

Then pass `configured_llm_complete` to `run_all()`.

### Task 7.3: Fix Streamlit app behavior

**Files:**
- Modify: `app.py`

**Required fixes:**
- Keep Streamlit as a thin UI shell around `core.services.run_analysis()`.
- Do not import research modules directly in `app.py`.
- Validate URL before running.
- Normalize or reject bare domains based on Checkpoint 3.
- Use provider/model selection if controls remain.
- Fix `Open in Folder` so it only runs after clicking the button.
- Open the containing folder, not the report file.
- Read report file with explicit encoding.
- Set `running` back to false after success and failure.
- Display failed/skipped modules if present.

### Task 7.4: Manual UI verification

**Commands:**

```bash
source .venv/bin/activate
streamlit run app.py --server.headless true --server.port 8501
```

**Manual checklist:**
- App loads at `http://localhost:8501`.
- URL validation works.
- Module toggles work.
- Provider/model override works or UI does not display unsupported controls.
- Progress updates in order.
- Report preview displays.
- Download button works.
- Open in Folder opens the report directory only when clicked.

## Checkpoint 7

Review together:
- UI flow
- Provider/model controls
- Error display
- Whether to add a “dry run with mock LLM” mode for demos

---

# Phase 8: End-to-End Test Path

**Goal:** Verify the full app pipeline without burning API credits unnecessarily.

## Tasks

### Task 8.1: Add a mock end-to-end script or test

**Files:**
- Create: `tests/test_end_to_end_mocked.py` or `scripts/mock_run.py`

**Recommended:** Add a pytest test that uses a fake `llm_complete` and a mocked scraper.

**Test should verify:**
- `run_all()` returns all expected sections.
- `write_report()` writes a real Markdown file.
- The report contains company name, SWOT, competitors, and acquisition strategy.

### Task 8.2: Run mocked E2E

**Commands:**

```bash
source .venv/bin/activate
python -m pytest tests/test_end_to_end_mocked.py -v
```

### Task 8.3: Run one real E2E manually

**Prerequisites:**
- At least one provider API key is set in `.env` or environment.

**Commands:**

```bash
source .venv/bin/activate
python -c "from dotenv import load_dotenv; load_dotenv(); print('env loaded')"
streamlit run app.py --server.headless true --server.port 8501
```

**Manual checklist:**
- Use a low-risk test URL, such as `https://example.com` or a known local business site.
- Confirm a report file is created under `reports/`.
- Confirm the report clearly states inferred data and limitations.

## Checkpoint 8

Review together:
- Whether outputs are useful enough for v1
- Whether LLM cost/speed is acceptable
- Whether app needs caching or result reuse

---

# Phase 9: Optional Enhancements After MVP

Do not start these until Phases 0-8 are complete and reviewed.

## Option 9A: Production Web App Migration Path

**Goal:** Convert the MVP architecture into a production-grade web app without rewriting the research engine.

**Recommended future stack:**
- Backend API: FastAPI
- Frontend: Next.js or React
- Database: Postgres
- Job queue: Celery/RQ/Arq/Dramatiq or managed queue
- Cache: Redis
- Object/file storage: S3-compatible storage for reports
- Auth: Clerk/Auth0/Supabase Auth or custom OAuth
- Deployment: Docker + Render/Fly.io/Railway/AWS/GCP
- Observability: structured logs, error tracking, metrics

**Future file structure:**

```text
api/
├── main.py
├── routes/
│   ├── analyses.py
│   └── reports.py
├── dependencies.py
└── schemas.py
workers/
└── analysis_worker.py
web/
└── <frontend app>
core/
research/
llm/
scraper/
report/
```

**Migration strategy:**
1. Keep `core.services.run_analysis()` as the canonical use case.
2. Add `api/main.py` with a FastAPI app.
3. Add `POST /analyses` to validate input and enqueue a background job.
4. Add `GET /analyses/{id}` for status.
5. Add `GET /reports/{id}` for report retrieval.
6. Move long-running LLM work out of request/response into a worker.
7. Store analysis status, metadata, and report paths in Postgres.
8. Store report files in S3-compatible object storage.
9. Add user accounts and per-user report ownership.
10. Add rate limits, cost controls, provider quotas, and audit logs.

**Design requirements to preserve now:**
- No Streamlit imports outside `app.py`.
- No direct filesystem assumptions inside research modules.
- No UI state inside coordinator.
- No provider secrets passed through frontend-visible data.
- Report generation should accept structured results and return a path or storage handle.
- Coordinator progress events should be serializable so they can become websocket/SSE events later.

## Option 9B: Playwright JS Rendering

**Files:**
- Modify: `requirements.txt`
- Modify: `scraper/scraper.py`
- Modify: `tests/test_scraper.py`

**Goal:** Add fallback scraping for JS-heavy sites.

**Commands:**

```bash
source .venv/bin/activate
python -m pip install playwright
python -m playwright install chromium
```

## Option 9C: Better Competitor Discovery

**Goal:** Use live search APIs or search-engine scraping alternatives instead of pure LLM inference.

**Possible tools:**
- SerpAPI
- Tavily
- Brave Search API
- Bing Web Search API

## Option 9D: Pydantic Schemas

**Goal:** Replace lightweight JSON validation with typed schemas.

**Files:**
- Create: `research/schemas.py`
- Modify: all modules
- Modify: tests

## Option 9E: Cached Runs

**Goal:** Avoid repeating expensive LLM calls for the same URL.

**Files:**
- Create: `cache/` or `.reconiq-cache/`
- Create: `research/cache.py`
- Modify: coordinator

## Option 9F: Export Formats

**Goal:** Add HTML/PDF exports after Markdown is stable.

---

# Suggested Work Sessions

## Session 1: Foundation

Scope:
- Phase 0
- Phase 1
- Phase 2

Outcome:
- Clean environment
- Reliable LLM router
- Shared JSON parser
- Tests passing for config/router/parser

## Session 2: Data Collection and Modules

Scope:
- Phase 3
- Phase 4

Outcome:
- Scraper works
- Research modules produce strict JSON-shaped outputs
- Mocked module tests pass

## Session 3: Orchestration and Reports

Scope:
- Phase 5
- Phase 6

Outcome:
- Correct execution order
- Partial failures handled
- Markdown report is readable and tested

## Session 4: UI and E2E

Scope:
- Phase 7
- Phase 8

Outcome:
- Streamlit UI works
- Mocked E2E passes
- One real report generated and reviewed

## Session 5: Polish / Optional Enhancements

Scope:
- Any Phase 9 option selected together

Outcome:
- Improved scraping, search, caching, schema validation, or exports

---

# Definition of Done for MVP

The MVP is complete when:

- `python -m pytest -v` passes.
- `python -m py_compile app.py core/*.py llm/router.py scraper/scraper.py research/*.py report/writer.py` passes.
- Streamlit app launches locally.
- A user can enter a URL and generate a Markdown report.
- The report includes:
  - Company overview
  - SEO/keyword analysis
  - Competitor landscape
  - Social/content audit
  - SWOT analysis
  - Client acquisition strategy
  - Data confidence and limitations
- Provider/model override either works or is removed from the UI.
- Reports are saved under the project’s `reports/` directory.
- Failures are shown clearly without crashing the whole run.

---

# Immediate Next Step

Start with Phase 0. After confirming environment and dependency choices, proceed to Phase 1 and fix the LLM router before touching the research modules.
