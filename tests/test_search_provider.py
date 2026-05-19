"""Tests for SerpAPISearchProvider and FallbackSearchProvider."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from research.search_provider import (
    DisabledSearchProvider,
    FallbackSearchProvider,
    FirecrawlSearchProvider,
    SerpAPISearchProvider,
    get_search_provider,
)


# ── SerpAPISearchProvider unit tests ────────────────────────────────────────


class TestSerpAPISearchProvider:
    """SerpAPISearchProvider correctly calls SerpAPI and parses results."""

    @pytest.fixture
    def provider(self):
        return SerpAPISearchProvider(api_key="test_serpapi_key")

    @pytest.fixture
    def company_profile(self):
        return {
            "company_name": "Acme Ice Cream",
            "industry": "ice cream shop",
            "location": {"city": "Ridgefield", "state": "WA"},
            "services_products": ["ice cream", "frozen treats"],
        }

    def test_name(self, provider):
        assert provider.name == "serpapi"

    def test_search_builds_correct_url(self, provider):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = b'{"organic_results": []}'
            mock_urlopen.return_value.__enter__.return_value = mock_response

            provider._search("ice cream Ridgefield WA", limit=5)

            mock_urlopen.assert_called_once()
            call_arg = mock_urlopen.call_args[0][0]
            parsed = str(call_arg)  # Request object stringifies to full URL
            assert "serpapi.com/search" in parsed
            assert "q=ice+cream+Ridgefield+WA" in parsed
            assert "api_key=test_serpapi_key" in parsed
            assert "num=5" in parsed

    def test_search_parses_organic_results(self, provider):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = b'{"organic_results": [{"title": "Local Creamery", "link": "https://example.com", "snippet": "Fresh ice cream"}]}'
            mock_urlopen.return_value.__enter__.return_value = mock_response

            results = provider._search("ice cream Ridgefield WA", limit=5)

            assert len(results) == 1
            assert results[0]["title"] == "Local Creamery"
            assert results[0]["url"] == "https://example.com"
            assert results[0]["snippet"] == "Fresh ice cream"

    def test_search_handles_nested_search_results_format(self, provider):
        """SerpAPI wraps organic_results under search_results when engine=google."""
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = b'{"search_results": {"organic_results": [{"title": "Nested Shop", "link": "https://nested.com", "snippet": "Yum"}]}}'
            mock_urlopen.return_value.__enter__.return_value = mock_response

            results = provider._search("ice cream", limit=5)

            assert len(results) == 1
            assert results[0]["url"] == "https://nested.com"

    def test_search_raises_on_http_error(self, provider):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = Exception("Connection refused")

            with pytest.raises(Exception, match="Connection refused"):
                provider._search("ice cream", limit=5)

    def test_discover_competitors_uses_query_builder(self, provider, company_profile):
        with patch.object(provider, "_search") as mock_search:
            mock_search.return_value = [
                {"title": "Rival Shop", "url": "https://rivals.com", "snippet": "Best treats"}
            ]
            result = provider.discover_competitors(
                company_profile, "https://acme.com"
            )

            assert result["provider"] == "serpapi"
            assert result["results"][0]["url"] == "https://rivals.com"
            # Verify query builder was used (query should be non-empty)
            assert "query" in result

    def test_discover_competitors_empty_when_no_results(self, provider, company_profile):
        with patch.object(provider, "_search") as mock_search:
            mock_search.return_value = []
            result = provider.discover_competitors(
                company_profile, "https://acme.com"
            )

            assert result["results"] == []
            assert "no competitors" in result["data_limitations"][0].lower()

    def test_discover_competitors_deduplicates_by_url(self, provider):
        profile = {
            "company_name": "Test",
            "industry": "test",
            "location": {"city": "Testville", "state": "TS"},
        }
        with patch.object(provider, "_search") as mock_search:
            # Both queries return the same URL
            mock_search.side_effect = [
                [{"title": "Dup", "url": "https://dup.com", "snippet": "A"}],
                [{"title": "Dup 2", "url": "https://dup.com", "snippet": "B"}],
            ]
            result = provider.discover_competitors(profile, "https://test.com")

            assert len(result["results"]) == 1
            assert result["results"][0]["url"] == "https://dup.com"

    def test_discover_social_accounts_finds_linkedin(self, provider):
        with patch.object(provider, "_search") as mock_search:
            mock_search.return_value = [
                {"title": "Acme Ice Cream | LinkedIn", "url": "https://linkedin.com/company/acme-ice-cream", "snippet": "LinkedIn page"}
            ]
            result = provider.discover_social_accounts("Acme Ice Cream", "https://acme.com")

            assert len(result["accounts"]) == 1
            assert result["accounts"][0]["platform"] == "linkedin"
            assert result["accounts"][0]["url"] == "https://linkedin.com/company/acme-ice-cream"

    def test_discover_social_accounts_skips_target_domain(self, provider):
        """LinkedIn URL containing the target domain should be filtered out."""
        with patch.object(provider, "_search") as mock_search:
            mock_search.return_value = [
                {"title": "Acme", "url": "https://acme.com/facebook", "snippet": ""}
            ]
            result = provider.discover_social_accounts("Acme Ice Cream", "https://acme.com")

            assert len(result["accounts"]) == 0

    def test_discover_social_accounts_empty_when_no_company_name(self, provider):
        result = provider.discover_social_accounts("", "https://acme.com")
        assert result["results"] == []
        assert "no company name" in result["data_limitations"][0].lower()


# ── FallbackSearchProvider tests ─────────────────────────────────────────────


class TestFallbackSearchProvider:
    """FallbackSearchProvider delegates to primary and falls back on failure."""

    @pytest.fixture
    def mock_primary(self):
        return MagicMock(spec=SerpAPISearchProvider)

    @pytest.fixture
    def mock_fallback(self):
        return MagicMock(spec=SerpAPISearchProvider)

    def test_name_combines_providers(self, mock_primary, mock_fallback):
        mock_primary.name = "primary"
        mock_fallback.name = "fallback"
        provider = FallbackSearchProvider(mock_primary, mock_fallback)
        assert provider.name == "primary+fallback"

    def test_returns_primary_when_results_exist(self, mock_primary, mock_fallback):
        mock_primary.name = "primary"
        mock_fallback.name = "fallback"
        mock_primary.discover_competitors.return_value = {
            "results": [{"url": "https://competitor.com"}],
            "accounts": [],
            "provider": "primary",
            "query": "test",
            "data_limitations": [],
        }

        provider = FallbackSearchProvider(mock_primary, mock_fallback)
        result = provider.discover_competitors(
            {"company_name": "Test"}, "https://target.com"
        )

        assert result["results"][0]["url"] == "https://competitor.com"
        mock_fallback.discover_competitors.assert_not_called()

    def test_falls_back_when_primary_returns_empty(self, mock_primary, mock_fallback):
        mock_primary.name = "primary"
        mock_fallback.name = "fallback"
        mock_primary.discover_competitors.return_value = {
            "results": [],
            "accounts": [],
            "provider": "primary",
            "query": "test",
            "data_limitations": ["nothing found"],
        }
        mock_fallback.discover_competitors.return_value = {
            "results": [{"url": "https://from_fallback.com"}],
            "accounts": [],
            "provider": "fallback",
            "query": "test",
            "data_limitations": [],
        }

        provider = FallbackSearchProvider(mock_primary, mock_fallback)
        result = provider.discover_competitors(
            {"company_name": "Test"}, "https://target.com"
        )

        assert result["results"][0]["url"] == "https://from_fallback.com"
        mock_fallback.discover_competitors.assert_called_once()

    def test_falls_back_on_insufficient_credits(self, mock_primary, mock_fallback):
        mock_primary.name = "primary"
        mock_fallback.name = "fallback"
        mock_primary.discover_competitors.return_value = {
            "results": [],
            "accounts": [],
            "provider": "primary",
            "query": "test",
            "data_limitations": ["Insufficient credits to perform this request"],
        }
        mock_fallback.discover_competitors.return_value = {
            "results": [{"url": "https://fallback_works.com"}],
            "accounts": [],
            "provider": "fallback",
            "query": "test",
            "data_limitations": [],
        }

        provider = FallbackSearchProvider(mock_primary, mock_fallback)
        result = provider.discover_competitors(
            {"company_name": "Test"}, "https://target.com"
        )

        assert result["results"][0]["url"] == "https://fallback_works.com"
        mock_fallback.discover_competitors.assert_called_once()

    def test_falls_back_on_payment_required(self, mock_primary, mock_fallback):
        mock_primary.name = "primary"
        mock_fallback.name = "fallback"
        mock_primary.discover_competitors.return_value = {
            "results": [],
            "accounts": [],
            "provider": "primary",
            "query": "test",
            "data_limitations": ["Payment Required: Failed to search"],
        }
        mock_fallback.discover_competitors.return_value = {
            "results": [{"url": "https://recovered.com"}],
            "accounts": [],
            "provider": "fallback",
            "query": "test",
            "data_limitations": [],
        }

        provider = FallbackSearchProvider(mock_primary, mock_fallback)
        result = provider.discover_competitors(
            {"company_name": "Test"}, "https://target.com"
        )

        assert result["results"][0]["url"] == "https://recovered.com"

    def test_merges_limitations_from_both_providers(self, mock_primary, mock_fallback):
        mock_primary.name = "primary"
        mock_fallback.name = "fallback"
        mock_primary.discover_competitors.return_value = {
            "results": [],
            "accounts": [],
            "provider": "primary",
            "query": "test",
            "data_limitations": ["Primary limitation"],
        }
        mock_fallback.discover_competitors.return_value = {
            "results": [],
            "accounts": [],
            "provider": "fallback",
            "query": "test",
            "data_limitations": ["Fallback limitation"],
        }

        provider = FallbackSearchProvider(mock_primary, mock_fallback)
        result = provider.discover_competitors(
            {"company_name": "Test"}, "https://target.com"
        )

        assert "Primary limitation" in result["data_limitations"]
        assert "Fallback limitation" in result["data_limitations"]
        assert result["provider"] == "primary+fallback"

    def test_social_accounts_also_falls_back(self, mock_primary, mock_fallback):
        mock_primary.name = "primary"
        mock_fallback.name = "fallback"
        mock_primary.discover_social_accounts.return_value = {
            "results": [],
            "accounts": [],
            "provider": "primary",
            "query": "test",
            "data_limitations": ["No accounts found"],
        }
        mock_fallback.discover_social_accounts.return_value = {
            "results": [],
            "accounts": [{"platform": "instagram", "url": "https://ig.com/test"}],
            "provider": "fallback",
            "query": "test",
            "data_limitations": [],
        }

        provider = FallbackSearchProvider(mock_primary, mock_fallback)
        result = provider.discover_social_accounts("Test Company", "https://target.com")

        assert result["accounts"][0]["url"] == "https://ig.com/test"


# ── get_search_provider integration tests ───────────────────────────────────


class TestGetSearchProviderWithSerpAPI:
    """Factory correctly wires up SerpAPI and fallback chains from config."""

    def test_serpapi_alone(self):
        config = {
            "search": {
                "enabled": True,
                "provider": "serpapi",
                "serpapi": {"api_key": "test_key"},
            }
        }
        provider = get_search_provider(config)
        assert isinstance(provider, SerpAPISearchProvider)

    def test_serpapi_missing_key_returns_disabled(self):
        config = {
            "search": {
                "enabled": True,
                "provider": "serpapi",
                "serpapi": {"api_key": ""},
            }
        }
        provider = get_search_provider(config)
        assert isinstance(provider, DisabledSearchProvider)

    def test_firecrawl_with_serpapi_fallback(self):
        config = {
            "search": {
                "enabled": True,
                "provider": "firecrawl",
                "firecrawl": {
                    "api_key": "firecrawl_key",
                    "api_url": "https://api.firecrawl.dev",
                },
                "serpapi": {"api_key": "serpapi_key"},
                "fallback_chains": {"firecrawl": ["serpapi"]},
            }
        }
        provider = get_search_provider(config)
        assert isinstance(provider, FallbackSearchProvider)
        assert provider.name == "firecrawl+serpapi"

    def test_firecrawl_disabled_when_key_missing(self):
        config = {
            "search": {
                "enabled": True,
                "provider": "firecrawl",
                "firecrawl": {"api_key": ""},
            }
        }
        provider = get_search_provider(config)
        assert isinstance(provider, DisabledSearchProvider)