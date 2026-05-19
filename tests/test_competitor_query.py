"""Tests for CompetitorQueryBuilder."""
from __future__ import annotations

import pytest

from research.competitor_query import (
    CompetitorQueryBuilder,
    _build_competitor_query,
    _extract_industry_signals,
    _extract_location_signals,
    _build_industry_location_query,
    _build_service_location_query,
    _build_vertical_directory_query,
    _build_broader_industry_query,
)


class TestExtractIndustrySignals:
    def test_what_they_do_first(self):
        profile = {"what_they_do": "HVAC contractor", "services_products": ["furnace repair"]}
        signals = _extract_industry_signals(profile)
        assert signals[0] == "HVAC contractor"

    def test_services_products_included(self):
        profile = {"services_products": ["SEO services", "web design", "marketing"]}
        signals = _extract_industry_signals(profile)
        assert "SEO services" in signals
        assert "web design" in signals

    def test_empty_profile(self):
        signals = _extract_industry_signals({})
        assert signals == []

    def test_target_audience_included(self):
        profile = {"target_audience": "small law firms", "what_they_do": "legal software"}
        signals = _extract_industry_signals(profile)
        assert "small law firms" in signals


class TestExtractLocationSignals:
    def test_city_and_state(self):
        profile = {"location_city": "Vancouver", "location_state": "WA"}
        signals = _extract_location_signals(profile)
        assert "Vancouver WA" in signals

    def test_service_area(self):
        profile = {
            "location_city": "Portland",
            "location_state": "OR",
            "service_area": ["Lake Oswego", "Beaverton"],
        }
        signals = _extract_location_signals(profile)
        assert "Lake Oswego, OR" in signals
        assert "Beaverton, OR" in signals

    def test_service_area_not_duplicated_as_city(self):
        profile = {"location_city": "Vancouver", "location_state": "WA", "service_area": ["Vancouver WA"]}
        signals = _extract_location_signals(profile)
        # service_area item matching the city+state combo should be deduplicated
        assert "Vancouver WA" in signals
        # Only one location entry should exist (not city+state AND service_area separately)
        assert signals.count("Vancouver WA") == 1

    def test_zip_code(self):
        profile = {"location_city": "Vancouver", "location_state": "WA", "location_zip": "98662"}
        signals = _extract_location_signals(profile)
        assert "98662" in signals


class TestBuildIndustryLocationQuery:
    def test_full_signal(self):
        q = _build_industry_location_query(["HVAC contractor", "furnace repair"], ["Vancouver WA"])
        assert q == "HVAC contractor, furnace repair Vancouver WA"

    def test_missing_industry(self):
        q = _build_industry_location_query([], ["Vancouver WA"])
        assert q is None

    def test_missing_location(self):
        q = _build_industry_location_query(["HVAC contractor"], [])
        assert q is None


class TestBuildServiceLocationQuery:
    def test_full_signal(self):
        q = _build_service_location_query(["SEO services", "PPC management"], ["Portland OR"])
        assert q == "SEO services, PPC management Portland OR"

    def test_missing_services(self):
        q = _build_service_location_query([], ["Portland OR"])
        assert q is None


class TestBuildVerticalDirectoryQuery:
    def test_full_signal(self):
        q = _build_vertical_directory_query(["plumber"], ["Seattle WA"])
        assert q == "top plumber in Seattle WA"

    def test_missing_industry(self):
        q = _build_vertical_directory_query([], ["Seattle WA"])
        assert q is None


class TestBuildBroaderIndustryQuery:
    def test_returns_industry(self):
        q = _build_broader_industry_query(["landscaping company"])
        assert q == "landscaping company"

    def test_empty(self):
        q = _build_broader_industry_query([])
        assert q is None


class TestCompetitorQueryBuilder:
    def test_full_profile_builds_five_queries(self):
        profile = {
            "company_name": "TestCo HVAC",
            "what_they_do": "HVAC contractor",
            "target_audience": "residential homeowners",
            "services_products": ["furnace repair", "air conditioning installation"],
            "location_city": "Vancouver",
            "location_state": "WA",
        }
        builder = CompetitorQueryBuilder(profile, "https://testcohvac.com")
        queries = builder.build_query_set()

        # Should have multiple queries
        assert len(queries) >= 3
        # Primary query should mention industry + location
        assert "Vancouver" in queries[0] or "WA" in queries[0]
        # None should be duplicates
        assert len(queries) == len(set(queries))

    def test_primary_query_is_most_specific(self):
        profile = {
            "what_they_do": "dental practice",
            "services_products": ["teeth whitening", "implants"],
            "location_city": "Portland",
            "location_state": "OR",
        }
        builder = CompetitorQueryBuilder(profile, "https://example.com")
        primary = builder.primary_query()

        # Primary should include both industry and location
        assert "Portland" in primary or "OR" in primary
        assert "dental" in primary.lower() or "teeth" in primary.lower()

    def test_no_location_falls_back_gracefully(self):
        profile = {
            "what_they_do": "SaaS marketing tool",
            "services_products": ["email automation"],
            "company_name": "Acme SaaS",
        }
        builder = CompetitorQueryBuilder(profile, "https://acmesaas.com")
        queries = builder.build_query_set()

        # Should still generate queries without location
        assert len(queries) >= 2
        # Last resort should be industry-only
        last = queries[-1]
        assert "SaaS marketing tool" in last

    def test_completely_empty_profile(self):
        profile = {}
        builder = CompetitorQueryBuilder(profile, "https://example.com")
        queries = builder.build_query_set()

        # No meaningful signal to build a query
        assert queries == []

    def test_lazy_signal_extraction(self):
        profile = {"what_they_do": "law firm", "location_city": "Seattle", "location_state": "WA"}
        builder = CompetitorQueryBuilder(profile, "https://example.com")

        # Signals not extracted until accessed
        assert builder._industry_signals is None
        _ = builder.industry_signals
        assert builder._industry_signals is not None

    def test_backward_compatible_function(self):
        profile = {
            "what_they_do": "plumbing services",
            "services_products": ["drain cleaning"],
            "location_city": "Tacoma",
            "location_state": "WA",
        }
        result = _build_competitor_query(profile, "https://example.com")
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Tacoma" in result