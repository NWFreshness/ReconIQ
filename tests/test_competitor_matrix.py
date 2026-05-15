from __future__ import annotations

from research.competitor_matrix import build_competitor_matrix


def test_build_competitor_matrix_empty_competitors():
    matrix = build_competitor_matrix({"competitors": []})

    assert matrix["columns"] == [
        "Competitor",
        "Pricing Tier",
        "Positioning",
        "Key Messaging",
        "Services",
        "Weaknesses",
        "Content Quality",
        "SEO Notes",
    ]
    assert matrix["rows"] == []


def test_build_competitor_matrix_one_competitor_normalizes_legacy_fields():
    matrix = build_competitor_matrix({
        "competitors": [
            {
                "name": "WidgetCo",
                "url": "https://widgetco.example",
                "estimated_pricing_tier": "premium",
                "positioning": "Regional premium provider.",
                "key_messaging": "Widgets that scale.",
                "inferred_services": ["Consulting", "Maintenance"],
                "weaknesses": ["Generic messaging"],
            }
        ]
    })

    assert matrix["rows"] == [
        {
            "name": "WidgetCo",
            "url": "https://widgetco.example",
            "pricing_tier": "premium",
            "positioning": "Regional premium provider.",
            "key_messaging": "Widgets that scale.",
            "services": ["Consulting", "Maintenance"],
            "weaknesses": ["Generic messaging"],
            "content_quality": "—",
            "seo_notes": "—",
        }
    ]


def test_build_competitor_matrix_multiple_competitors_with_partial_fields():
    matrix = build_competitor_matrix({
        "competitors": [
            {"name": "Budget Widgets", "pricing_tier": "budget", "services": ["Repair"]},
            {"name": "Enterprise Widgets", "content_quality": "strong", "seo_notes": "Ranks for service pages"},
        ]
    })

    assert len(matrix["rows"]) == 2
    assert matrix["rows"][0]["pricing_tier"] == "budget"
    assert matrix["rows"][0]["services"] == ["Repair"]
    assert matrix["rows"][0]["seo_notes"] == "—"
    assert matrix["rows"][1]["pricing_tier"] == "—"
    assert matrix["rows"][1]["content_quality"] == "strong"
    assert matrix["rows"][1]["seo_notes"] == "Ranks for service pages"
