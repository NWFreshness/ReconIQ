import pytest

from research.parsing import JsonParsingError, extract_json_object, require_keys


# ── Fenced / messy JSON parsing ──────────────────────────────────────────────


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

    result = extract_json_object(raw)

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

    result = extract_json_object(raw)

    assert result["competitors"][0]["name"] == "Competitor A"
    assert result["data_limitations"] == ["Competitor data is inferred."]


# ── Invalid JSON handling ────────────────────────────────────────────────────


def test_invalid_json_raises_instead_of_flattening():
    """Trailing commas and other JSON syntax errors should raise JsonParsingError."""
    raw = '{"company_name": "Acme", "services_products": ["SEO", ]}'

    with pytest.raises(JsonParsingError):
        extract_json_object(raw)


def test_non_json_text_raises():
    """Plain text that isn't JSON at all should raise JsonParsingError."""
    raw = "platforms: LinkedIn\ncontent_quality: high"

    with pytest.raises(JsonParsingError):
        extract_json_object(raw)


def test_truncated_json_raises():
    """Incomplete JSON objects (truncated) should raise JsonParsingError."""
    raw = '{"swot": {"strengths": ["Brand"], "weaknesses": ["thin'

    with pytest.raises(JsonParsingError):
        extract_json_object(raw)


# ── require_keys ─────────────────────────────────────────────────────────────


def test_require_keys_passes_when_all_keys_present():
    data = {"company_name": "Acme", "what_they_do": "Builds widgets"}
    result = require_keys(data, ["company_name", "what_they_do"], context="test")
    assert result == data


def test_require_keys_raises_on_missing_keys():
    data = {"company_name": "Acme"}
    with pytest.raises(JsonParsingError, match="missing required keys"):
        require_keys(data, ["company_name", "what_they_do", "brand_voice"], context="test")