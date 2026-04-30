import pytest

from research.parsing import JsonParsingError, extract_json_array, extract_json_object, require_keys


def test_extract_json_object_from_plain_json():
    raw = '{"company_name": "Acme", "services": ["SEO", "Ads"]}'

    result = extract_json_object(raw)

    assert result == {"company_name": "Acme", "services": ["SEO", "Ads"]}


def test_extract_json_object_from_fenced_markdown():
    raw = """
    Here is the analysis:

    ```json
    {"company_name": "Acme", "score": 7}
    ```
    """

    result = extract_json_object(raw)

    assert result == {"company_name": "Acme", "score": 7}


def test_extract_json_object_from_surrounding_text():
    raw = 'Analysis result: {"company_name": "Acme", "score": 7} End.'

    result = extract_json_object(raw)

    assert result == {"company_name": "Acme", "score": 7}


def test_extract_json_array_from_plain_json():
    raw = '[{"name": "Competitor A"}, {"name": "Competitor B"}]'

    result = extract_json_array(raw)

    assert result == [{"name": "Competitor A"}, {"name": "Competitor B"}]


def test_extract_json_array_from_fenced_markdown():
    raw = """
    ```json
    [{"name": "Competitor A"}, {"name": "Competitor B"}]
    ```
    """

    result = extract_json_array(raw)

    assert result == [{"name": "Competitor A"}, {"name": "Competitor B"}]


def test_invalid_json_raises_clear_error():
    raw = '{"company_name": "Acme", "score": }'

    with pytest.raises(JsonParsingError, match="Could not parse JSON object"):
        extract_json_object(raw)


def test_missing_json_raises_clear_error():
    raw = "company_name: Acme\nscore: 7"

    with pytest.raises(JsonParsingError, match="No JSON object found"):
        extract_json_object(raw)


def test_bad_nested_json_is_not_flattened_to_key_value_output():
    raw = '{"company": {"name": "Acme", "services": ["SEO", ]}}'

    with pytest.raises(JsonParsingError):
        extract_json_object(raw)


def test_require_keys_returns_data_when_present():
    data = {"company_name": "Acme", "what_they_do": "Marketing"}

    result = require_keys(data, ["company_name", "what_they_do"], context="company profile")

    assert result is data


def test_require_keys_raises_for_missing_keys():
    data = {"company_name": "Acme"}

    with pytest.raises(JsonParsingError, match="company profile missing required keys: what_they_do"):
        require_keys(data, ["company_name", "what_they_do"], context="company profile")
