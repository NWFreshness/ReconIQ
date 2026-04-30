"""Tests for Streamlit app helpers and wiring."""
from __future__ import annotations

import pytest

from app import build_analysis_request, normalize_url, validate_url


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


class TestValidateUrl:
    def test_valid_https(self):
        ok, result = validate_url("https://example.com")
        assert ok is True
        assert result == "https://example.com"

    def test_valid_http(self):
        ok, result = validate_url("http://example.com")
        assert ok is True
        assert result == "http://example.com"

    def test_bare_domain_normalized(self):
        ok, result = validate_url("example.com")
        assert ok is True
        assert result == "https://example.com"

    def test_empty_string_invalid(self):
        ok, result = validate_url("")
        assert ok is False
        assert "enter a url" in result.lower()

    def test_whitespace_only_invalid(self):
        ok, result = validate_url("   ")
        assert ok is False

    def test_missing_tld_invalid(self):
        ok, result = validate_url("https://example")
        assert ok is False
        assert "valid" in result.lower()


class TestBuildAnalysisRequest:
    def test_basic_request(self):
        req = build_analysis_request(
            target_url="https://example.com",
            enabled_modules={"company_profile": True, "seo_keywords": False},
            provider="deepseek",
            model="",
            output_dir="reports",
        )
        assert req.target_url == "https://example.com"
        assert req.enabled_modules == {"company_profile": True, "seo_keywords": False}
        assert req.provider_override is None
        assert req.model_override is None
        assert req.output_dir == "reports"

    def test_provider_override_when_changed(self):
        req = build_analysis_request(
            target_url="https://example.com",
            enabled_modules={},
            provider="openai",
            model="",
            output_dir=None,
        )
        assert req.provider_override == "openai"
        assert req.model_override is None

    def test_model_override_when_set(self):
        req = build_analysis_request(
            target_url="https://example.com",
            enabled_modules={},
            provider="deepseek",
            model="gpt-4o",
            output_dir=None,
        )
        assert req.provider_override is None  # deepseek is default
        assert req.model_override == "gpt-4o"

    def test_both_overrides(self):
        req = build_analysis_request(
            target_url="https://example.com",
            enabled_modules={},
            provider="anthropic",
            model="claude-3-sonnet",
            output_dir=None,
        )
        assert req.provider_override == "anthropic"
        assert req.model_override == "claude-3-sonnet"
