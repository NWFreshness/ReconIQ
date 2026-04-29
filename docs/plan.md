# ReconIQ Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Build a Streamlit-based marketing intelligence platform that takes a company URL, runs parallel research modules (company profile, SEO/keywords, competitor intel, social/content), synthesizes a SWOT, and outputs a Markdown report.

**Architecture:** Streamlit UI on top of a research coordinator that fires modules 1-4 in parallel via ThreadPoolExecutor, then runs SWOT synthesis (module 5) after all complete. LLM calls routed through litellm for multi-provider support (OpenAI, DeepSeek, Anthropic, Groq, Ollama). Scraping via requests + BeautifulSoup. Reports written as Markdown to ~/reconiq/reports/.

**Tech Stack:** Python 3.11+, Streamlit, litellm, requests, BeautifulSoup4, PyYAML, python-dotenv, (optional: playwright)

---

## Phase 1: Project Scaffold

### Task 1: Create requirements.txt

**Objective:** Pin all dependencies for the project.

**Files:**
- Create: `~/reconiq/requirements.txt`

**Step 1: Write requirements.txt**

```
streamlit>=1.40.0
litellm>=1.50.0
requests>=2.32.0
beautifulsoup4>=4.12.0
pyyaml>=6.0.0
python-dotenv>=1.0.0
playwright>=1.48.0
```

**Step 2: Install dependencies**

Run: `pip install --break-system-packages -r ~/reconiq/requirements.txt`

**Step 3: Install Playwright browsers (optional)**

Run: `playwright install chromium`

**Step 4: Commit**

```bash
cd ~/reconiq && git init && git add requirements.txt && git commit -m "feat: scaffold project with requirements"
```

---

### Task 2: Create config.yaml and .env.example

**Objective:** Centralize API keys and defaults.

**Files:**
- Create: `~/reconiq/config.yaml`
- Create: `~/reconiq/.env.example`

**Step 1: Write config.yaml**

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
  model: null

report_output_dir: "~/reconiq/reports"

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

**Step 2: Write .env.example**

```
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...
```

**Step 3: Commit**

```bash
cd ~/reconiq && git add config.yaml .env.example && git commit -m "feat: add config.yaml and .env.example"
```

---

### Task 3: Create package init files and directory structure

**Objective:** Establish Python package structure.

**Files:**
- Create: `~/reconiq/research/__init__.py`
- Create: `~/reconiq/scraper/__init__.py`
- Create: `~/reconiq/llm/__init__.py`
- Create: `~/reconiq/report/__init__.py`
- Create: `~/reconiq/.gitignore`

**Step 1: Write .gitignore**

```
reports/
__pycache__/
*.pyc
.env
.env.local
```

**Step 2: Write minimal __init__.py files** (empty, for package discovery)

**Step 3: Commit**

```bash
cd ~/reconiq && git add .gitignore research/__init__.py scraper/__init__.py llm/__init__.py report/__init__.py && git commit -m "feat: add package structure and gitignore"
```

---

## Phase 2: LLM Router

### Task 4: Build litellm router wrapper

**Objective:** Provide a single `llm.complete(prompt, module_name)` interface that routes to the right provider/model per module and falls back on error.

**Files:**
- Create: `~/reconiq/llm/router.py`

**Step 1: Write the LLM router**

```python
"""LLM Router — unified interface for all providers via litellm."""
from __future__ import annotations

import os
import re
from typing import Optional

import yaml
from dotenv import load_dotenv
from litellm import completion

load_dotenv()


def _resolve_env(value: str) -> str:
    """Resolve ${ENV_VAR} references in config values."""
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        env_var = value[2:-1]
        return os.getenv(env_var, "")
    return value


def _load_config() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    with open(config_path) as f:
        raw = yaml.safe_load(f)

    # Resolve env vars
    def resolve(d):
        if isinstance(d, dict):
            return {k: resolve(v) for k, v in d.items()}
        return _resolve_env(d)

    return resolve(raw)


def _get_module_config(module_name: str, config: dict) -> tuple[str, Optional[str]]:
    """Return (provider, model) for a given module. Model is None = provider default."""
    modules = config.get("modules", {})
    mod = modules.get(module_name, {})
    provider = mod.get("provider", config.get("defaults", {}).get("provider", "deepseek"))
    model = mod.get("model")
    return provider, model


def _build_kwargs(provider: str, model: Optional[str], messages: list) -> dict:
    """Build litellm completion kwargs for a provider/model pair."""
    kwargs = {
        "model": f"{provider}/{model}" if model else f"{provider}/default",
        "messages": messages,
    }
    if provider == "ollama":
        kwargs["api_base"] = config["providers"]["ollama"]["endpoint"]
        kwargs["model"] = model or config["providers"]["ollama"]["default_model"]
    return kwargs


# Cache config on module load
config = _load_config()


def complete(
    prompt: str,
    module: str,
    system: Optional[str] = None,
    max_tokens: int = 2048,
    temperature: float = 0.7,
) -> str:
    """
    Send a completion request to the appropriate LLM for a research module.

    Args:
        prompt: The user prompt.
        module: Module name matching config keys (e.g. 'company_profile', 'competitor').
        system: Optional system prompt override.
        max_tokens: Max response tokens.
        temperature: Sampling temperature.

    Returns:
        The raw text response from the LLM.
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    provider, model = _get_module_config(module, config)

    kwargs = _build_kwargs(provider, model, messages)
    kwargs["max_tokens"] = max_tokens
    kwargs["temperature"] = temperature

    # Retry logic: if first attempt fails, retry once
    last_error = None
    for attempt in range(2):
        try:
            response = completion(**kwargs)
            return response.choices[0].message.content
        except Exception as exc:
            last_error = exc
            # Swap to deepseek as fallback provider
            if provider != "deepseek":
                provider = "deepseek"
                model = None
                kwargs = _build_kwargs(provider, model, messages)
                kwargs["max_tokens"] = max_tokens
                kwargs["temperature"] = temperature
                continue
            break

    raise RuntimeError(f"LLM call failed after fallback: {last_error}")


def check_ollama() -> bool:
    """Check if Ollama is reachable at its configured endpoint."""
    try:
        import requests
        endpoint = config["providers"]["ollama"]["endpoint"]
        r = requests.get(f"{endpoint}/api/tags", timeout=5)
        return r.status_code == 200
    except Exception:
        return False
```

**Step 2: Verify syntax**

Run: `python -c "from llm.router import check_ollama; print('OK')"`

**Step 3: Commit**

```bash
cd ~/reconiq && git add llm/router.py && git commit -m "feat: add litellm router with fallback logic"
```

---

## Phase 3: Scraper

### Task 5: Build the web scraper

**Objective:** Provide a `scrape(url)` function that returns cleaned text content from a URL, with graceful fallback.

**Files:**
- Create: `~/reconiq/scraper/scraper.py`

**Step 1: Write the scraper**

```python
"""Web scraper — extracts clean text from URLs."""
from __future__ import annotations

from typing import Optional

import requests
from bs4 import BeautifulSoup
from bs4.dammit import EncodingDetector


MAX_LENGTH = 50_000  # chars


def scrape(url: str, timeout: int = 10) -> str:
    """
    Fetch and extract clean text from a URL.

    Falls back to domain-name-only inference if the domain can't be reached.

    Args:
        url: The target URL.
        timeout: Request timeout in seconds.

    Returns:
        Cleaned text content from the page.
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (compatible; ReconIQ/1.0; "
                "+https://github.com/nwfreshness)"
            ),
            "Accept": "text/html,application/xhtml+xml",
        }
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        response.raise_for_status()

        # Detect encoding
        enc = EncodingDetector.find_declared_encoding(response.content, is_html=True) or "utf-8"
        response.encoding = enc

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove noise elements
        for tag in soup.find_all(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        # Collapse blank lines
        lines = [line for line in text.splitlines() if line.strip()]
        return "\n".join(lines)[:MAX_LENGTH]

    except Exception:
        return ""


def extract_domain_name(url: str) -> str:
    """Extract a readable domain name for fallback LLM inference."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path
    return domain.replace("www.", "").split(":")[0]
```

**Step 2: Test on a known URL**

Run: `python -c "from scraper.scraper import scrape; txt = scrape('https://example.com'); print(len(txt), 'chars'); print(txt[:200]))`

Expected: ~700 chars of example.com content printed.

**Step 3: Commit**

```bash
cd ~/reconiq && git add scraper/scraper.py && git commit -m "feat: add web scraper with fallback"
```

---

## Phase 4: Research Modules

### Task 6: Write Module 1 — Company Profile

**Objective:** Extract company overview from scraped content.

**Files:**
- Create: `~/reconiq/research/company_profile.py`

**Step 1: Write the module**

```python
"""Module 1: Company Profile — extract what the company does and how they present themselves."""
from __future__ import annotations

from scraper.scraper import scrape, extract_domain_name


SYSTEM_PROMPT = (
    "You are a expert marketing analyst. Analyze the following website content "
    "and extract a structured company profile. Return a JSON-like dict with these fields:\n"
    "- company_name: inferred name\n"
    "- what_they_do: 1-2 sentence description\n"
    "- target_audience: who they serve\n"
    "- value_proposition: their main value claim\n"
    "- brand_voice: descriptive tags (e.g. professional, friendly, urgent)\n"
    "- primary_cta: main call-to-action text\n"
    "- services_products: list of 3-8 specific offerings\n"
    "- marketing_channels: inferred channels they use (website, social, email, etc.)\n"
    "If you cannot determine a field, use 'Not discernible from available data'.\n"
    "Return ONLY the dict, no preamble."
)


def run(target_url: str, llm_complete) -> dict:
    """
    Run the company profile module.

    Args:
        target_url: URL to analyze.
        llm_complete: Callable(prompt, module, system, max_tokens) -> str.

    Returns:
        Dict with company profile fields.
    """
    content = scrape(target_url)

    if not content:
        # Fallback: use domain name as hint
        domain = extract_domain_name(target_url)
        content = (
            f"Could not access {target_url}. "
            f"The company's domain is: {domain}. "
            f"Analyze based on the domain name alone."
        )

    prompt = (
        f"TARGET URL: {target_url}\n\n"
        f"WEBSITE CONTENT:\n{content[:8000]}\n\n"
        f"Extract the company profile as instructed."
    )

    raw = llm_complete(prompt, module="company_profile", system=SYSTEM_PROMPT, max_tokens=1500)

    return _parse_response(raw)


def _parse_response(raw: str) -> dict:
    """Parse the LLM text response into a structured dict."""
    import json, re

    # Try JSON first
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Fallback: parse as key-value lines
    result = {}
    for line in raw.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            result[key.strip().lower().replace(" ", "_")] = val.strip()
    return result if result else {"error": raw}
```

**Step 2: Verify import**

Run: `python -c "from research.company_profile import run; print('OK')"`

**Step 3: Commit**

```bash
cd ~/reconiq && git add research/company_profile.py && git commit -m "feat: add company profile module"
```

---

### Task 7: Write Module 2 — SEO & Keywords

**Objective:** Infer SEO landscape and keyword gaps from company profile.

**Files:**
- Create: `~/reconiq/research/seo_keywords.py`

**Step 1: Write the module**

```python
"""Module 2: SEO & Keywords — analyze search presence and content gaps."""
from __future__ import annotations


SYSTEM_PROMPT = (
    "You are an expert SEO analyst. Based on the provided company profile and target URL, "
    "infer the company's SEO landscape. Return a JSON-like dict with:\n"
    "- top_keywords: 8-12 likely organic search terms they rank for\n"
    "- content_gaps: 4-6 keyword areas they likely do NOT target well\n"
    "- seo_weaknesses: 4-5 specific weaknesses (technical, content, or backlink)\n"
    "- quick_wins: 3-4 SEO improvements they could make with moderate effort\n"
    "- estimated_traffic_tier: 'low', 'medium', or 'high' (explain briefly)\n"
    "- local_seo_signals: 'strong', 'moderate', 'weak' (Google Business Profile, local keywords)\n"
    "Return ONLY the dict, no preamble."
)


def run(company_profile: dict, target_url: str, llm_complete) -> dict:
    """
    Run the SEO & keywords module.

    Args:
        company_profile: Output from Module 1.
        target_url: Original target URL.
        llm_complete: LLM completion callable.

    Returns:
        Dict with SEO analysis fields.
    """
    prompt = (
        f"TARGET URL: {target_url}\n"
        f"COMPANY PROFILE:\n{_format_profile(company_profile)}\n\n"
        f"Infer the SEO landscape as instructed."
    )

    raw = llm_complete(prompt, module="seo_keywords", system=SYSTEM_PROMPT, max_tokens=1200)
    return _parse_response(raw)


def _format_profile(profile: dict) -> str:
    return "\n".join(f"- {k}: {v}" for k, v in profile.items())


def _parse_response(raw: str) -> dict:
    import json, re

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    result = {}
    for line in raw.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            result[key.strip().lower().replace(" ", "_")] = val.strip()
    return result if result else {"error": raw}
```

**Step 2: Verify import**

Run: `python -c "from research.seo_keywords import run; print('OK')"`

**Step 3: Commit**

```bash
cd ~/reconiq && git add research/seo_keywords.py && git commit -m "feat: add SEO keywords module"
```

---

### Task 8: Write Module 3 — Competitor Intelligence

**Objective:** Auto-discover and analyze 3-5 competitors.

**Files:**
- Create: `~/reconiq/research/competitors.py`

**Step 1: Write the module**

```python
"""Module 3: Competitor Intelligence — auto-discover and analyze competitors."""
from __future__ import annotations


SYSTEM_PROMPT = (
    "You are an expert competitive intelligence analyst. Based on the company profile and target URL, "
    "identify 4-5 direct competitors in the same market. Return a JSON array of competitor objects, "
    "each with:\n"
    "- name: company name\n"
    "- url: their website (use plausible URLs if unknown)\n"
    "- positioning: 1-2 sentence market position description\n"
    "- estimated_pricing_tier: 'budget', 'mid-market', 'premium', or 'enterprise'\n"
    "- key_messaging: their main marketing claim or tagline\n"
    "- weaknesses: 2-3 specific weaknesses or gaps\n"
    "- inferred_services: 3-5 services they likely offer\n\n"
    "Return ONLY the JSON array, no preamble or explanation."
)


def run(company_profile: dict, target_url: str, llm_complete) -> dict:
    """
    Run the competitor intelligence module.

    Args:
        company_profile: Output from Module 1.
        target_url: Original target URL.
        llm_complete: LLM completion callable.

    Returns:
        Dict with 'competitors' key containing list of competitor dicts.
    """
    prompt = (
        f"TARGET URL: {target_url}\n"
        f"COMPANY PROFILE:\n{_format_profile(company_profile)}\n\n"
        f"Identify direct competitors and analyze each as instructed."
    )

    raw = llm_complete(prompt, module="competitor", system=SYSTEM_PROMPT, max_tokens=2000)
    return _parse_response(raw)


def _format_profile(profile: dict) -> str:
    return "\n".join(f"- {k}: {v}" for k, v in profile.items())


def _parse_response(raw: str) -> dict:
    import json, re

    # Try to extract JSON array
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if match:
        try:
            competitors = json.loads(match.group())
            return {"competitors": competitors}
        except json.JSONDecodeError:
            pass

    # If we can't parse, wrap the raw text
    return {"competitors": [], "raw_error": raw}
```

**Step 2: Verify import**

Run: `python -c "from research.competitors import run; print('OK')"`

**Step 3: Commit**

```bash
cd ~/reconiq && git add research/competitors.py && git commit -m "feat: add competitor intelligence module"
```

---

### Task 9: Write Module 4 — Social & Content

**Objective:** Infer social presence and content quality.

**Files:**
- Create: `~/reconiq/research/social_content.py`

**Step 1: Write the module**

```python
"""Module 4: Social & Content — infer social presence and content quality."""
from __future__ import annotations


SYSTEM_PROMPT = (
    "You are a content and social media analyst. Based on the company profile and target URL, "
    "infer their social media presence and content strategy. Return a JSON-like dict with:\n"
    "- platforms: list of social platforms they likely use (e.g. LinkedIn, Facebook, Instagram, Twitter/X)\n"
    "- content_quality: 'low', 'moderate', or 'high' with 1-sentence explanation\n"
    "- content_frequency: 'sporadic', 'consistent', or 'heavy' publishing cadence\n"
    "- engagement_signals: 'weak', 'moderate', or 'strong' (likes, comments, shares)\n"
    "- review_sites: list of review platforms they likely appear on (Google, Yelp, Trustpilot, etc.)\n"
    "- blog_or_resources: 'yes' or 'no' — do they maintain a blog or resource center\n"
    "- content_gaps: 3-4 types of content they likely don't produce well\n"
    "- email_signals: 'prominent', 'present', or 'minimal' — how visible is their email list/CTAs\n"
    "Return ONLY the dict, no preamble."
)


def run(company_profile: dict, target_url: str, llm_complete) -> dict:
    """
    Run the social & content module.

    Args:
        company_profile: Output from Module 1.
        target_url: Original target URL.
        llm_complete: LLM completion callable.

    Returns:
        Dict with social/content analysis fields.
    """
    prompt = (
        f"TARGET URL: {target_url}\n"
        f"COMPANY PROFILE:\n{_format_profile(company_profile)}\n\n"
        f"Analyze social and content presence as instructed."
    )

    raw = llm_complete(prompt, module="social_content", system=SYSTEM_PROMPT, max_tokens=1200)
    return _parse_response(raw)


def _format_profile(profile: dict) -> str:
    return "\n".join(f"- {k}: {v}" for k, v in profile.items())


def _parse_response(raw: str) -> dict:
    import json, re

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    result = {}
    for line in raw.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            result[key.strip().lower().replace(" ", "_")] = val.strip()
    return result if result else {"error": raw}
```

**Step 2: Verify import**

Run: `python -c "from research.social_content import run; print('OK')"`

**Step 3: Commit**

```bash
cd ~/reconiq && git add research/social_content.py && git commit -m "feat: add social content module"
```

---

### Task 10: Write Module 5 — SWOT Synthesis

**Objective:** Combine all module outputs into a structured SWOT and acquisition strategy.

**Files:**
- Create: `~/reconiq/research/swot.py`

**Step 1: Write the module**

```python
"""Module 5: SWOT Synthesis — combine all findings into a strategic acquisition report."""
from __future__ import annotations


SYSTEM_PROMPT = (
    "You are a senior marketing strategist. Synthesize all provided research into a "
    "client acquisition strategy. Return a JSON-like dict with:\n\n"
    "- swot:\n"
    "  - strengths: list of 3-5 internal strengths (what they do well)\n"
    "  - weaknesses: list of 3-5 internal weaknesses (marketing gaps, inefficiencies)\n"
    "  - opportunities: list of 3-5 external opportunities (market gaps, trends they ignore)\n"
    "  - threats: list of 3-5 external threats (competitors, market shifts, risks)\n\n"
    "- acquisition_angle: 2-3 sentence summary of the best way to pitch YOUR agency to them\n"
    "- talking_points: 4-6 specific talking points for outreach (what to say, what to offer)\n"
    "- recommended_next_steps: 3-5 specific tactical actions (email sequence, content, offer)\n"
    "- competitive_advantage: 1-2 sentences on what you'd offer that their current provider lacks\n"
    "Return ONLY the dict, no preamble."
)


def run(
    company_profile: dict,
    seo_keywords: dict,
    competitor: dict,
    social_content: dict,
    target_url: str,
    llm_complete,
) -> dict:
    """
    Run the SWOT synthesis module.

    Args:
        company_profile: Output from Module 1.
        seo_keywords: Output from Module 2.
        competitor: Output from Module 3.
        social_content: Output from Module 4.
        target_url: Original target URL.
        llm_complete: LLM completion callable.

    Returns:
        Dict with SWOT and acquisition strategy fields.
    """
    prompt = (
        f"TARGET URL: {target_url}\n\n"
        f"--- COMPANY PROFILE ---\n{_format_dict(company_profile)}\n\n"
        f"--- SEO & KEYWORDS ---\n{_format_dict(seo_keywords)}\n\n"
        f"--- COMPETITOR INTELLIGENCE ---\n{_format_dict(competitor)}\n\n"
        f"--- SOCIAL & CONTENT ---\n{_format_dict(social_content)}\n\n"
        f"Synthesize into an acquisition strategy as instructed."
    )

    raw = llm_complete(prompt, module="swot", system=SYSTEM_PROMPT, max_tokens=2000)
    return _parse_response(raw)


def _format_dict(d: dict, prefix: str = "") -> str:
    """Format a dict for prompt consumption, handling nested structures."""
    lines = []
    for k, v in d.items():
        if isinstance(v, list):
            lines.append(f"- {k}:")
            for item in v:
                lines.append(f"  - {item}")
        elif isinstance(v, dict):
            lines.append(f"- {k}:")
            for sub_k, sub_v in v.items():
                lines.append(f"  - {sub_k}: {sub_v}")
        else:
            lines.append(f"- {k}: {v}")
    return "\n".join(lines)


def _parse_response(raw: str) -> dict:
    import json, re

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    result = {}
    for line in raw.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            result[key.strip().lower().replace(" ", "_")] = val.strip()
    return result if result else {"error": raw}
```

**Step 2: Verify import**

Run: `python -c "from research.swot import run; print('OK')"`

**Step 3: Commit**

```bash
cd ~/reconiq && git add research/swot.py && git commit -m "feat: add SWOT synthesis module"
```

---

## Phase 5: Coordinator & Report Writer

### Task 11: Write the Research Coordinator

**Objective:** Orchestrate parallel module execution and sequential synthesis.

**Files:**
- Create: `~/reconiq/research/coordinator.py`

**Step 1: Write the coordinator**

```python
"""Research Coordinator — parallel execution of modules 1-4, then sequential SWOT."""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Optional

from research.company_profile import run as run_company_profile
from research.seo_keywords import run as run_seo_keywords
from research.competitors import run as run_competitors
from research.social_content import run as run_social_content
from research.swot import run as run_swot


ModuleResult = dict[str, Any]
ProgressCallback = Optional[Callable[[str, float], None]]


def run_all(
    target_url: str,
    llm_complete: Callable,
    enabled_modules: dict[str, bool],
    progress_callback: ProgressCallback = None,
) -> dict[str, Any]:
    """
    Run all enabled research modules and return a combined results dict.

    Execution order:
    - Modules 1-4: run in parallel via ThreadPoolExecutor
    - Module 5 (SWOT): runs only after all 1-4 complete

    Args:
        target_url: URL to research.
        llm_complete: LLM completion callable.
        enabled_modules: Dict of module_name -> enabled (bool).
        progress_callback: Optional fn(log_message, progress_pct) for UI updates.

    Returns:
        Dict with keys: company_profile, seo_keywords, competitor, social_content, swot, metadata.
    """
    results: dict[str, Any] = {
        "metadata": {
            "target_url": target_url,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "modules_run": [],
            "modules_skipped": [],
        }
    }

    def log(msg: str, pct: float):
        if progress_callback:
            progress_callback(msg, pct)

    # Phase 1: Parallel modules (1-4)
    parallel_futures = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        if enabled_modules.get("company_profile", True):
            f = executor.submit(_safe_module, run_company_profile, target_url, llm_complete, "company_profile")
            parallel_futures[f] = "company_profile"
        if enabled_modules.get("seo_keywords", True):
            f = executor.submit(_safe_module, run_seo_keywords, _get_profile_or_empty(results), target_url, llm_complete, "seo_keywords")
            parallel_futures[f] = "seo_keywords"
        if enabled_modules.get("competitor", True):
            f = executor.submit(_safe_module, run_competitors, _get_profile_or_empty(results), target_url, llm_complete, "competitor")
            parallel_futures[f] = "competitor"
        if enabled_modules.get("social_content", True):
            f = executor.submit(_safe_module, run_social_content, _get_profile_or_empty(results), target_url, llm_complete, "social_content")
            parallel_futures[f] = "social_content"

        # Wait for all parallel tasks
        for future in as_completed(parallel_futures):
            module_name = parallel_futures[future]
            try:
                result = future.result()
                results[module_name] = result
                results["metadata"]["modules_run"].append(module_name)
                log(f"✓ {module_name} complete", 60.0)
            except Exception as exc:
                results[module_name] = {"error": str(exc)}
                results["metadata"]["modules_skipped"].append(module_name)
                log(f"✗ {module_name} failed: {exc}", 60.0)

    # Phase 2: SWOT synthesis (module 5) — only if enabled and at least one module succeeded
    if enabled_modules.get("swot", True):
        swot_input = {k: results.get(k, {}) for k in ["company_profile", "seo_keywords", "competitor", "social_content"]}
        swot_input["target_url"] = target_url

        log("Running SWOT synthesis...", 80.0)
        try:
            results["swot"] = run_swot(
                company_profile=results.get("company_profile", {}),
                seo_keywords=results.get("seo_keywords", {}),
                competitor=results.get("competitor", {}),
                social_content=results.get("social_content", {}),
                target_url=target_url,
                llm_complete=llm_complete,
            )
            results["metadata"]["modules_run"].append("swot")
            log("✓ SWOT synthesis complete", 95.0)
        except Exception as exc:
            results["swot"] = {"error": str(exc)}
            results["metadata"]["modules_skipped"].append("swot")
            log(f"✗ SWOT synthesis failed: {exc}", 95.0)
    else:
        results["metadata"]["modules_skipped"].append("swot")

    return results


def _safe_module(fn, *args, module_name: str = ""):
    """Wrapper to catch module exceptions."""
    return fn(*args)


def _get_profile_or_empty(results: dict) -> dict:
    return results.get("company_profile", {})
```

**Step 2: Verify import**

Run: `python -c "from research.coordinator import run_all; print('OK')"`

**Step 3: Commit**

```bash
cd ~/reconiq && git add research/coordinator.py && git commit -m "feat: add research coordinator with parallel execution"
```

---

### Task 12: Write the Report Writer

**Objective:** Convert the results dict into a formatted Markdown report.

**Files:**
- Create: `~/reconiq/report/writer.py`

**Step 1: Write the report writer**

```python
"""Report Writer — convert research results into a Markdown report."""
from __future__ import annotations

import os
import re
import time
from pathlib import Path


def write_report(results: dict, output_dir: str = "~/reconiq/reports") -> str:
    """
    Convert research results dict into a formatted Markdown report.

    Args:
        results: Output from coordinator.run_all().
        output_dir: Base directory for reports.

    Returns:
        Absolute path to the written report file.
    """
    company_name = _infer_company_name(results.get("company_profile", {}))
    slug = re.sub(r"[^a-z0-9]+", "-", company_name.lower()).strip("-")
    timestamp = time.strftime("%Y-%m-%d-%H%M%S")

    report_dir = Path(os.path.expanduser(output_dir)) / slug
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{timestamp}.md"

    content = _build_markdown(results, company_name)
    report_path.write_text(content, encoding="utf-8")

    return str(report_path)


def _infer_company_name(profile: dict) -> str:
    return profile.get("company_name", "Unknown Company")


def _format_dict(d: dict, indent: int = 0) -> str:
    """Render a dict/list as formatted Markdown lists."""
    lines = []
    prefix = "  " * indent
    for k, v in d.items():
        if isinstance(v, list):
            lines.append(f"{prefix}- **{k}:**")
            for item in v:
                lines.append(f"{prefix}  - {item}")
        elif isinstance(v, dict):
            lines.append(f"{prefix}- **{k}:**")
            lines.extend(_format_dict(v, indent + 1).splitlines())
        else:
            lines.append(f"{prefix}- **{k}:** {v}")
    return "\n".join(lines)


def _build_markdown(results: dict, company_name: str) -> str:
    meta = results.get("metadata", {})
    target_url = meta.get("target_url", "Unknown URL")
    timestamp = meta.get("timestamp", time.strftime("%Y-%m-%d %H:%M:%S"))

    profile = results.get("company_profile", {})
    seo = results.get("seo_keywords", {})
    competitor = results.get("competitor", {})
    social = results.get("social_content", {})
    swot = results.get("swot", {})

    lines = [
        f"# ReconIQ Report: {company_name}",
        "",
        f"**Target URL:** {target_url}",
        f"**Generated:** {timestamp}",
        f"**Modules Run:** {', '.join(meta.get('modules_run', [])) or 'None'}",
        "",
        "---",
        "",
        "## 1. Company Overview",
        "",
        _section_content(profile),
        "",
        "---",
        "",
        "## 2. SEO & Keyword Analysis",
        "",
        _section_content(seo),
        "",
        "---",
        "",
        "## 3. Competitor Landscape",
        "",
        _competitor_section(competitor),
        "",
        "---",
        "",
        "## 4. Social & Content Audit",
        "",
        _section_content(social),
        "",
        "---",
        "",
        "## 5. SWOT Analysis",
        "",
        _swot_section(swot),
        "",
        "---",
        "",
        "## 6. Client Acquisition Strategy",
        "",
        _acquisition_section(swot),
        "",
        "---",
        "",
        "## 7. Next Steps",
        "",
        _next_steps_section(swot),
        "",
        f"---\n*Report generated by ReconIQ | {timestamp}*",
    ]

    return "\n".join(lines)


def _section_content(d: dict) -> str:
    """Render a flat module dict as readable Markdown."""
    if not d or d.get("error"):
        return "*Module did not return data.*"

    lines = []
    for k, v in d.items():
        if k in ("error", "raw_error"):
            continue
        if isinstance(v, list):
            lines.append(f"**{k.replace('_', ' ').title()}:**")
            for item in v:
                lines.append(f"- {item}")
            lines.append("")
        elif isinstance(v, dict):
            lines.append(f"**{k.replace('_', ' ').title()}:**")
            for sub_k, sub_v in v.items():
                lines.append(f"- **{sub_k}:** {sub_v}")
            lines.append("")
        else:
            lines.append(f"**{k.replace('_', ' ').title()}:** {v}")
    return "\n".join(lines).strip()


def _competitor_section(competitor: dict) -> str:
    competitors = competitor.get("competitors", [])
    if not competitors:
        return "*No competitor data available.*"

    lines = []
    for i, comp in enumerate(competitors, 1):
        if isinstance(comp, dict):
            lines.append(f"### {i}. {comp.get('name', 'Unknown Competitor')}")
            for k, v in comp.items():
                if k not in ("name",):
                    lines.append(f"- **{k.replace('_', ' ').title()}:** {v}")
            lines.append("")
        else:
            lines.append(f"- {comp}")
    return "\n".join(lines).strip()


def _swot_section(swot: dict) -> str:
    sw = swot.get("swot", swot)
    if not sw:
        return "*SWOT data not available.*"

    def list_items(items):
        if isinstance(items, list):
            return "\n".join(f"- {i}" for i in items)
        return str(items)

    lines = [
        "| | Helpful | Harmful |",
        "|---|---|---|",
        f"| **Internal** | {list_items(sw.get('strengths', ['—']))} | {list_items(sw.get('weaknesses', ['—']))} |",
        f"| **External** | {list_items(sw.get('opportunities', ['—']))} | {list_items(sw.get('threats', ['—']))} |",
    ]
    return "\n".join(lines)


def _acquisition_section(swot: dict) -> str:
    sections = []
    angle = swot.get("acquisition_angle")
    if angle:
        sections.append(f"**Recommended Angle:** {angle}")
    advantage = swot.get("competitive_advantage")
    if advantage:
        sections.append(f"**Your Competitive Edge:** {advantage}")
    points = swot.get("talking_points", [])
    if points:
        sections.append("**Talking Points:**")
        for p in points:
            sections.append(f"- {p}")
    return "\n\n".join(sections) if sections else "*No acquisition data available.*"


def _next_steps_section(swot: dict) -> str:
    steps = swot.get("recommended_next_steps", [])
    if not steps:
        return "*No next steps available.*"
    return "\n".join(f"{i}. {s}" for i, s in enumerate(steps, 1))
```

**Step 2: Verify import**

Run: `python -c "from report.writer import write_report; print('OK')"`

**Step 3: Commit**

```bash
cd ~/reconiq && git add report/writer.py && git commit -m "feat: add report writer"
```

---

## Phase 6: Streamlit UI

### Task 13: Build the Streamlit app

**Objective:** Provide the full UI — URL input, module toggles, provider selector, progress output, and report display.

**Files:**
- Create: `~/reconiq/app.py`

**Step 1: Write the Streamlit app**

```python
"""ReconIQ — Marketing Intelligence Platform."""
from __future__ import annotations

import streamlit as st

from llm.router import check_ollama, complete as llm_complete
from report.writer import write_report
from research.coordinator import run_all


st.set_page_config(
    page_title="ReconIQ",
    page_icon="🎯",
    layout="wide",
)


# ── Init session state ──────────────────────────────────────────────────────────
if "report_path" not in st.session_state:
    st.session_state.report_path = None
if "report_content" not in st.session_state:
    st.session_state.report_content = None
if "running" not in st.session_state:
    st.session_state.running = False


# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.title("ReconIQ")
st.sidebar.markdown("**Provider:**")
ollama_ok = check_ollama()
st.sidebar.markdown(f"**Ollama:** {'🟢 Connected' if ollama_ok else '🔴 Not found'}")

with st.sidebar.expander("LLM Settings", expanded=True):
    provider = st.selectbox(
        "Provider",
        options=["deepseek", "openai", "anthropic", "groq", "ollama"],
        index=0,
    )
    model = st.text_input("Model override (leave blank for default)", value="")

with st.sidebar.expander("Report Output", expanded=False):
    output_dir = st.text_input("Output directory", value="~/reconiq/reports")


# ── Main ──────────────────────────────────────────────────────────────────────
st.title("🎯 ReconIQ — Marketing Intelligence")
st.markdown("Input a company URL and get a full marketing intelligence report.")

target_url = st.text_input(
    "Target URL",
    placeholder="https://example.com",
    label_visibility="collapsed",
)

col1, col2 = st.columns([1, 1])
with col1:
    run_analysis = st.button("Analyze Company", type="primary", use_container_width=True)
with col2:
    clear_btn = st.button("Clear", use_container_width=True)

# Module toggles
with st.expander("Modules", expanded=True):
    m1, m2 = st.columns(2)
    with m1:
        toggle_profile = st.checkbox("Company Profile", value=True)
        toggle_seo = st.checkbox("SEO & Keywords", value=True)
    with m2:
        toggle_competitor = st.checkbox("Competitor Intel", value=True)
        toggle_social = st.checkbox("Social & Content", value=True)
    toggle_swot = st.checkbox("SWOT Synthesis", value=True)

enabled_modules = {
    "company_profile": toggle_profile,
    "seo_keywords": toggle_seo,
    "competitor": toggle_competitor,
    "social_content": toggle_social,
    "swot": toggle_swot,
}

# Status area
status_container = st.empty()
progress_bar = st.progress(0)
log_container = st.empty()

# Report display
report_container = st.empty()

if clear_btn:
    st.session_state.report_path = None
    st.session_state.report_content = None
    st.session_state.running = False
    st.rerun()

if run_analysis and target_url:
    if not target_url.startswith(("http://", "https://")):
        st.error("Please enter a valid URL starting with http:// or https://")
    else:
        st.session_state.running = True
        log_lines = []

        def progress_callback(msg: str, pct: float):
            log_lines.append(msg)
            progress_bar.progress(pct / 100.0)
            log_container.info("\n".join(log_lines[-10:]))

        try:
            # Run the research
            status_container.info("Running research modules...")
            results = run_all(
                target_url=target_url,
                llm_complete=llm_complete,
                enabled_modules=enabled_modules,
                progress_callback=progress_callback,
            )

            # Write the report
            report_path = write_report(results, output_dir=output_dir)
            report_content = open(report_path).read()
            st.session_state.report_path = report_path
            st.session_state.report_content = report_content

            progress_bar.progress(100.0)
            status_container.success(f"Report complete! Saved to:\n`{report_path}`")

        except Exception as exc:
            status_container.error(f"Error: {exc}")
            st.session_state.running = False

# Display report if available
if st.session_state.report_content:
    report_container.markdown("---")
    report_container.markdown("### Report Preview")
    st.markdown(st.session_state.report_content)
    st.markdown("---")

    col_dl, col_open = st.columns(2)
    with col_dl:
        st.download_button(
            "Download .md",
            data=st.session_state.report_content,
            file_name=f"reconiq-report.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col_open:
        import subprocess, platform
        system = platform.system()
        if system == "Darwin":
            subprocess.run(["open", st.session_state.report_path])
        elif system == "Linux":
            subprocess.run(["xdg-open", st.session_state.report_path])
        st.button("Open in Folder", use_container_width=True)
```

**Step 2: Verify syntax**

Run: `python -m py_compile ~/reconiq/app.py && echo "OK"`

**Step 3: Commit**

```bash
cd ~/reconiq && git add app.py && git commit -m "feat: add Streamlit UI"
```

---

## Phase 7: End-to-End Test

### Task 14: Run end-to-end test with a real URL

**Objective:** Verify the full pipeline works from URL input to Markdown report output.

**Run command:**

```bash
cd ~/reconiq && \
  export OPENAI_API_KEY="..." && \
  export DEEPSEEK_API_KEY="..." && \
  export ANTHROPIC_API_KEY="..." && \
  streamlit run app.py --server.headless true --server.port 8501
```

**Verification checklist:**

- [ ] Streamlit app loads at http://localhost:8501
- [ ] Ollama indicator shows correctly
- [ ] Entering a URL and clicking "Analyze Company" fires all enabled modules
- [ ] Progress bar updates per module
- [ ] Report generates and displays in the page
- [ ] Report .md file is written to ~/reconiq/reports/<company-name>/
- [ ] Download button works
- [ ] Module toggles work (disable one, re-run, see it skipped in report metadata)

---

## Phase Tracker

- [x] Design
- [x] Implementation Plan
- [ ] Task 1: requirements.txt
- [ ] Task 2: config.yaml + .env.example
- [ ] Task 3: Package init files + .gitignore
- [ ] Task 4: LLM router (litellm + fallback)
- [ ] Task 5: Web scraper
- [ ] Task 6: Module 1 — Company Profile
- [ ] Task 7: Module 2 — SEO & Keywords
- [ ] Task 8: Module 3 — Competitor Intelligence
- [ ] Task 9: Module 4 — Social & Content
- [ ] Task 10: Module 5 — SWOT Synthesis
- [ ] Task 11: Research Coordinator (parallel + sequential)
- [ ] Task 12: Report Writer
- [ ] Task 13: Streamlit UI
- [ ] Task 14: End-to-end test
