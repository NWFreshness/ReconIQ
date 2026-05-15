"""Tests for Phase 21: Visual report builder — data models and SVG generation."""
from __future__ import annotations

import pytest
from report.visuals import (
    SWOTQuadrant, build_swot_quadrant, swot_quadrant_svg,
    RadarChart, build_radar_chart, radar_chart_svg,
    BarChart, BarChartItem, build_content_gap_chart, bar_chart_svg,
    ScoreDonut, build_score_donut, score_donut_svg,
    RoadmapItem, build_automation_roadmap, roadmap_svg,
)


# ── SWOT Quadrant ───────────────────────────────────────────────────────────


class TestSWOTQuadrant:
    def test_build_swot_quadrant(self):
        swot = {
            "swot": {
                "strengths": ["Strong brand", "Good location"],
                "weaknesses": ["No website", "Poor SEO"],
                "opportunities": ["Online ordering", "Social media"],
                "threats": ["New competitors", "Economic downturn"],
            }
        }
        model = build_swot_quadrant(swot)
        assert isinstance(model, SWOTQuadrant)
        assert len(model.strengths) == 2
        assert len(model.weaknesses) == 2
        assert len(model.opportunities) == 2
        assert len(model.threats) == 2

    def test_build_swot_quadrant_empty(self):
        model = build_swot_quadrant({})
        assert model.strengths == ["—"]
        assert model.weaknesses == ["—"]
        assert model.opportunities == ["—"]
        assert model.threats == ["—"]

    def test_build_swot_quadrant_missing_keys(self):
        model = build_swot_quadrant({"swot": {"strengths": ["Good brand"]}})
        assert model.strengths == ["Good brand"]
        assert model.weaknesses == ["—"]

    def test_swot_quadrant_svg(self):
        swot = {
            "swot": {
                "strengths": ["Strong brand"],
                "weaknesses": ["No website"],
                "opportunities": ["Online ordering"],
                "threats": ["Competition"],
            }
        }
        model = build_swot_quadrant(swot)
        svg = swot_quadrant_svg(model)
        assert "<svg" in svg
        assert "</svg>" in svg
        assert "Strengths" in svg
        assert "Weaknesses" in svg
        assert "Opportunities" in svg
        assert "Threats" in svg
        assert "Strong brand" in svg

    def test_swot_quadrant_svg_dimensions(self):
        model = build_swot_quadrant({})
        svg = swot_quadrant_svg(model)
        assert 'width="800"' in svg
        assert 'height="500"' in svg


# ── Radar Chart ─────────────────────────────────────────────────────────────


class TestRadarChart:
    def test_build_radar_chart_from_competitors(self):
        competitor = {
            "competitors": [
                {"name": "CompA", "pricing_tier": "Premium", "content_quality": "High",
                 "positioning": "Enterprise"},
                {"name": "CompB", "pricing_tier": "Budget", "content_quality": "Low",
                 "positioning": "SMB"},
            ]
        }
        model = build_radar_chart(competitor)
        assert isinstance(model, RadarChart)
        assert len(model.axes) == 5  # 5 axes: Pricing Tier, Positioning, Content Quality, Services, SEO
        assert len(model.series) == 2

    def test_build_radar_chart_empty(self):
        model = build_radar_chart({})
        assert model.series == []

    def test_radar_chart_svg(self):
        competitor = {
            "competitors": [
                {"name": "CompA", "pricing_tier": "Premium"},
                {"name": "CompB", "pricing_tier": "Budget"},
            ]
        }
        model = build_radar_chart(competitor)
        svg = radar_chart_svg(model)
        assert "<svg" in svg
        assert "</svg>" in svg
        assert "CompA" in svg or "CompB" in svg

    def test_radar_chart_svg_with_legend(self):
        competitor = {
            "competitors": [
                {"name": "A", "pricing_tier": "Premium"},
            ]
        }
        model = build_radar_chart(competitor)
        svg = radar_chart_svg(model)
        assert "A" in svg


# ── Bar Chart (Content Gaps) ────────────────────────────────────────────────


class TestBarChart:
    def test_build_content_gap_chart(self):
        seo = {
            "content_gaps": [
                "No blog content about local services",
                "Missing location-specific landing pages",
                "No FAQ section",
            ],
            "seo_weaknesses": [
                "Missing meta descriptions",
                "No structured data",
            ],
        }
        model = build_content_gap_chart(seo)
        assert isinstance(model, BarChart)
        assert len(model.items) >= 1

    def test_build_content_gap_chart_empty(self):
        model = build_content_gap_chart({})
        assert model.items == []

    def test_bar_chart_svg(self):
        model = BarChart(
            title="Content Gaps",
            items=[
                BarChartItem(label="Blog content", value=80),
                BarChartItem(label="FAQ", value=60),
            ],
        )
        svg = bar_chart_svg(model)
        assert "<svg" in svg
        assert "Content Gaps" in svg
        assert "Blog content" in svg

    def test_bar_chart_svg_empty(self):
        model = BarChart(title="Empty", items=[])
        svg = bar_chart_svg(model)
        assert "<svg" in svg
        assert "No data" in svg


# ── Score Donut ──────────────────────────────────────────────────────────────


class TestScoreDonut:
    def test_build_score_donut(self):
        score = {
            "overall": 75.5,
            "grade": "B+",
            "marketing_gap_severity": 60,
            "ai_automation_fit": 80,
            "local_relevance": 70,
            "likely_budget": 65,
            "outreach_ease": 50,
            "urgency_signals": 40,
            "data_confidence": 90,
        }
        model = build_score_donut(score)
        assert isinstance(model, ScoreDonut)
        assert model.overall == 75.5
        assert model.grade == "B+"
        assert len(model.dimensions) == 7

    def test_build_score_donut_empty(self):
        model = build_score_donut({})
        assert model.overall == 0
        assert model.grade == ""

    def test_score_donut_svg(self):
        score = {"overall": 85, "grade": "A"}
        model = build_score_donut(score)
        svg = score_donut_svg(model)
        assert "<svg" in svg
        assert "85" in svg
        assert "A" in svg

    def test_score_donut_svg_dimensions(self):
        model = build_score_donut({"overall": 50, "grade": "C+"})
        svg = score_donut_svg(model)
        assert 'width="300"' in svg
        assert 'height="300"' in svg

    def test_score_donut_color_by_grade(self):
        score_a = {"overall": 90, "grade": "A+"}
        score_f = {"overall": 10, "grade": "F"}
        svg_a = score_donut_svg(build_score_donut(score_a))
        svg_f = score_donut_svg(build_score_donut(score_f))
        # Different grades should produce different colors
        assert svg_a != svg_f


# ── Roadmap ──────────────────────────────────────────────────────────────────


class TestRoadmap:
    def test_build_automation_roadmap_from_swot(self):
        swot = {
            "swot": {
                "weaknesses": ["No email marketing", "Poor website"],
                "opportunities": ["Online ordering", "Social media presence"],
            }
        }
        items = build_automation_roadmap(swot)
        assert isinstance(items, list)
        assert len(items) > 0
        assert all(isinstance(item, RoadmapItem) for item in items)

    def test_build_automation_roadmap_empty(self):
        items = build_automation_roadmap({})
        # Should still return default items
        assert isinstance(items, list)
        assert len(items) > 0

    def test_roadmap_svg(self):
        items = [
            RoadmapItem(phase="Phase 1", title="Fix website", priority="high"),
            RoadmapItem(phase="Phase 2", title="Start email marketing", priority="medium"),
        ]
        model = build_automation_roadmap({})  # Uses defaults
        svg = roadmap_svg(model)
        assert "<svg" in svg

    def test_roadmap_svg_styling(self):
        items = [
            RoadmapItem(phase="Phase 1", title="SEO improvements", priority="high"),
        ]
        model = items
        svg = roadmap_svg(model)
        assert "<svg" in svg
        assert "SEO improvements" in svg


# ── Markdown ASCII fallbacks ────────────────────────────────────────────────


class TestASCIIFallbacks:
    def test_swot_ascii_table(self):
        from report.visuals import swot_quadrant_ascii
        model = build_swot_quadrant({
            "swot": {
                "strengths": ["Strong brand"],
                "weaknesses": ["No website"],
                "opportunities": ["Online"],
                "threats": ["Competition"],
            }
        })
        text = swot_quadrant_ascii(model)
        assert "STRENGTHS" in text
        assert "WEAKNESSES" in text
        assert "Strong brand" in text

    def test_radar_ascii_table(self):
        from report.visuals import radar_chart_ascii
        competitor = {"competitors": [{"name": "A", "pricing_tier": "Premium"}]}
        model = build_radar_chart(competitor)
        text = radar_chart_ascii(model)
        assert "A" in text or "Competitor" in text

    def test_bar_chart_ascii(self):
        from report.visuals import bar_chart_ascii
        model = BarChart(title="Gaps", items=[
            BarChartItem(label="Blog", value=80),
            BarChartItem(label="FAQ", value=40),
        ])
        text = bar_chart_ascii(model)
        assert "Blog" in text
        assert "FAQ" in text

    def test_score_donut_ascii(self):
        from report.visuals import score_donut_ascii
        model = build_score_donut({"overall": 75, "grade": "B+"})
        text = score_donut_ascii(model)
        assert "75" in text
        assert "B+" in text
