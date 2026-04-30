"""Tests for Playwright fallback scraping and config toggle."""
from __future__ import annotations

import pytest

from scraper.scraper import (
    normalize_url,
    scrape,
    scrape_with_playwright,
    should_use_playwright,
)


class TestShouldUsePlaywright:
    """Config toggle: when should Playwright be used?"""

    def test_returns_false_by_default(self):
        assert should_use_playwright() is False

    def test_returns_true_when_config_enabled(self, monkeypatch):
        monkeypatch.setattr("scraper.scraper._config", {"scraper": {"use_playwright_fallback": True}})
        assert should_use_playwright() is True

    def test_returns_false_when_config_missing_section(self, monkeypatch):
        monkeypatch.setattr("scraper.scraper._config", {})
        assert should_use_playwright() is False

    def test_returns_false_when_config_false(self, monkeypatch):
        monkeypatch.setattr("scraper.scraper._config", {"scraper": {"use_playwright_fallback": False}})
        assert should_use_playwright() is False


class TestScrapeWithPlaywright:
    """Playwright scrape function behavior."""

    def test_returns_empty_string_when_playwright_not_installed(self, monkeypatch):
        """If playwright is not importable, return empty string gracefully."""
        # Simulate ImportError by making the import fail
        import sys
        fake_modules = {m: v for m, v in sys.modules.items() if m != "playwright.sync_api"}
        monkeypatch.setitem(sys.modules, "playwright.sync_api", None)
        monkeypatch.setattr("scraper.scraper._playwright_available", False)

        result = scrape_with_playwright("https://example.com")
        assert result == ""

    def test_returns_empty_string_on_playwright_error(self, monkeypatch):
        """If Playwright throws any error, return empty string gracefully."""
        monkeypatch.setattr("scraper.scraper._playwright_available", False)
        result = scrape_with_playwright("https://example.com")
        assert result == ""


class TestScrapeFallbackToPlaywright:
    """Integration: scrape() should fall back to Playwright when enabled and requests fails."""

    def test_requests_succeeds_no_playwright_called(self, monkeypatch):
        """When requests returns good content, Playwright should not be called."""
        import responses

        # Use enough content to exceed the 200-char Playwright fallback threshold
        html = "<html><body><main>" + "Real content here. " * 20 + "</main></body></html>"
        playwright_called = []

        def mock_playwright(url):
            playwright_called.append(url)
            return "playwright content"

        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, "https://example.com", body=html, status=200)
            monkeypatch.setattr("scraper.scraper.should_use_playwright", lambda: True)
            monkeypatch.setattr("scraper.scraper.scrape_with_playwright", mock_playwright)

            text = scrape("https://example.com")

        assert "Real content here" in text
        assert playwright_called == []  # Playwright should NOT have been called

    def test_requests_empty_triggers_playwright_fallback(self, monkeypatch):
        """When requests returns empty/very short content and Playwright is enabled, try Playwright."""
        import responses

        # requests returns a page with very little visible content
        html = "<html><body></body></html>"
        monkeypatch.setattr("scraper.scraper.should_use_playwright", lambda: True)
        monkeypatch.setattr(
            "scraper.scraper.scrape_with_playwright",
            lambda url: "Blog Posts\nOur Services\nContact Us",
        )

        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, "https://example.com", body=html, status=200)
            text = scrape("https://example.com")

        assert "Blog Posts" in text
        assert "Our Services" in text

    def test_playwright_disabled_no_fallback(self, monkeypatch):
        """When Playwright is disabled, empty requests result stays empty."""
        import responses

        html = "<html><body></body></html>"

        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, "https://example.com", body=html, status=200)
            monkeypatch.setattr("scraper.scraper.should_use_playwright", lambda: False)
            text = scrape("https://example.com")

        assert text == ""

    def test_playwright_fallback_also_fails_returns_best_available(self, monkeypatch):
        """If both requests and Playwright fail/return empty, return whatever requests got."""
        import responses

        html = "<html><body><p>Tiny</p></body></html>"

        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, "https://example.com", body=html, status=200)
            monkeypatch.setattr("scraper.scraper.should_use_playwright", lambda: True)
            monkeypatch.setattr("scraper.scraper.scrape_with_playwright", lambda url: "")

            text = scrape("https://example.com")

        # Should fall back to whatever requests gave us
        assert "Tiny" in text