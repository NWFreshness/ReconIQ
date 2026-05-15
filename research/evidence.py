"""Evidence helpers for traceable ReconIQ report claims."""
from __future__ import annotations

from typing import Any

from scraper.models import LinkData, PageData, ScrapeResult, SocialLink

EvidenceItem = dict[str, str]


def evidence_item(
    *,
    module: str,
    source_type: str,
    url: str,
    page_title: str,
    selector_or_field: str,
    excerpt: str,
    confidence: str = "high",
) -> EvidenceItem:
    """Create a normalized evidence item and trim noisy whitespace."""
    return {
        "module": module,
        "source_type": source_type,
        "url": url,
        "page_title": page_title,
        "selector_or_field": selector_or_field,
        "excerpt": _clean_excerpt(excerpt),
        "confidence": confidence,
    }


def collect_scrape_evidence(result: ScrapeResult | None, module: str, limit: int = 20) -> list[EvidenceItem]:
    """Collect evidence items from structured scrape output for a module.

    The evidence list is intentionally conservative: it records raw observed
    website facts (title, meta fields, headings, links, contact info, and page
    excerpts) and leaves LLM interpretations to be labeled separately by the
    module output.
    """
    if result is None:
        return []

    items: list[EvidenceItem] = []
    _add_homepage_evidence(items, result, module)
    _add_link_evidence(items, result.internal_links, result, module, "internal_links")
    _add_link_evidence(items, result.external_links, result, module, "external_links")
    _add_social_evidence(items, result.social_links, result, module)
    _add_subpage_evidence(items, result.pages, module)
    return items[:limit]


def attach_evidence(data: dict[str, Any], evidence: list[EvidenceItem]) -> dict[str, Any]:
    """Return module data with evidence attached when available."""
    if evidence:
        data["evidence"] = evidence
    return data


def _add_homepage_evidence(items: list[EvidenceItem], result: ScrapeResult, module: str) -> None:
    homepage = result.url
    title = result.title
    observed_fields = [
        ("title", result.title),
        ("meta_description", result.meta_description),
        ("meta_keywords", ", ".join(result.meta_keywords)),
        ("body_text", result.body_text),
    ]
    for field, value in observed_fields:
        if value:
            items.append(
                evidence_item(
                    module=module,
                    source_type="scrape",
                    url=homepage,
                    page_title=title,
                    selector_or_field=field,
                    excerpt=value,
                )
            )

    for level, headings in result.headings.items():
        for heading in headings[:5]:
            items.append(
                evidence_item(
                    module=module,
                    source_type="scrape",
                    url=homepage,
                    page_title=title,
                    selector_or_field=f"headings.{level}",
                    excerpt=heading,
                )
            )

    for email in result.emails[:5]:
        items.append(
            evidence_item(
                module=module,
                source_type="scrape",
                url=homepage,
                page_title=title,
                selector_or_field="emails",
                excerpt=email,
            )
        )

    for phone in result.phone_numbers[:5]:
        items.append(
            evidence_item(
                module=module,
                source_type="scrape",
                url=homepage,
                page_title=title,
                selector_or_field="phone_numbers",
                excerpt=phone,
            )
        )


def _add_link_evidence(
    items: list[EvidenceItem],
    links: list[LinkData],
    result: ScrapeResult,
    module: str,
    field: str,
) -> None:
    for link in links[:8]:
        items.append(
            evidence_item(
                module=module,
                source_type="scrape",
                url=result.url,
                page_title=result.title,
                selector_or_field=field,
                excerpt=f"{link.text or '(no text)'}: {link.href}",
            )
        )


def _add_social_evidence(
    items: list[EvidenceItem],
    links: list[SocialLink],
    result: ScrapeResult,
    module: str,
) -> None:
    for link in links:
        items.append(
            evidence_item(
                module=module,
                source_type="scrape",
                url=result.url,
                page_title=result.title,
                selector_or_field=f"social_links.{link.platform}",
                excerpt=link.url,
            )
        )


def _add_subpage_evidence(items: list[EvidenceItem], pages: list[PageData], module: str) -> None:
    for page in pages[:8]:
        if page.title:
            items.append(
                evidence_item(
                    module=module,
                    source_type="scrape",
                    url=page.url,
                    page_title=page.title,
                    selector_or_field="page.title",
                    excerpt=page.title,
                )
            )
        for level, headings in page.headings.items():
            for heading in headings[:3]:
                items.append(
                    evidence_item(
                        module=module,
                        source_type="scrape",
                        url=page.url,
                        page_title=page.title,
                        selector_or_field=f"page.headings.{level}",
                        excerpt=heading,
                    )
                )
        if page.text:
            items.append(
                evidence_item(
                    module=module,
                    source_type="scrape",
                    url=page.url,
                    page_title=page.title,
                    selector_or_field="page.text",
                    excerpt=page.text,
                )
            )


def _clean_excerpt(text: str, max_chars: int = 320) -> str:
    cleaned = " ".join(str(text).split())
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[:max_chars].rstrip() + "…"
