"""Structured extractors — pull typed metadata from HTML before flattening to text.

Phase 9J-1: These functions parse BeautifulSoup objects into the dataclasses
defined in scraper/models.py, giving research modules real scraped data instead
of requiring the LLM to infer everything from raw text.
"""
from __future__ import annotations

import json
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from scraper.models import LinkData, SocialLink


# ── Social platform detection ────────────────────────────────────────────────

_SOCIAL_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("facebook", re.compile(r"https?://(www\.)?facebook\.com/", re.I)),
    ("instagram", re.compile(r"https?://(www\.)?instagram\.com/", re.I)),
    ("x", re.compile(r"https?://(www\.)?x\.com/", re.I)),
    ("twitter", re.compile(r"https?://(www\.)?twitter\.com/", re.I)),
    ("linkedin", re.compile(r"https?://(www\.)?linkedin\.com/", re.I)),
    ("yelp", re.compile(r"https?://(www\.)?yelp\.com/", re.I)),
    ("google_maps", re.compile(r"https?://(www\.)?google\.com/maps", re.I)),
    ("youtube", re.compile(r"https?://(www\.)?youtube\.com/", re.I)),
    ("tiktok", re.compile(r"https?://(www\.)?tiktok\.com/", re.I)),
    ("nextdoor", re.compile(r"https?://(www\.)?nextdoor\.com/", re.I)),
    ("pinterest", re.compile(r"https?://(www\.)?pinterest\.com/", re.I)),
    ("threads", re.compile(r"https?://(www\.)?threads\.net/", re.I)),
    ("reddit", re.compile(r"https?://(www\.)?reddit\.com/", re.I)),
    ("angies_list", re.compile(r"https?://(www\.)?angieslist\.com/", re.I)),
    ("houzz", re.compile(r"https?://(www\.)?houzz\.com/", re.I)),
    ("gmb", re.compile(r"https?://(www\.)?google\.com/maps/place", re.I)),
    ("bbb", re.compile(r"https?://(www\.)?bbb\.org/", re.I)),
]

# Phone number patterns (US-centric, covers most formats)
_PHONE_PATTERNS = [
    re.compile(r"\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}"),        # (555) 123-4567, 555-123-4567, 555.123.4567
    re.compile(r"\+1[-.\s]?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}"),  # +1 (555) 123-4567
    re.compile(r"\+1[-.\s]?\d{3}[-.\s]\d{3}[-.\s]\d{4}"),        # +1-555-123-4567
]

_EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")


# ── extract_meta ──────────────────────────────────────────────────────────────


def extract_meta(soup: BeautifulSoup) -> dict:
    """Extract page title, meta description, keywords, and Open Graph tags."""
    result = {
        "title": "",
        "meta_description": "",
        "meta_keywords": [],
        "og_tags": {},
    }

    # Title: prefer <title>, fall back to first <h1>
    title_tag = soup.find("title")
    if title_tag and title_tag.string:
        result["title"] = title_tag.string.strip()
    else:
        h1 = soup.find("h1")
        if h1:
            result["title"] = h1.get_text(strip=True)

    # Meta description
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        result["meta_description"] = meta_desc["content"].strip()

    # Meta keywords
    meta_kw = soup.find("meta", attrs={"name": "keywords"})
    if meta_kw and meta_kw.get("content"):
        result["meta_keywords"] = [
            kw.strip()
            for kw in meta_kw["content"].split(",")
            if kw.strip()
        ]

    # Open Graph tags
    for tag in soup.find_all("meta", attrs={"property": True}):
        prop = tag.get("property", "")
        content = tag.get("content", "")
        if prop.startswith("og:") and content:
            result["og_tags"][prop] = content.strip()

    return result


# ── extract_links ────────────────────────────────────────────────────────────


def extract_links(soup: BeautifulSoup, base_url: str) -> tuple[list[LinkData], list[LinkData]]:
    """Separate all <a> tags into internal and external links.

    Internal links point to the same domain (including relative paths).
    External links point to different domains.
    Anchor-only links (#) and javascript: links are excluded.
    """
    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc.lower().lstrip("www.")

    internal: list[LinkData] = []
    external: list[LinkData] = []
    seen: set[str] = set()

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()
        text = a_tag.get_text(strip=True)

        # Skip anchor-only and javascript links
        if not href or href.startswith("#") or href.startswith("javascript:"):
            continue

        # Skip duplicate URLs
        if href in seen:
            continue
        seen.add(href)

        # Determine if internal or external
        parsed = urlparse(href)
        if parsed.scheme in ("", "http", "https"):
            link_domain = parsed.netloc.lower().lstrip("www.") if parsed.netloc else ""
            if not parsed.netloc:
                # Relative URL — always internal
                internal.append(LinkData(href=href, text=text))
            elif link_domain == base_domain:
                # Same domain
                internal.append(LinkData(href=href, text=text))
            else:
                # Different domain
                external.append(LinkData(href=href, text=text))

    return internal, external


# ── extract_social_links ──────────────────────────────────────────────────────


def extract_social_links(soup: BeautifulSoup) -> list[SocialLink]:
    """Extract social media links from all <a> tags on the page.

    Deduplicates by URL so footer/header repeats don't create duplicates.
    """
    seen_urls: set[str] = set()
    links: list[SocialLink] = []

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()
        if not href:
            continue

        for platform, pattern in _SOCIAL_PATTERNS:
            if pattern.search(href):
                # Deduplicate by URL
                normalized = href.rstrip("/")
                if normalized in seen_urls:
                    break
                seen_urls.add(normalized)
                # For twitter vs x, prefer the detected platform
                links.append(SocialLink(platform=platform, url=href))
                break

    return links


# ── extract_contact_info ──────────────────────────────────────────────────────


def extract_contact_info(soup: BeautifulSoup) -> tuple[list[str], list[str]]:
    """Extract phone numbers and email addresses from page text and mailto:/tel: links.

    Returns (phones, emails) with duplicates removed.
    """
    text = soup.get_text(separator=" ")

    # Emails from mailto: links and body text
    emails: list[str] = []
    seen_emails: set[str] = set()

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if href.startswith("mailto:"):
            email = href[7:].split("?")[0].strip()
            if email and email not in seen_emails:
                seen_emails.add(email)
                emails.append(email)

    # Also find emails in plain text
    for match in _EMAIL_PATTERN.finditer(text):
        email = match.group(0)
        if email not in seen_emails:
            seen_emails.add(email)
            emails.append(email)

    # Phone numbers from tel: links and body text
    phones: list[str] = []
    seen_phones: set[str] = set()

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if href.startswith("tel:"):
            phone = href[4:].strip()
            if phone and phone not in seen_phones:
                seen_phones.add(phone)
                phones.append(phone)

    # Also find phone numbers in plain text
    for pattern in _PHONE_PATTERNS:
        for match in pattern.finditer(text):
            phone = match.group(0).strip()
            if phone and phone not in seen_phones:
                seen_phones.add(phone)
                phones.append(phone)

    return phones, emails


# ── extract_json_ld ────────────────────────────────────────────────────────────


def extract_json_ld(soup: BeautifulSoup) -> list[dict]:
    """Extract all JSON-LD structured data blocks from <script type="application/ld+json">.

    Returns a list of parsed JSON objects. Invalid JSON blocks are silently skipped.
    """
    results: list[dict] = []

    for script_tag in soup.find_all("script", type="application/ld+json"):
        content = script_tag.string
        if not content:
            continue
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                results.append(data)
            elif isinstance(data, list):
                results.extend(item for item in data if isinstance(item, dict))
        except (json.JSONDecodeError, ValueError):
            # Silently skip invalid JSON-LD blocks
            continue

    return results


# ── extract_headings ──────────────────────────────────────────────────────────


def extract_headings(soup: BeautifulSoup) -> dict[str, list[str]]:
    """Extract h1, h2, and h3 heading text from the page.

    Returns dict like {"h1": ["Title"], "h2": ["Section 1", "Section 2"]}.
    """
    headings: dict[str, list[str]] = {}

    for level in ("h1", "h2", "h3"):
        texts = []
        for tag in soup.find_all(level):
            text = tag.get_text(strip=True)
            if text:
                texts.append(text)
        if texts:
            headings[level] = texts

    return headings