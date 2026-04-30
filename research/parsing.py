"""Shared JSON parsing helpers for LLM-backed research modules."""
from __future__ import annotations

import json
from typing import Any


JSON_RESPONSE_RULES = (
    "Return valid JSON only.\n"
    "Use double quotes for all keys and string values.\n"
    "Do not wrap the JSON in markdown.\n"
    "Do not include comments, explanations, or trailing commas."
)


class JsonParsingError(ValueError):
    """Raised when an LLM response cannot be parsed as the expected JSON shape."""


_DECODER = json.JSONDecoder()


def extract_json_object(raw: str) -> dict[str, Any]:
    """Extract the first valid JSON object from an LLM response.

    The response may be plain JSON, fenced markdown, or JSON surrounded by
    explanatory text. Invalid JSON raises a clear error instead of falling back
    to lossy key/value parsing.
    """
    value = _extract_json_value(raw, expected_type=dict, label="object")
    return value


def extract_json_array(raw: str) -> list[Any]:
    """Extract the first valid JSON array from an LLM response."""
    value = _extract_json_value(raw, expected_type=list, label="array")
    return value


def require_keys(data: dict[str, Any], keys: list[str], context: str) -> dict[str, Any]:
    """Require specific keys in parsed JSON data and return the original dict."""
    missing = [key for key in keys if key not in data]
    if missing:
        raise JsonParsingError(f"{context} missing required keys: {', '.join(missing)}")
    return data


def _extract_json_value(raw: str, expected_type: type, label: str):
    if not isinstance(raw, str):
        raise JsonParsingError(f"Expected raw LLM response to be a string, got {type(raw).__name__}")

    expected_start_char = "{" if expected_type is dict else "["
    saw_candidate = False
    errors: list[str] = []

    index = 0
    while index < len(raw):
        char = raw[index]
        if char not in "[{":
            index += 1
            continue

        if char == expected_start_char:
            saw_candidate = True

        try:
            value, end = _DECODER.raw_decode(raw[index:])
        except json.JSONDecodeError as exc:
            if char == expected_start_char:
                errors.append(str(exc))
            index += 1
            continue

        if isinstance(value, expected_type):
            return value

        index += max(end, 1)

    if saw_candidate:
        detail = f": {errors[0]}" if errors else ""
        raise JsonParsingError(f"Could not parse JSON {label}{detail}")

    raise JsonParsingError(f"No JSON {label} found in LLM response")
