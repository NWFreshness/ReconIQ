"""Web scraper — extracts clean text from URLs, with Playwright fallback for JS-heavy sites."""
from __future__ import annotations

import logging
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from core.settings import load_config

logger = logging.getLogger(__name__)

MAX_LENGTH = 50_000  # chars
NOISE_TAGS = ["script", "style", "nav", "header", "footer", "aside", "noscript"]

# Lazy Playwright detection — only check once at module load
_playwright_available: bool | None = None
_config: dict | None = None


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
    """Parse HTML, remove noise tags, and return clean text."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(NOISE_TAGS):
        tag.decompose()
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


def scrape_with_playwright(url: str, timeout: int = 20) -> str:
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
                page.goto(url, wait_until="networkidle")
                # Wait briefly for any late-loading content
                page.wait_for_timeout(1500)
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