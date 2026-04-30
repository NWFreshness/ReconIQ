"""Data models for structured scraping results — Phase 9J-1."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SocialLink:
    """A social media link found on a page."""
    platform: str  # e.g. "facebook", "instagram", "linkedin"
    url: str


@dataclass(slots=True)
class LinkData:
    """A hyperlink found on a page."""
    href: str
    text: str


@dataclass(slots=True)
class PageData:
    """Content and metadata from a single crawled page."""
    url: str
    title: str
    text: str
    headings: dict[str, list[str]] = field(default_factory=dict)


@dataclass(slots=True)
class ScrapeResult:
    """Structured result from a site crawl — the centerpiece of Phase 9J-1.

    Replaces the raw text string that `scrape()` returns with typed fields
    so research modules can work from real data instead of LLM inference.
    """
    url: str
    title: str
    meta_description: str = ""
    meta_keywords: list[str] = field(default_factory=list)
    og_tags: dict[str, str] = field(default_factory=dict)
    headings: dict[str, list[str]] = field(default_factory=dict)
    internal_links: list[LinkData] = field(default_factory=list)
    external_links: list[LinkData] = field(default_factory=list)
    social_links: list[SocialLink] = field(default_factory=list)
    phone_numbers: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    json_ld: list[dict] = field(default_factory=list)
    body_text: str = ""
    pages: list[PageData] = field(default_factory=list)
    raw_html_length: int = 0
    crawl_duration_s: float = 0.0