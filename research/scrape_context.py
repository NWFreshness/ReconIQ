"""Prompt formatting helpers for structured scrape results."""
from __future__ import annotations

import json
from urllib.parse import urlparse

from scraper.models import LinkData, ScrapeResult, SocialLink


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "…"


def _format_headings(headings: dict[str, list[str]]) -> str:
    lines: list[str] = []
    for level in ("h1", "h2", "h3"):
        values = headings.get(level, [])
        if values:
            lines.append(f"{level.upper()}: " + "; ".join(values[:8]))
    return "\n".join(lines) or "None found"


def _format_links(links: list[LinkData], limit: int = 12) -> str:
    if not links:
        return "None found"
    return "\n".join(f"- {link.text or '(no text)'}: {link.href}" for link in links[:limit])


def _format_social_links(links: list[SocialLink]) -> str:
    if not links:
        return "None found"
    return "\n".join(f"- {link.platform}: {link.url}" for link in links)


def format_company_context(result: ScrapeResult, max_chars: int = 12_000) -> str:
    """Format a multi-page scrape for company-profile extraction."""
    parts = [
        f"URL: {result.url}",
        f"Title: {result.title}",
        f"Meta description: {result.meta_description or 'None found'}",
        f"Meta keywords: {', '.join(result.meta_keywords) or 'None found'}",
        "Headings:\n" + _format_headings(result.headings),
        f"Phone numbers: {', '.join(result.phone_numbers) or 'None found'}",
        f"Emails: {', '.join(result.emails) or 'None found'}",
        "Verified social links found on site:\n" + _format_social_links(result.social_links),
        "Internal links:\n" + _format_links(result.internal_links, limit=10),
    ]
    if result.json_ld:
        parts.append("JSON-LD structured data:\n" + _truncate(json.dumps(result.json_ld, ensure_ascii=False), 1500))
    parts.append("Homepage text:\n" + _truncate(result.body_text, 5000))
    if result.pages:
        subpage_lines = []
        for page in result.pages[:8]:
            subpage_lines.append(
                f"Subpage: {page.url}\nTitle: {page.title}\nHeadings:\n{_format_headings(page.headings)}\nText:\n{_truncate(page.text, 1600)}"
            )
        parts.append("Crawled subpages:\n" + "\n\n".join(subpage_lines))
    return _truncate("\n\n".join(parts), max_chars)


def format_seo_context(result: ScrapeResult, max_chars: int = 6_000) -> str:
    parts = [
        f"Title: {result.title}",
        f"Meta description: {result.meta_description or 'None found'}",
        f"Meta keywords: {', '.join(result.meta_keywords) or 'None found'}",
        "Headings:\n" + _format_headings(result.headings),
        "Open Graph tags:\n" + (json.dumps(result.og_tags, ensure_ascii=False) if result.og_tags else "None found"),
        "Internal link anchor text:\n" + _format_links(result.internal_links, limit=20),
    ]
    for page in result.pages[:8]:
        parts.append(f"Subpage SEO: {page.url}\nTitle: {page.title}\nHeadings:\n{_format_headings(page.headings)}")
    return _truncate("\n\n".join(parts), max_chars)


def format_social_context(result: ScrapeResult) -> str:
    return "\n".join([
        "Verified social links discovered from site HTML:",
        _format_social_links(result.social_links),
        "Review/social-looking external links:",
        _format_links([link for link in result.external_links if _looks_social_or_review(link.href)], limit=20),
        f"Emails found: {', '.join(result.emails) or 'None found'}",
    ])


def format_competitor_context(result: ScrapeResult) -> str:
    return "\n".join([
        "Observed external links from crawled site. These are candidates/evidence, not automatically competitors:",
        _format_links(result.external_links, limit=25),
    ])


def _looks_social_or_review(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return any(token in host for token in ("facebook", "instagram", "linkedin", "twitter", "x.com", "yelp", "google", "trustpilot"))
