"""Tests for URL normalization helpers."""
from __future__ import annotations

import pytest

from scraper.scraper import normalize_url


class TestNormalizeUrl:
    def test_bare_domain_gets_https(self):
        assert normalize_url("example.com") == "https://example.com"

    def test_already_has_scheme_unchanged(self):
        assert normalize_url("https://example.com") == "https://example.com"
        assert normalize_url("http://example.com") == "http://example.com"

    def test_whitespace_stripped(self):
        assert normalize_url("  example.com  ") == "https://example.com"

    def test_empty_string_returns_empty(self):
        assert normalize_url("") == ""

    def test_path_preserved(self):
        assert normalize_url("example.com/path") == "https://example.com/path"