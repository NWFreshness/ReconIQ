"""Exercise the optional provider through real MCP serialization and HTTP requests."""
from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from core.settings import load_config
from research import competitors, search
from research import parallel_search
from research.search_provider import (
    DisabledSearchProvider, FallbackSearchProvider, FirecrawlSearchProvider,
    SerpAPISearchProvider, get_search_provider,
)

CONFIG = {"search": {"enabled": True, "provider": "parallel"}}
PROFILE = {"company_name": "Acme", "services_products": ["plumbing"],
           "location_city": "Portland", "location_state": "OR"}
TARGET = "https://acme.example"


@pytest.fixture
def mcp_server(monkeypatch):
    """Replace only the network, preserving the SDK, loader, and response parser."""
    state = {"requests": [], "result": {"results": []}, "clients": [],
             "structured": True, "error": False, "http_error": False, "delay": 0}
    real_client = httpx.AsyncClient

    async def handler(request):
        state["requests"].append(request)
        assert str(request.url) == parallel_search.MCP_URL
        assert request.headers["user-agent"] == parallel_search.USER_AGENT
        assert "authorization" not in request.headers
        if request.method != "POST":
            return httpx.Response(405)
        data = json.loads(request.content)
        method = data["method"]
        if method == "notifications/initialized":
            return httpx.Response(202)
        if method == "initialize":
            result = {"protocolVersion": data["params"]["protocolVersion"],
                      "capabilities": {"tools": {}},
                      "serverInfo": {"name": "fixture", "version": "1"}}
        elif method == "tools/list":
            result = {"tools": [{"name": "web_search", "inputSchema": {"type": "object"}}]}
        elif method == "tools/call":
            assert data["params"]["name"] == "web_search"
            if state["http_error"]:
                return httpx.Response(503)
            await asyncio.sleep(state["delay"])
            result = {"content": [{"type": "text", "text": json.dumps(state["result"])}],
                      "isError": state["error"]}
            if state["structured"]:
                result["structuredContent"] = state["result"]
        else:
            raise AssertionError(method)
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": data["id"], "result": result})

    def client(**kwargs):
        instance = real_client(**kwargs, transport=httpx.MockTransport(handler))
        state["clients"].append(instance)
        return instance

    monkeypatch.setattr(parallel_search.httpx, "AsyncClient", client)
    # An anonymous provider must ignore credentials for all other providers too.
    for name in ("PARALLEL_API_KEY", "FIRECRAWL_API_KEY", "SERPAPI_API_KEY"):
        monkeypatch.setenv(name, "must-not-be-sent")
    return state


def tool_arguments(state):
    return [json.loads(r.content)["params"]["arguments"] for r in state["requests"]
            if r.method == "POST" and json.loads(r.content)["method"] == "tools/call"]


@pytest.mark.parametrize("structured", [True, False])
def test_competitor_entry_point_normalizes_and_deduplicates(mcp_server, structured):
    mcp_server["structured"] = structured
    mcp_server["result"] = {
        "results": [
            {"url": TARGET, "title": "Acme", "excerpts": []},
            {"url": "https://rival.example", "title": "Rival | Plumbing", "excerpts": ["Local", "24/7"]},
            {"url": "https://rival.example", "title": "Duplicate", "excerpts": []},
            {"url": "file:///tmp/private", "excerpts": []},
        ],
        "warnings": [{"message": "Some sources were unavailable."}],
    }
    result = search.discover_competitors(PROFILE, TARGET, CONFIG)
    assert result["provider"] == "parallel"
    assert result["results"] == [{"url": "https://rival.example", "title": "Rival | Plumbing", "snippet": "Local\n24/7"}]
    assert result["data_limitations"] == ["Some sources were unavailable."]
    args, = tool_arguments(mcp_server)
    assert "Acme" in args["objective"] and TARGET in args["objective"]
    assert 1 <= len(args["search_queries"]) <= 3
    assert "Portland" in args["search_queries"][0]
    assert all("companies like " not in q for q in args["search_queries"])
    assert all("-site:acme.example" in q for q in args["search_queries"])
    assert all(c.is_closed for c in mcp_server["clients"])


def test_competitors_are_capped(mcp_server):
    mcp_server["result"] = {"results": [
        {"url": f"https://rival{i}.example", "excerpts": []} for i in range(10)
    ]}
    result = search.discover_competitors(PROFILE, TARGET, CONFIG)
    assert len(result["results"]) == 5


@pytest.mark.parametrize("target,own_url", [
    ("https://acme.example", "https://www.acme.example/about"),
    ("https://www.acme.example", "https://acme.example/about"),
    ("acme.example", "https://WWW.Acme.Example:443/about"),
])
def test_target_www_alias_is_excluded(mcp_server, target, own_url):
    mcp_server["result"] = {"results": [
        {"url": own_url, "excerpts": []},
        {"url": "https://rival.example", "excerpts": []},
    ]}
    result = search.discover_competitors(PROFILE, target, CONFIG)
    assert [r["url"] for r in result["results"]] == ["https://rival.example"]


def test_social_entry_point_checks_real_platform_hosts(mcp_server):
    urls = ["https://evil.example/linkedin.com/acme", "https://linkedin.com.evil.example/acme",
            "https://www.linkedin.com/company/acme", "https://facebook.com/acme",
            "https://instagram.com/acme", "https://twitter.com/acme"]
    mcp_server["result"] = {"results": [{"url": u, "excerpts": []} for u in urls]}
    result = search.discover_social_accounts("Acme", TARGET, CONFIG)
    assert result["provider"] == "parallel"
    assert result["accounts"] == [
        {"platform": p, "url": u} for p, u in zip(
            ["linkedin", "facebook", "instagram", "twitter"], urls[2:])
    ]
    assert result["data_limitations"] == []
    assert len(tool_arguments(mcp_server)) == 1


def test_no_company_name_does_not_search(mcp_server):
    assert search.discover_social_accounts("", TARGET, CONFIG)["accounts"] == []
    assert mcp_server["requests"] == []


def test_provider_instances_share_anonymous_session(mcp_server):
    search.discover_competitors(PROFILE, TARGET, CONFIG)
    search.discover_social_accounts("Acme", TARGET, CONFIG)
    assert {a["session_id"] for a in tool_arguments(mcp_server)} == {parallel_search.SESSION_ID}


@pytest.mark.parametrize("method", ["competitors", "social"])
@pytest.mark.parametrize("failure", ["empty", "malformed", "tool_error", "http_error", "timeout"])
def test_failures_are_reported_without_breaking_analysis(mcp_server, monkeypatch, method, failure):
    if failure == "malformed":
        mcp_server["result"] = {"unexpected": []}
    elif failure == "tool_error":
        mcp_server["error"] = True
        mcp_server["result"] = {"message": "rate limit exceeded"}
    elif failure == "http_error":
        mcp_server["http_error"] = True
    elif failure == "timeout":
        monkeypatch.setattr(parallel_search, "SEARCH_TIMEOUT", 0.05)
        mcp_server["delay"] = 10
    result = (search.discover_competitors(PROFILE, TARGET, CONFIG) if method == "competitors"
              else search.discover_social_accounts("Acme", TARGET, CONFIG))
    assert result["provider"] == "parallel"
    assert result["results"] == [] and result["accounts"] == []
    assert result["data_limitations"]
    if failure == "tool_error":
        assert "rate limit exceeded" in result["data_limitations"][0]
    assert all(c.is_closed for c in mcp_server["clients"])


def test_cancellation_propagates_and_closes_client(mcp_server):
    mcp_server["delay"] = 10

    async def cancel_search():
        provider = get_search_provider(CONFIG)
        task = asyncio.create_task(provider._search_async("Find plumbers", ["Portland plumbers"]))
        while not tool_arguments(mcp_server):
            await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(cancel_search())
    assert all(c.is_closed for c in mcp_server["clients"])


def test_downstream_competitor_module_consumes_search_excerpts(mcp_server, monkeypatch):
    mcp_server["result"] = {"results": [{"url": "https://rival.example", "title": "Rival", "excerpts": ["Emergency repairs"]}]}
    monkeypatch.setattr("core.settings.load_config", lambda: CONFIG)
    monkeypatch.setattr(competitors, "_scrape_competitor_homepage", lambda url: {"url": url, "text": "Plumbing service"})
    prompts = []

    def complete(prompt, **kwargs):
        prompts.append(prompt)
        return json.dumps({"competitors": [{"name": "Rival", "url": "https://rival.example"}],
                           "data_confidence": "high", "data_limitations": []})

    result = competitors.run(PROFILE, TARGET, complete)
    assert "Emergency repairs" in prompts[0]
    assert result["competitors"][0]["url"] == "https://rival.example"
    assert result["inferred_competitors"] == []


def test_downstream_social_module_preserves_discovered_accounts(mcp_server, monkeypatch):
    from research import social_content

    mcp_server["result"] = {"results": [
        {"url": "https://www.linkedin.com/company/acme", "excerpts": ["Acme profile"]},
    ]}
    monkeypatch.setattr("core.settings.load_config", lambda: CONFIG)

    def complete(prompt, **kwargs):
        return json.dumps({
            "platforms": ["invented"], "verified_social_accounts": [],
            "content_quality": "moderate", "content_frequency": "sporadic",
            "engagement_signals": "weak", "review_sites": [], "blog_or_resources": "no",
            "content_gaps": [], "email_signals": "minimal", "data_confidence": "low",
            "data_limitations": [],
        })

    result = social_content.run(PROFILE, TARGET, complete)
    assert result["platforms"] == ["linkedin"]
    assert result["verified_social_accounts"] == [
        {"platform": "linkedin", "url": "https://www.linkedin.com/company/acme"},
    ]


def test_factory_preserves_existing_selections_and_disabled_search(mcp_server):
    assert isinstance(get_search_provider({"search": {"enabled": False, "provider": "parallel"}}), DisabledSearchProvider)
    assert isinstance(get_search_provider({"search": {"enabled": True}}), FirecrawlSearchProvider)
    assert isinstance(get_search_provider({"search": {"enabled": True, "provider": "serpapi", "serpapi": {"api_key": "explicit"}}}), SerpAPISearchProvider)
    assert isinstance(get_search_provider({"search": {"enabled": True, "provider": "unknown"}}), DisabledSearchProvider)
    assert load_config()["search"]["provider"] == "firecrawl"
    assert mcp_server["requests"] == []


def test_opt_in_firecrawl_fallback_uses_parallel(mcp_server, monkeypatch):
    monkeypatch.setattr(FirecrawlSearchProvider, "discover_competitors", lambda *args: {
        "results": [], "data_limitations": ["Primary unavailable."]})
    mcp_server["result"] = {"results": [{"url": "https://rival.example", "excerpts": ["Plumbing"]}]}
    config = {"search": {"enabled": True, "provider": "firecrawl", "firecrawl": {"api_key": ""},
                         "fallback_chains": {"firecrawl": ["parallel"]}}}
    assert isinstance(get_search_provider(config), FallbackSearchProvider)
    result = search.discover_competitors(PROFILE, TARGET, config)
    assert result["provider"] == "firecrawl+parallel"
    assert result["results"][0]["snippet"] == "Plumbing"
    assert result["data_limitations"] == ["Primary unavailable."]
