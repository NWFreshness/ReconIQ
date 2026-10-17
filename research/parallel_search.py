"""Opt-in, anonymous Parallel Search MCP provider for company research."""
from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any
from urllib.parse import urlparse

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from research.competitor_query import CompetitorQueryBuilder
from research.search_provider import SearchProvider, _empty_search_result

MCP_URL = "https://search.parallel.ai/mcp"
USER_AGENT = "ReconIQ/ParallelSearch (+https://github.com/NWFreshness/ReconIQ)"
SEARCH_TIMEOUT = 30
# Share one anonymous session across provider instances for this app process.
SESSION_ID = uuid.uuid4().hex
SOCIAL_DOMAINS = {
    "linkedin": "linkedin.com",
    "facebook": "facebook.com",
    "instagram": "instagram.com",
    "twitter": "x.com",
}


class ParallelSearchProvider(SearchProvider):
    """Use Streamable HTTP MCP without reading API keys or saved credentials."""

    @property
    def name(self) -> str:
        return "parallel"

    async def _search_async(self, objective: str, queries: list[str]) -> dict:
        # Bound the whole handshake/tool call, including streaming responses.
        async with asyncio.timeout(SEARCH_TIMEOUT):
            async with httpx.AsyncClient(
                headers={"User-Agent": USER_AGENT}, timeout=SEARCH_TIMEOUT,
            ) as http:
                async with streamable_http_client(MCP_URL, http_client=http) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        response = await session.call_tool(
                            "web_search", {"objective": objective, "search_queries": queries,
                                           "session_id": SESSION_ID},
                        )
        if response.isError:
            message = " ".join(c.text for c in response.content if c.type == "text")
            raise ValueError(message or "Parallel web_search returned an error.")
        payload = response.structuredContent
        if payload is None:
            text = "".join(c.text for c in response.content if c.type == "text")
            payload = json.loads(text)
        if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
            raise ValueError("Parallel web_search returned an invalid results payload.")
        return payload

    def _search(self, objective: str, queries: list[str]) -> tuple[list[dict], list[str]]:
        payload = asyncio.run(self._search_async(objective, queries))
        results = []
        seen = set()
        for item in payload["results"]:
            url = item.get("url", "")
            if not isinstance(url, str) or urlparse(url).scheme not in ("http", "https"):
                continue
            if not urlparse(url).hostname or url in seen:
                continue
            seen.add(url)
            results.append({
                "url": url,
                "title": item.get("title") or "",
                "snippet": "\n".join(item.get("excerpts") or []),
            })
        limitations = [w["message"] for w in payload.get("warnings") or [] if w.get("message")]
        return results, limitations

    def discover_competitors(self, company_profile: dict[str, Any], target_url: str) -> dict[str, Any]:
        builder = CompetitorQueryBuilder(company_profile, target_url)
        queries = builder.build_query_set()
        query = builder.primary_query() or ""
        if not queries:
            return _empty_search_result("No competitor search query available.", self.name, query)
        try:
            results, limitations = self._search(
                f"Find competitor company websites for {company_profile.get('company_name') or target_url}. "
                f"Use the industry and location in the queries. Exclude the target website {target_url}.",
                queries[:3],
            )
        except Exception as exc:
            reason = str(exc) or type(exc).__name__
            return _empty_search_result(f"Parallel competitor search failed: {reason}", self.name, query)
        target_host = urlparse(target_url).hostname
        results = [r for r in results if urlparse(r["url"]).hostname != target_host][:5]
        if not results:
            limitations.append("No competitors found via Parallel search.")
        return {"results": results, "accounts": [], "provider": self.name,
                "query": query, "data_limitations": limitations}

    def discover_social_accounts(self, company_name: str, target_url: str) -> dict[str, Any]:
        if not company_name:
            return _empty_search_result("No company name available for social search.", self.name)
        try:
            results, limitations = self._search(
                f"Find the official LinkedIn, Facebook, Instagram and Twitter/X profiles of "
                f"{company_name}, whose website is {target_url}. Exclude unrelated companies.",
                [f"{company_name} official social profiles", f"{company_name} LinkedIn Facebook Instagram"],
            )
        except Exception as exc:
            reason = str(exc) or type(exc).__name__
            return _empty_search_result(f"Parallel social search failed: {reason}", self.name, company_name)
        accounts = []
        for platform, domain in SOCIAL_DOMAINS.items():
            domains = (domain, "twitter.com") if platform == "twitter" else (domain,)
            for result in results:
                host = urlparse(result["url"]).hostname or ""
                if host != urlparse(target_url).hostname and any(
                    host == d or host.endswith("." + d) for d in domains
                ):
                    accounts.append({"platform": platform, "url": result["url"]})
                    break
        if not accounts:
            limitations.append("No verified social media accounts found via Parallel search.")
        return {"results": [], "accounts": accounts, "provider": self.name,
                "query": company_name, "data_limitations": limitations}
