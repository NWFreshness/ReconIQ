# Firecrawl No-Key Migration — Implementation Plan

**Target:** ReconIQ (`~/Documents/ReconIQ/`)  
**Approach:** Option A from `FIRECRAWL_NO_KEY_MIGRATION.md` — keyless cloud Firecrawl via direct REST.  
**Estimated effort:** 30–45 minutes.  
**Risk:** Low. Changes are isolated to `research/search_provider.py`; fallback to SerpAPI already exists.

---

## Guiding Principles

1. **No breakage in existing behavior.** The authenticated SDK path must continue to work exactly as before when `FIRECRAWL_API_KEY` is present.
2. **Strategy pattern stays intact.** Only `FirecrawlSearchProvider._search()` changes internally; the factory and fallback chain are untouched in behavior.
3. **Test-driven.** Add tests before/alongside code changes. Full suite must pass before merge.
4. **Reversible.** Every config/code change can be rolled back in under 60 seconds.

---

## Phase Status Tracker

| Phase | Task | Status | Notes |
|---|---|---|---|
| 0 | Safety: branch, backup env, verify baseline tests | ⬜ | |
| 1 | Config: `config.yaml`, `.env`, `.env.example` | ⬜ | |
| 2 | Code: update `_is_missing_api_key` and `_search` | ⬜ | |
| 3 | Tests: add keyless test cases | ⬜ | |
| 4 | Verify: unit tests, live API smoke test, full suite | ⬜ | |
| 5 | Commit, update docs, restart server | ⬜ | |

---

## Phase 0 — Safety & Baseline

**Goal:** Create a clean rollback point and confirm the current state is healthy.

1. `cd ~/Documents/ReconIQ`
2. `git status` — ensure you're on a clean working tree (or stash/branch accordingly).
3. Create a feature branch:
   ```bash
   git checkout -b feat/firecrawl-keyless-cloud
   ```
4. Back up `.env` (it contains live keys):
   ```bash
   cp .env .env.backup
   ```
5. Note the current `firecrawl-py` version:
   ```bash
   .venv/bin/python3 -m pip show firecrawl-py | grep Version
   ```
6. Run the relevant tests to establish a baseline:
   ```bash
   .venv/bin/python -m pytest tests/test_search_provider.py -v
   .venv/bin/python -m pytest tests/test_research_modules.py -v -k competitor
   ```

**Exit criteria:** Baseline tests pass, branch created, `.env` backed up.

---

## Phase 1 — Configuration Changes

**Goal:** Tell ReconIQ to use Firecrawl cloud with no API key.

### 1.1 `config.yaml`

Change:
```yaml
  firecrawl:
    api_url: "https://api.firecrawl.dev"
    api_key: "${FIRECRAWL_API_KEY}"
```

To:
```yaml
  firecrawl:
    api_url: "https://api.firecrawl.dev"
    api_key: ""                    # keyless free-tier cloud mode
```

Leave `serpapi` and `fallback_chains` unchanged.

### 1.2 `.env`

Comment out or remove:
```dotenv
# FIRECRAWL_API_KEY=fc-...
```

Keep `SERPAPI_API_KEY` and all LLM keys intact.

### 1.3 `.env.example`

Comment out or remove the `FIRECRAWL_API_KEY=` line so new clones don't expect it.

**Exit criteria:** `config.yaml` has `api_key: ""`; `.env` has no Firecrawl key; `.env.example` updated.

---

## Phase 2 — Code Changes

**Goal:** Allow the factory to instantiate `FirecrawlSearchProvider` with an empty key, and bypass the SDK when keyless.

### 2.1 Update `_is_missing_api_key`

File: `research/search_provider.py`

Current:
```python
def _is_missing_api_key(api_key: str) -> bool:
    return not api_key or api_key.startswith("${")
```

New:
```python
def _is_missing_api_key(api_key: str, api_url: str = "") -> bool:
    """A missing key is only an error if we're pointing at an authed host.

    Cloud Firecrawl (`api.firecrawl.dev`) accepts keyless requests on the free
    tier — verified 2026-06-17 via unauthenticated POST returning HTTP 200.
    Self-hosted servers without auth also return False here.
    Only treat as missing if the key is the unsubstituted env var.
    """
    if api_key.startswith("${"):
        return True
    return False
```

### 2.2 Update factory call sites

There are two places that call `_is_missing_api_key` for Firecrawl (lines ~499 and ~538). Update both to pass `api_url`:

```python
if _is_missing_api_key(api_key, api_url):
```

### 2.3 Rewrite `FirecrawlSearchProvider._search`

File: `research/search_provider.py`, method `_search`.

Replace the current method body with a keyless REST path + existing SDK path:

```python
def _search(self, query: str, limit: int = 5) -> list[dict[str, str]]:
    """Search via Firecrawl v2 API.

    When no API key is configured, hit the cloud endpoint directly with no
    Authorization header. Firecrawl's free tier accepts this (1,000 credits/mo).
    When a key is configured, use the official SDK (supports self-hosted too).
    """
    if not self._api_key:
        import requests

        resp = requests.post(
            f"{self._api_url.rstrip('/')}/v2/search",
            json={"query": query, "limit": limit},
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()
        results: list[dict[str, str]] = []
        for item in (payload.get("data") or {}).get("web", [])[:limit]:
            url = item.get("url") or ""
            if url:
                results.append({
                    "title": item.get("title", "") or "",
                    "url": url,
                    "snippet": item.get("description", "") or "",
                })
        return results

    # Authenticated path: SDK
    from firecrawl import FirecrawlApp

    app = FirecrawlApp(api_key=self._api_key, api_url=self._api_url)
    response = app.v2.search(query=query, limit=limit)
    results = []
    web_results = getattr(response, "web", None) or []
    for item in web_results[:limit]:
        url = getattr(item, "url", None) or ""
        if url:
            results.append({
                "title": getattr(item, "title", "") or "",
                "url": url,
                "snippet": getattr(item, "description", "")
                or getattr(item, "snippet", "")
                or "",
            })
    return results
```

**Exit criteria:** Code edits applied; no syntax errors (`python -m py_compile research/search_provider.py`).

---

## Phase 3 — Tests

**Goal:** Prove keyless mode works and doesn't break the authenticated path.

File: `tests/test_search_provider.py`

Add a new test class:

```python
class TestFirecrawlKeylessMode:
    """Cloud Firecrawl accepts unauthenticated requests on the free tier."""

    def test_keyless_provider_instantiates(self):
        provider = FirecrawlSearchProvider(api_key="", api_url="https://api.firecrawl.dev")
        assert provider._api_key == ""

    def test_keyless_search_hits_rest_directly(self):
        provider = FirecrawlSearchProvider(api_key="", api_url="https://api.firecrawl.dev")
        with patch("research.search_provider.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "success": True,
                "data": {
                    "web": [
                        {"url": "https://x.com", "title": "X", "description": "d", "position": 1}
                    ]
                },
                "creditsUsed": 2,
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            results = provider._search("ice cream", limit=5)

            mock_post.assert_called_once()
            call_url = mock_post.call_args[0][0]
            assert call_url == "https://api.firecrawl.dev/v2/search"
            assert mock_post.call_args.kwargs["json"]["query"] == "ice cream"

            assert len(results) == 1
            assert results[0]["url"] == "https://x.com"
            assert results[0]["snippet"] == "d"

    def test_keyless_search_handles_empty_data(self):
        provider = FirecrawlSearchProvider(api_key="", api_url="https://api.firecrawl.dev")
        with patch("research.search_provider.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"success": True, "data": {"web": []}}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            results = provider._search("nothing", limit=5)
            assert results == []

    def test_factory_allows_empty_key_against_cloud(self):
        config = {
            "search": {
                "enabled": True,
                "provider": "firecrawl",
                "firecrawl": {"api_key": "", "api_url": "https://api.firecrawl.dev"},
            }
        }
        provider = get_search_provider(config)
        assert isinstance(provider, FirecrawlSearchProvider)
        assert provider._api_key == ""

    def test_factory_still_rejects_unresolved_env_var(self):
        config = {
            "search": {
                "enabled": True,
                "provider": "firecrawl",
                "firecrawl": {"api_key": "${FIRECRAWL_API_KEY}", "api_url": "https://api.firecrawl.dev"},
            }
        }
        provider = get_search_provider(config)
        assert isinstance(provider, DisabledSearchProvider)
```

**Exit criteria:** New tests run green alongside existing tests.

---

## Phase 4 — Verification

### 4.1 Unit tests

```bash
cd ~/Documents/ReconIQ
.venv/bin/python -m pytest tests/test_search_provider.py -v
```

### 4.2 Live API smoke test

Run a one-off script to confirm the actual cloud endpoint still accepts unauthenticated requests after our changes:

```bash
.venv/bin/python3 -c "
from research.search_provider import FirecrawlSearchProvider
p = FirecrawlSearchProvider(api_key='', api_url='https://api.firecrawl.dev')
results = p._search('ice cream Ridgefield WA', limit=3)
print('results:', results)
assert any('eightcowcreamery.com' in r['url'] for r in results), 'expected Eight Cow Creamery'
print('OK')
"
```

### 4.3 Full test suite

```bash
.venv/bin/python -m pytest tests/ -v
```

**Expected:** Existing tests still pass. New tests add +5. If baseline was 459, target is 464.

### 4.4 Coordinator integration check

Run a lightweight end-to-end competitor analysis via the Python REPL or the Streamlit app to confirm `provider: firecrawl` appears in results and SerpAPI fallback is not triggered.

**Exit criteria:** Unit tests green, live smoke test returns Eight Cow Creamery or similar, full suite green.

---

## Phase 5 — Commit, Docs, Restart

1. Stage changes:
   ```bash
   git add config.yaml .env.example research/search_provider.py tests/test_search_provider.py
   git add FIRECRAWL_NO_KEY_MIGRATION.md FIRECRAWL_NO_KEY_IMPLEMENTATION_PLAN.md
   ```
   (Do **not** stage `.env` or `.env.backup`.)

2. Commit:
   ```bash
   git commit -m "feat(search): use keyless Firecrawl cloud free tier

   - Cloud Firecrawl /v2/search accepts unauthenticated requests on the free tier
     (1,000 credits/month). Verified 2026-06-17.
   - Bypass firecrawl-py SDK for keyless mode because SDK still requires a key.
   - Keep authenticated SDK path intact for users with FIRECRAWL_API_KEY.
   - Add tests for keyless REST path and factory behavior.
   - SerpAPI fallback remains in place for rate-limit/credit exhaustion."
   ```

3. Update the migration doc:
   - Mark Option A as **Implemented** in `FIRECRAWL_NO_KEY_MIGRATION.md`.
   - Add the commit SHA once known.

4. Restart the FastAPI server (env/config changes require it):
   ```bash
   pkill -f "uvicorn api.main" || true
   .venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
   ```

5. Verify `/health`:
   ```bash
   curl -s http://localhost:8000/health
   ```

**Exit criteria:** Commit pushed (or ready to push), server running, health check OK.

---

## Rollback Plan

If anything goes wrong at any phase:

```bash
cd ~/Documents/ReconIQ
git checkout -- research/search_provider.py config.yaml tests/test_search_provider.py
cp .env.backup .env
.venv/bin/python -m pytest tests/test_search_provider.py -v
```

Then restart uvicorn. The authenticated SDK path is restored.

---

## Open Decision

Do you want me to execute this plan now? I can run all phases in order and report real results, or hand you the branch/PR if you prefer to review first. Reply with:

- **"execute"** — I'll implement, test, and commit.
- **"review first"** — I'll just show you the exact diff before applying it.
- **"do phases X-Y only"** — e.g. "just phase 0 and 1" to limit scope.
