"""Competitor comparison matrix formatting helpers."""
from __future__ import annotations

from typing import Any

MATRIX_COLUMNS = [
    "Competitor",
    "Pricing Tier",
    "Positioning",
    "Key Messaging",
    "Services",
    "Weaknesses",
    "Content Quality",
    "SEO Notes",
]

DASH = "—"


def build_competitor_matrix(competitor_result: dict[str, Any]) -> dict[str, Any]:
    """Convert competitor module output into a normalized matrix model.

    Supports both Phase 11 normalized fields and earlier Phase 9/10 field names
    so existing LLM outputs keep rendering cleanly.
    """
    rows: list[dict[str, Any]] = []
    competitors = competitor_result.get("competitors", [])
    if not isinstance(competitors, list):
        competitors = []

    for item in competitors:
        if not isinstance(item, dict):
            rows.append(_empty_row(name=str(item)))
            continue
        rows.append({
            "name": _text(item.get("name") or item.get("company_name") or "Unknown Competitor"),
            "url": _text(item.get("url")),
            "pricing_tier": _text(item.get("pricing_tier") or item.get("estimated_pricing_tier")),
            "positioning": _text(item.get("positioning")),
            "key_messaging": _text(item.get("key_messaging")),
            "services": _list(item.get("services") or item.get("inferred_services")),
            "weaknesses": _list(item.get("weaknesses")),
            "content_quality": _text(item.get("content_quality")),
            "seo_notes": _text(item.get("seo_notes")),
        })

    return {"columns": MATRIX_COLUMNS, "rows": rows}


def _empty_row(name: str) -> dict[str, Any]:
    return {
        "name": name or "Unknown Competitor",
        "url": "",
        "pricing_tier": DASH,
        "positioning": DASH,
        "key_messaging": DASH,
        "services": [],
        "weaknesses": [],
        "content_quality": DASH,
        "seo_notes": DASH,
    }


def _text(value: Any) -> str:
    if value is None:
        return DASH
    text = str(value).strip()
    return text or DASH


def _list(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]
