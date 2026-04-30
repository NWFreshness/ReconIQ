import pytest

from research import company_profile, competitors, seo_keywords, social_content, swot
from research.parsing import JsonParsingError


def test_object_modules_parse_fenced_json():
    raw = '''```json
{
  "top_keywords": ["agency"],
  "content_gaps": [],
  "seo_weaknesses": [],
  "quick_wins": [],
  "estimated_traffic_tier": "low — inferred",
  "local_seo_signals": "weak — inferred",
  "data_confidence": "low",
  "data_limitations": ["No measured SEO data was available."]
}
```'''

    result = seo_keywords._parse_response(raw)

    assert result["top_keywords"] == ["agency"]
    assert result["data_confidence"] == "low"


def test_competitors_parse_fenced_json_array():
    raw = '''```json
{
  "competitors": [
    {
      "name": "Competitor A",
      "url": "https://example.com",
      "positioning": "Local competitor",
      "estimated_pricing_tier": "mid-market",
      "key_messaging": "Reliable service",
      "weaknesses": ["thin content"],
      "inferred_services": ["consulting"]
    }
  ],
  "data_confidence": "low",
  "data_limitations": ["Competitor data is inferred."]
}
```'''

    result = competitors._parse_response(raw)

    assert result["competitors"][0]["name"] == "Competitor A"
    assert result["data_limitations"] == ["Competitor data is inferred."]


def test_company_profile_invalid_json_raises_instead_of_flattening():
    raw = '{"company_name": "Acme", "services_products": ["SEO", ]}'

    with pytest.raises(JsonParsingError):
        company_profile._parse_response(raw)


def test_social_content_invalid_json_raises_instead_of_flattening():
    raw = "platforms: LinkedIn\ncontent_quality: high"

    with pytest.raises(JsonParsingError):
        social_content._parse_response(raw)


def test_swot_invalid_json_raises_instead_of_flattening():
    raw = '{"swot": {"strengths": ["Brand"], "weaknesses": [}}'

    with pytest.raises(JsonParsingError):
        swot._parse_response(raw)
