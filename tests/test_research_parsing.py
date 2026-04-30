import pytest

from research import company_profile, competitors, seo_keywords, social_content, swot
from research.parsing import JsonParsingError


def test_object_modules_parse_fenced_json():
    raw = '```json\n{"top_keywords": ["agency"], "content_gaps": []}\n```'

    assert seo_keywords._parse_response(raw) == {"top_keywords": ["agency"], "content_gaps": []}


def test_competitors_parse_fenced_json_array():
    raw = '```json\n[{"name": "Competitor A", "url": "https://example.com"}]\n```'

    assert competitors._parse_response(raw) == {
        "competitors": [{"name": "Competitor A", "url": "https://example.com"}]
    }


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
