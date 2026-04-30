"""Web scraper — extracts clean text from URLs, with Playwright fallback for JS-heavy sites."""
from __future__ import annotations

import logging
import time
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from core.settings import load_config
from scraper.extractors import (
    extract_contact_info,
    extract_headings,
    extract_json_ld,
    extract_links,
    extract_meta,
    extract_social_links,
)
from scraper.models import ScrapeResult

logger = logging.getLogger(__name__)

MAX_LENGTH = 50_000  # chars
# Tags to strip entirely (scripts, styles, metadata headers)
NOISE_TAGS = ["script", "style", "noscript"]
# Tags to unwrap (keep their text content, but remove the tag itself)
# Navigation often contains valuable links like Blog, Services, etc.
UNWRAP_TAGS = ["nav", "header", "footer", "aside"]

# Lazy Playwright detection — only check once at module load
_playwright_available: bool | None = None
_config: dict | None = None


class ScrapeCache:
    """Simple in-memory cache for scrape results, scoped to a single analysis run.

    Prevents re-scraping the same URL across multiple research modules within
    one run_all() call. Thread-safe for use with ThreadPoolExecutor.
    """

    def __init__(self) -> None:
        self._text_cache: dict[str, str] = {}
        self._structured_cache: dict[str, ScrapeResult] = {}

    def get_text(self, url: str, timeout: int = 15) -> str:
        """Scrape and cache raw text for a URL. Returns cached result on subsequent calls."""
        normalized = normalize_url(url) if url else url
        if normalized in self._text_cache:
            logger.debug("ScrapeCache hit (text) for %s", normalized)
            return self._text_cache[normalized]
        result = scrape(normalized or url, timeout=timeout)
        self._text_cache[normalized] = result
        return result

    def get_structured(self, url: str, timeout: int = 15) -> ScrapeResult:
        """Scrape and cache structured data for a URL. Returns cached result on subsequent calls."""
        normalized = normalize_url(url) if url else url
        if normalized in self._structured_cache:
            logger.debug("ScrapeCache hit (structured) for %s", normalized)
            return self._structured_cache[normalized]
        result = scrape_structured(normalized or url, timeout=timeout)
        self._structured_cache[normalized] = result
        return result


def _get_config() -> dict:
    """Load scraper config lazily (cached after first call)."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def _check_playwright() -> bool:
    """Check whether playwright.sync_api is importable."""
    global _playwright_available
    if _playwright_available is not None:
        return _playwright_available
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        _playwright_available = True
    except ImportError:
        _playwright_available = False
    return _playwright_available


def should_use_playwright() -> bool:
    """Return True if Playwright fallback is enabled in config AND Playwright is installed."""
    cfg = _get_config()
    scraper_cfg = cfg.get("scraper", {})
    enabled = scraper_cfg.get("use_playwright_fallback", False)
    if not enabled:
        return False
    return _check_playwright()


def normalize_url(url: str) -> str:
    """Return a URL with an HTTP scheme, defaulting bare domains to HTTPS."""
    cleaned = url.strip()
    if not cleaned:
        return cleaned
    if urlparse(cleaned).scheme:
        return cleaned
    return f"https://{cleaned}"


def _clean_html(html: str) -> str:
    """Parse HTML, remove noise tags, unwrap structural tags, and return clean text."""
    soup = BeautifulSoup(html, "html.parser")
    # Remove noise tags entirely (script, style, noscript)
    for tag in soup.find_all(NOISE_TAGS):
        tag.decompose()
    # Unwrap structural tags (nav, header, footer, aside) — keep their text content
    for tag in soup.find_all(UNWRAP_TAGS):
        tag.unwrap()
    text = soup.get_text(separator="\n", strip=True)
    lines = [line for line in text.splitlines() if line.strip()]
    return "\n".join(lines)[:MAX_LENGTH]


def scrape(url: str, timeout: int = 15) -> str:
    """
    Fetch and extract clean text from a URL.

    Uses requests + BeautifulSoup first. If Playwright fallback is enabled
    and the result is empty or very sparse, retries with a headless browser.

    Falls back to empty string if everything fails.

    Args:
        url: The target URL.
        timeout: Request timeout in seconds.

    Returns:
        Cleaned text content from the page.
    """
    normalized = normalize_url(url) if url else url

    # Primary: requests + BeautifulSoup
    text = _scrape_with_requests(normalized, timeout)

    # If we got useful content, return it
    if text and len(text.strip()) >= 200:
        return text

    # Fallback: try Playwright if enabled and available
    if should_use_playwright():
        logger.info("Requests returned sparse content for %s, trying Playwright fallback", normalized)
        pw_text = scrape_with_playwright(normalized)
        if pw_text and len(pw_text.strip()) > len(text.strip()):
            return pw_text

    # Return whatever we have (even if empty)
    return text


def _scrape_with_requests(url: str, timeout: int = 15) -> str:
    """Scrape using requests + BeautifulSoup."""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (compatible; ReconIQ/1.0; "
                "+https://github.com/nwfreshness)"
            ),
            "Accept": "text/html,application/xhtml+xml",
        }
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        response.raise_for_status()

        # Detect encoding from headers or content
        response.encoding = response.apparent_encoding or "utf-8"

        return _clean_html(response.text)

    except Exception:
        return ""


def scrape_with_playwright(url: str, timeout: int = 25) -> str:
    """
    Scrape a URL using Playwright headless browser for JS-rendered content.

    Returns empty string if Playwright is not installed or any error occurs.
    """
    if not _check_playwright():
        logger.warning("Playwright not available, skipping JS rendering for %s", url)
        return ""

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.set_default_timeout(timeout * 1000)
                # Use domcontentloaded instead of networkidle — many sites
                # have persistent connections that prevent networkidle from firing.
                page.goto(url, wait_until="domcontentloaded")
                # Wait for JS rendering to settle
                page.wait_for_timeout(3000)
                html = page.content()
            finally:
                browser.close()

        return _clean_html(html)

    except Exception as exc:
        logger.warning("Playwright scrape failed for %s: %s", url, exc)
        return ""


def extract_domain_name(url: str) -> str:
    """Extract a readable domain name for fallback LLM inference."""
    parsed = urlparse(normalize_url(url))
    domain = parsed.netloc or parsed.path
    return domain.replace("www.", "").split(":")[0]


def scrape_structured(url: str, timeout: int = 15) -> ScrapeResult:
    """
    Fetch and extract structured data from a URL.

    Like scrape(), but returns a ScrapeResult with typed fields instead of
    raw text. This gives research modules real scraped data (social links,
    headings, contact info, JSON-LD) instead of requiring the LLM to infer
    everything from a flat text dump.

    Uses requests first; falls back to Playwright if enabled and the result
    is sparse. Extracts structured metadata before flattening to body_text.
    """
    start = time.monotonic()
    normalized = normalize_url(url) if url else url

    # Fetch HTML (requests first, Playwright fallback)
    html = _fetch_html(normalized, timeout)

    if not html:
        return ScrapeResult(
            url=normalized or url,
            title=extract_domain_name(url) if url else "",
            body_text="",
            raw_html_length=0,
            crawl_duration_s=time.monotonic() - start,
        )

    soup = BeautifulSoup(html, "html.parser")

    # Extract structured metadata from the full HTML (before stripping tags)
    meta = extract_meta(soup)
    internal_links, external_links = extract_links(soup, normalized or url)
    social_links = extract_social_links(soup)
    phone_numbers, emails = extract_contact_info(soup)
    json_ld_data = extract_json_ld(soup)
    headings = extract_headings(soup)

    # Now strip noise tags and get clean body text (same as _clean_html)
    body_text = _clean_html(html)

    result = ScrapeResult(
        url=normalized or url,
        title=meta["title"],
        meta_description=meta["meta_description"],
        meta_keywords=meta["meta_keywords"],
        og_tags=meta["og_tags"],
        headings=headings,
        internal_links=internal_links,
        external_links=external_links,
        social_links=social_links,
        phone_numbers=phone_numbers,
        emails=emails,
        json_ld=json_ld_data,
        body_text=body_text,
        raw_html_length=len(html),
        crawl_duration_s=time.monotonic() - start,
    )

    # If body_text is sparse and Playwright is available, retry with Playwright
    if len(body_text.strip()) < 200 and should_use_playwright():
        logger.info("Structured scrape returned sparse content for %s, trying Playwright fallback", normalized)
        pw_html = scrape_with_playwright(normalized, timeout=25)
        if pw_html and len(_clean_html(pw_html).strip()) > len(body_text.strip()):
            pw_soup = BeautifulSoup(pw_html, "html.parser")
            pw_meta = extract_meta(pw_soup)
            pw_internal, pw_external = extract_links(pw_soup, normalized or url)
            pw_social = extract_social_links(pw_soup)
            pw_phones, pw_emails = extract_contact_info(pw_soup)
            pw_json_ld = extract_json_ld(pw_soup)
            pw_headings = extract_headings(pw_soup)

            result = ScrapeResult(
                url=normalized or url,
                title=pw_meta["title"] or result.title,
                meta_description=pw_meta["meta_description"] or result.meta_description,
                meta_keywords=pw_meta["meta_keywords"] or result.meta_keywords,
                og_tags=pw_meta["og_tags"] or result.og_tags,
                headings=pw_headings or result.headings,
                internal_links=pw_internal or result.internal_links,
                external_links=pw_external or result.external_links,
                social_links=pw_social or result.social_links,
                phone_numbers=pw_phones or result.phone_numbers,
                emails=pw_emails or result.emails,
                json_ld=pw_json_ld or result.json_ld,
                body_text=_clean_html(pw_html),
                raw_html_length=len(pw_html),
                crawl_duration_s=time.monotonic() - start,
            )

    return result


def _fetch_html(url: str, timeout: int = 15) -> str:
    """Fetch raw HTML using requests. Returns empty string on failure."""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (compatible; ReconIQ/1.0; "
                "+https://github.com/nwfreshness)"
            ),
            "Accept": "text/html,application/xhtml+xml",
        }
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or "utf-8"
        return response.text
    except Exception:
        return ""