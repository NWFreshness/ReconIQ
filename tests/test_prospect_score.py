"""Tests for deterministic prospect scoring."""
from __future__ import annotations

import pytest

from research.prospect_score import (
    ProspectScore,
    grade_from_score,
    score_marketing_gap,
    score_ai_fit,
    score_local_relevance,
    score_likely_budget,
    score_outreach_ease,
    score_urgency,
    score_data_confidence,
    compute_prospect_score,
    WEIGHTS,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _minimal_profile() -> dict:
    return {
        "company_name": "Test Co",
        "what_they_do": "A small business",
        "target_audience": "Local customers",
        "value_proposition": "Quality service",
        "brand_voice": "friendly",
        "primary_cta": "Contact us",
        "services_products": [],
        "marketing_channels": [],
        "location_city": "",
        "location_state": "",
        "location_zip": "",
        "service_area": [],
        "data_confidence": "",
        "data_limitations": [],
    }


def _minimal_seo() -> dict:
    return {
        "top_keywords": [],
        "content_gaps": [],
        "seo_weaknesses": [],
        "quick_wins": [],
        "estimated_traffic_tier": "medium",
        "local_seo_signals": "moderate",
        "data_confidence": "",
        "data_limitations": [],
    }


def _minimal_competitor() -> dict:
    return {
        "competitors": [],
        "scraped_competitors": [],
        "inferred_competitors": [],
        "data_confidence": "",
        "data_limitations": [],
    }


def _minimal_social() -> dict:
    return {
        "platforms": [],
        "verified_social_accounts": [],
        "inferred_platforms": [],
        "content_quality": "",
        "content_frequency": "",
        "engagement_signals": "",
        "review_sites": [],
        "blog_or_resources": "",
        "content_gaps": [],
        "email_signals": "",
        "data_confidence": "",
        "data_limitations": [],
    }


def _minimal_swot() -> dict:
    return {
        "swot": {
            "strengths": [],
            "weaknesses": [],
            "opportunities": [],
            "threats": [],
        },
        "acquisition_angle": "",
        "talking_points": [],
        "recommended_next_steps": [],
        "competitive_advantage": "",
        "lead_generation_strategy": "",
        "close_rate_strategy": "",
        "data_confidence": "",
        "data_limitations": [],
    }


# ── Grade mapping ────────────────────────────────────────────────────────────

class TestGradeMapping:
    def test_a_plus(self):
        assert grade_from_score(95) == "A+"
        assert grade_from_score(90) == "A+"

    def test_a(self):
        assert grade_from_score(85) == "A"
        assert grade_from_score(80) == "A"

    def test_b_plus(self):
        assert grade_from_score(75) == "B+"
        assert grade_from_score(70) == "B+"

    def test_b(self):
        assert grade_from_score(65) == "B"
        assert grade_from_score(60) == "B"

    def test_c_plus(self):
        assert grade_from_score(55) == "C+"
        assert grade_from_score(50) == "C+"

    def test_c(self):
        assert grade_from_score(45) == "C"
        assert grade_from_score(40) == "C"

    def test_d(self):
        assert grade_from_score(30) == "D"
        assert grade_from_score(25) == "D"

    def test_f(self):
        assert grade_from_score(20) == "F"
        assert grade_from_score(0) == "F"

    def test_boundary_values(self):
        """Test exact boundaries between grades."""
        assert grade_from_score(89.9) == "A"
        assert grade_from_score(79.9) == "B+"
        assert grade_from_score(69.9) == "B"
        assert grade_from_score(49.9) == "C"
        assert grade_from_score(24.9) == "F"  # D starts at 25


# ── Weights sanity ───────────────────────────────────────────────────────────

class TestWeights:
    def test_weights_sum_to_one(self):
        assert sum(WEIGHTS.values()) == pytest.approx(1.0)

    def test_all_weights_positive(self):
        for k, v in WEIGHTS.items():
            assert v > 0, f"Weight for {k} must be positive"


# ── Marketing gap scoring ────────────────────────────────────────────────────

class TestScoreMarketingGap:
    def test_empty_inputs_low_score(self):
        score = score_marketing_gap({}, {}, {})
        assert score > 0  # empty platforms = gap detected

    def test_many_seo_weaknesses_high_score(self):
        seo = _minimal_seo()
        seo["seo_weaknesses"] = [
            "No meta descriptions",
            "No schema markup",
            "No backlinks",
            "Thin content",
            "No blog",
        ]
        score = score_marketing_gap({}, seo, {})
        assert score >= 30  # 5 weaknesses * 8 = 40

    def test_many_content_gaps_add_score(self):
        seo = _minimal_seo()
        seo["content_gaps"] = ["pricing page", "about page", "faq", "testimonials"]
        score = score_marketing_gap({}, seo, {})
        assert score >= 15  # 4 gaps * 5 = 20

    def test_no_social_platforms(self):
        social = _minimal_social()
        score = score_marketing_gap({}, _minimal_seo(), social)
        assert score >= 10  # no platforms bonus

    def test_weak_engagement(self):
        social = _minimal_social()
        social["engagement_signals"] = "weak"
        score = score_marketing_gap({}, _minimal_seo(), social)
        assert score >= 10  # weak engagement bonus

    def test_no_blog(self):
        social = _minimal_social()
        social["blog_or_resources"] = "no"
        score = score_marketing_gap({}, _minimal_seo(), social)
        assert score >= 5  # no blog bonus

    def test_score_capped_at_100(self):
        """Ensure score never exceeds 100 even with extreme inputs."""
        seo = _minimal_seo()
        seo["seo_weaknesses"] = ["x"] * 20
        seo["content_gaps"] = ["x"] * 20
        score = score_marketing_gap({}, seo, {})
        assert score <= 100


# ── AI automation fit scoring ───────────────────────────────────────────────

class TestScoreAIFit:
    def test_empty_inputs_detects_opportunity(self):
        score = score_ai_fit({}, {}, {})
        assert score > 0  # no digital services = AI opportunity

    def test_no_online_ordering(self):
        profile = _minimal_profile()
        score = score_ai_fit(profile, {}, {})
        assert score >= 20  # no online ordering bonus

    def test_no_email_marketing(self):
        social = _minimal_social()
        social["email_signals"] = "absent"
        score = score_ai_fit({}, social, {})
        assert score >= 15  # no email bonus

    def test_swot_weaknesses_mention_digital_gaps(self):
        swot = _minimal_swot()
        swot["swot"]["weaknesses"] = [
            "No online ordering system",
            "Poor digital presence",
            "No automation in place",
        ]
        score = score_ai_fit({}, {}, swot)
        assert score > 0

    def test_limited_marketing_channels(self):
        profile = _minimal_profile()
        profile["marketing_channels"] = ["in-person"]
        score = score_ai_fit(profile, {}, {})
        assert score >= 10  # in-person channel bonus

    def test_sporadic_content(self):
        social = _minimal_social()
        social["content_frequency"] = "sporadic"
        score = score_ai_fit({}, social, {})
        assert score >= 10  # sporadic content bonus

    def test_score_capped_at_100(self):
        profile = _minimal_profile()
        profile["marketing_channels"] = ["in-person"]
        social = _minimal_social()
        social["email_signals"] = "absent"
        social["content_frequency"] = "sporadic"
        swot = _minimal_swot()
        swot["swot"]["weaknesses"] = [
            "no online ordering",
            "no automation",
            "no digital strategy",
            "poor website",
            "no crm",
            "no email system",
        ]
        score = score_ai_fit(profile, social, swot)
        assert score <= 100


# ── Local relevance scoring ─────────────────────────────────────────────────

class TestScoreLocalRelevance:
    def test_empty_inputs_zero_score(self):
        score = score_local_relevance({})
        assert score == 0

    def test_vancouver_wa_high_score(self):
        profile = _minimal_profile()
        profile["location_city"] = "Vancouver"
        profile["location_state"] = "WA"
        score = score_local_relevance(profile)
        assert score >= 70  # city+state + Vancouver + WA

    def test_longview_wa(self):
        profile = _minimal_profile()
        profile["location_city"] = "Longview"
        profile["location_state"] = "WA"
        score = score_local_relevance(profile)
        assert score >= 70

    def test_out_of_state(self):
        profile = _minimal_profile()
        profile["location_city"] = "Los Angeles"
        profile["location_state"] = "CA"
        score = score_local_relevance(profile)
        assert score < 60  # no local bonus, no WA bonus

    def test_service_area_adds_points(self):
        profile = _minimal_profile()
        profile["location_city"] = "Vancouver"
        profile["location_state"] = "WA"
        profile["service_area"] = ["Clark County", "Cowlitz County"]
        score = score_local_relevance(profile)
        assert score >= 80

    def test_score_capped_at_100(self):
        profile = _minimal_profile()
        profile["location_city"] = "Vancouver"
        profile["location_state"] = "WA"
        profile["service_area"] = ["Everywhere"] * 20
        score = score_local_relevance(profile)
        assert score <= 100


# ── Likely budget scoring ───────────────────────────────────────────────────

class TestLikelyBudget:
    def test_empty_inputs_zero_score(self):
        score = score_likely_budget({})
        assert score == 0

    def test_many_services(self):
        profile = _minimal_profile()
        profile["services_products"] = ["coffee", "pastries", "catering", "events"]
        score = score_likely_budget(profile)
        assert score >= 25

    def test_multiple_channels(self):
        profile = _minimal_profile()
        profile["marketing_channels"] = ["website", "facebook", "instagram", "email"]
        score = score_likely_budget(profile)
        assert score >= 20

    def test_established_business(self):
        profile = _minimal_profile()
        profile["value_proposition"] = "Serving since 2018"
        score = score_likely_budget(profile)
        assert score >= 15

    def test_has_location(self):
        profile = _minimal_profile()
        profile["location_city"] = "Portland"
        score = score_likely_budget(profile)
        assert score >= 10

    def test_score_capped_at_100(self):
        profile = _minimal_profile()
        profile["services_products"] = ["x"] * 20
        profile["marketing_channels"] = ["x"] * 20
        score = score_likely_budget(profile)
        assert score <= 100


# ── Outreach ease scoring ───────────────────────────────────────────────────

class TestOutreachEase:
    def test_empty_inputs_zero_score(self):
        score = score_outreach_ease({}, {})
        assert score == 0

    def test_social_accounts(self):
        social = _minimal_social()
        social["verified_social_accounts"] = [
            {"platform": "facebook", "url": "https://fb.com/test"},
            {"platform": "instagram", "url": "https://ig.com/test"},
        ]
        score = score_outreach_ease({}, social)
        assert score >= 25

    def test_digital_channels(self):
        profile = _minimal_profile()
        profile["marketing_channels"] = ["website", "facebook", "instagram"]
        score = score_outreach_ease(profile, {})
        assert score >= 15

    def test_partial_profile_info(self):
        profile = _minimal_profile()
        profile["company_name"] = "Test Co"
        profile["location_city"] = "Vancouver"
        score = score_outreach_ease(profile, {})
        assert score >= 15

    def test_score_capped_at_100(self):
        social = _minimal_social()
        social["verified_social_accounts"] = [{"platform": "x", "url": ""}] * 20
        score = score_outreach_ease({}, social)
        assert score <= 100


# ── Urgency scoring ─────────────────────────────────────────────────────────

class TestUrgency:
    def test_empty_inputs_zero_score(self):
        score = score_urgency({}, {})
        assert score == 0

    def test_low_traffic_tier(self):
        seo = _minimal_seo()
        seo["estimated_traffic_tier"] = "low"
        score = score_urgency({}, seo)
        assert score >= 20

    def test_dict_traffic_tier(self):
        seo = _minimal_seo()
        seo["estimated_traffic_tier"] = {"tier": "low", "explanation": "test"}
        score = score_urgency({}, seo)
        assert score >= 20

    def test_swot_threats(self):
        swot = _minimal_swot()
        swot["swot"]["threats"] = [
            "Competing chains opening nearby",
            "Economic downturn reducing spending",
            "Rising supply chain costs",
        ]
        score = score_urgency(swot, {})
        assert score > 0

    def test_weak_local_seo(self):
        seo = _minimal_seo()
        seo["local_seo_signals"] = "weak"
        score = score_urgency({}, seo)
        assert score >= 15

    def test_many_opportunities_unexploited(self):
        swot = _minimal_swot()
        swot["swot"]["opportunities"] = [
            "Online ordering",
            "Email marketing",
            "Social media automation",
            "Local SEO improvements",
        ]
        score = score_urgency(swot, {})
        assert score >= 10

    def test_score_capped_at_100(self):
        swot = _minimal_swot()
        swot["swot"]["threats"] = ["competitor"] * 20
        seo = _minimal_seo()
        seo["estimated_traffic_tier"] = "low"
        seo["local_seo_signals"] = "weak"
        score = score_urgency(swot, seo)
        assert score <= 100


# ── Data confidence scoring ──────────────────────────────────────────────────

class TestDataConfidence:
    def test_all_high_confidence(self):
        mods = [
            {"data_confidence": "high"},
            {"data_confidence": "high"},
            {"data_confidence": "high"},
            {"data_confidence": "high"},
            {"data_confidence": "high"},
        ]
        score = score_data_confidence(*mods)
        assert score == 100

    def test_all_low_confidence(self):
        mods = [
            {"data_confidence": "low"},
            {"data_confidence": "low"},
            {"data_confidence": "low"},
            {"data_confidence": "low"},
            {"data_confidence": "low"},
        ]
        score = score_data_confidence(*mods)
        assert score == 30

    def test_mixed_confidence(self):
        mods = [
            {"data_confidence": "high"},
            {"data_confidence": "medium"},
            {"data_confidence": "low"},
            {"data_confidence": "high"},
            {"data_confidence": "medium"},
        ]
        score = score_data_confidence(*mods)
        assert 40 <= score <= 70  # roughly (100+60+30+100+60)/5 = 70

    def test_empty_inputs_default(self):
        score = score_data_confidence({}, {}, {}, {}, {})
        assert score == 50  # default unknown


# ── Full prospect score computation ─────────────────────────────────────────

class TestComputeProspectScore:
    def test_all_empty_data(self):
        result = compute_prospect_score({}, {}, {}, {}, {})
        assert isinstance(result, ProspectScore)
        assert 0 <= result.overall <= 100
        assert result.grade == grade_from_score(result.overall)
        assert len(result.breakdown) == 7

    def test_perfect_prospect(self):
        """A Vancouver coffee shop with terrible digital presence."""
        profile = _minimal_profile()
        profile["company_name"] = "Creed Coffee Co."
        profile["location_city"] = "Vancouver"
        profile["location_state"] = "WA"
        profile["services_products"] = ["coffee", "pastries", "catering", "events"]
        profile["marketing_channels"] = ["website", "in-person"]
        profile["value_proposition"] = "Serving since 2018"

        seo = _minimal_seo()
        seo["seo_weaknesses"] = [
            "No meta descriptions",
            "No schema markup",
            "No backlinks",
            "Thin content",
        ]
        seo["content_gaps"] = ["pricing", "about", "faq", "blog"]
        seo["estimated_traffic_tier"] = "low"
        seo["local_seo_signals"] = "weak"
        seo["data_confidence"] = "high"

        competitor = _minimal_competitor()
        competitor["data_confidence"] = "low"

        social = _minimal_social()
        social["platforms"] = ["facebook", "instagram"]
        social["verified_social_accounts"] = [
            {"platform": "facebook", "url": "https://fb.com/creed"},
            {"platform": "instagram", "url": "https://ig.com/creed"},
        ]
        social["engagement_signals"] = "weak"
        social["content_frequency"] = "sporadic"
        social["email_signals"] = "absent"
        social["blog_or_resources"] = "no"
        social["data_confidence"] = "high"

        swot = _minimal_swot()
        swot["swot"]["weaknesses"] = [
            "No online ordering system",
            "Poor digital presence",
            "No email marketing",
            "No automation",
        ]
        swot["swot"]["threats"] = [
            "Competing chains opening nearby",
            "Economic downturn",
        ]
        swot["swot"]["opportunities"] = [
            "Online ordering",
            "Email marketing",
            "Social automation",
        ]
        swot["data_confidence"] = "high"

        result = compute_prospect_score(profile, seo, competitor, social, swot)

        assert isinstance(result, ProspectScore)
        assert 0 <= result.overall <= 100
        assert result.grade in ("A+", "A", "B+", "B", "C+", "C", "D", "F")
        assert len(result.breakdown) == 7
        assert result.marketing_gap_severity > 0
        assert result.ai_automation_fit > 0
        assert result.local_relevance >= 70  # Vancouver WA
        assert len(result.summary) > 0

    def test_result_is_not_empty(self):
        """Even with minimal data, all dimensions should have scores."""
        result = compute_prospect_score({}, {}, {}, {}, {})
        assert result.marketing_gap_severity >= 0
        assert result.ai_automation_fit >= 0
        assert result.local_relevance >= 0
        assert result.likely_budget >= 0
        assert result.outreach_ease >= 0
        assert result.urgency_signals >= 0
        assert result.data_confidence >= 0


# ── ProspectScore dataclass ──────────────────────────────────────────────────

class TestProspectScoreDataclass:
    def test_default_values(self):
        ps = ProspectScore()
        assert ps.overall == 0.0
        assert ps.grade == ""
        assert ps.breakdown == []
        assert ps.summary == ""

    def test_to_dict_compatible(self):
        """ProspectScore fields should be serializable."""
        ps = ProspectScore(overall=75.5, grade="B+", summary="Good prospect")
        import dataclasses
        d = dataclasses.asdict(ps)
        assert d["overall"] == 75.5
        assert d["grade"] == "B+"
        assert d["summary"] == "Good prospect"
