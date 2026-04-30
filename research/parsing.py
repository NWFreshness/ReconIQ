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


# ── Retry helper ────────────────────────────────────────────────────────────

_JSON_RETRY_REMINDER = (
    "\n\nIMPORTANT: Your previous response could not be parsed as valid JSON. "
    "Please return ONLY a valid JSON object with no surrounding text, no markdown fences, "
    "no comments, and no trailing commas. Double-check that every key and string value "
    "uses double quotes."
)

# Lower temperature for retry attempts — more deterministic output
_RETRY_TEMPERATURES = [0.7, 0.4, 0.3]


def llm_json_call(
    llm_complete: callable,
    prompt: str,
    module: str,
    system: str,
    required_keys: list[str] | None = None,
    context: str = "",
    max_tokens: int = 2048,
    max_retries: int = 2,
) -> dict:
    """Call the LLM, parse the JSON response, and retry on parse failures.

    This wraps the common pattern shared by every research module:
    call LLM → extract JSON → validate required keys.

    On parse failure, retries with:
      1st retry: same temperature, but appends a JSON reminder to the prompt
      2nd retry: lower temperature (0.3), JSON reminder appended

    Args:
        llm_complete: LLM completion callable from core/services.
        prompt: The user prompt for the LLM.
        module: Module name for LLM routing (e.g. "company_profile").
        system: System prompt for the LLM.
        required_keys: Keys that must exist in the parsed JSON dict.
                      If None, only JSON parsing is attempted (no key validation).
        context: Human-readable context for error messages (e.g. "company profile").
        max_tokens: Max tokens for the LLM completion.
        max_retries: Number of retry attempts after the first failure (default 2).

    Returns:
        Parsed and validated dict from the LLM response.

    Raises:
        JsonParsingError: If all attempts fail to produce valid JSON.
    """
    last_error: Exception | None = None
    attempt = 0
    max_attempts = 1 + max_retries

    while attempt < max_attempts:
        temperature = _RETRY_TEMPERATURES[min(attempt, len(_RETRY_TEMPERATURES) - 1)]

        # On retries, append the JSON reminder to the prompt
        attempt_prompt = prompt
        if attempt > 0:
            attempt_prompt = prompt + _JSON_RETRY_REMINDER

        raw = llm_complete(
            prompt=attempt_prompt,
            module=module,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        try:
            data = extract_json_object(raw)
        except JsonParsingError as exc:
            last_error = exc
            attempt += 1
            continue

        # JSON parsed successfully — validate keys if requested
        if required_keys is not None:
            try:
                data = require_keys(data, required_keys, context=context or module)
            except JsonParsingError as exc:
                last_error = exc
                attempt += 1
                continue

        return data

    # All attempts exhausted
    raise last_error  # type: ignore[misc]


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
