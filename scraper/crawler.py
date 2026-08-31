"""Multi-page site crawler — Phase 9J-2.

Crawls a target URL and its discovered subpages, returning a single ScrapeResult
that aggregates structured metadata from all pages. Uses requests (not Playwright)
for subpages to keep crawling fast.
"""
from __future__ import annotations

import logging
import time
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

from bs4 import BeautifulSoup

from scraper.extractors import (
    extract_contact_info,
    extract_headings,
    extract_json_ld,
    extract_links,
    extract_meta,
    extract_social_links,
    _phone_key,
)
from scraper.models import LinkData, PageData, ScrapeResult, SocialLink
from scraper.scraper import _clean_html, _fetch_html, fetch_html_with_playwright, normalize_url, should_use_playwright

logger = logging.getLogger(__name__)

# Common high-value subpage paths to probe if the homepage doesn't yield enough links
_SEED_PATHS = ("/about", "/services", "/contact", "/blog")


class _SubpageResult:
    """Internal container for data extracted from a single subpage."""
    __slots__ = ("page_data", "emails", "phones", "social_links", "internal_links", "html")

    def __init__(
        self,
        page_data: PageData,
        emails: list[str],
        phones: list[str],
        social_links: list[SocialLink],
        internal_links: list[LinkData],
        html: str,
    ):
        self.page_data = page_data
        self.emails = emails
        self.phones = phones
        self.social_links = social_links
        self.internal_links = internal_links
        self.html = html


# ── robots.txt ────────────────────────────────────────────────────────────────


def fetch_robots_txt(base_url: str, timeout: int = 5) -> RobotFileParser | None:
    """Fetch and parse robots.txt for the given base URL.

    Returns None if robots.txt is unreachable or unparseable, so the crawler
    falls back to permissive crawling.
    """
    parsed = urlparse(base_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    # Explicitly check that robots.txt is reachable before handing to
    # RobotFileParser, which silently treats 404 as an empty allow-all.
    try:
        import requests
        resp = requests.get(robots_url, headers={"User-Agent": "ReconIQ/1.0"}, timeout=timeout)
        resp.raise_for_status()
    except Exception:
        logger.debug("Could not fetch robots.txt from %s", robots_url)
        return None

    parser = RobotFileParser()
    parser.set_url(robots_url)
    try:
        parser.parse(resp.text.splitlines())
        return parser
    except Exception:
        logger.debug("Could not parse robots.txt from %s", robots_url)
        return None


def is_allowed_by_robots(parser: RobotFileParser | None, url: str, user_agent: str = "*") -> bool:
    """Return True if the URL is allowed by robots.txt.

    Always returns True if parser is None (robots.txt not available).
    """
    if parser is None:
        return True
    return bool(parser.can_fetch(user_agent, url))


# ── sitemap.xml ──────────────────────────────────────────────────────────────


def _locs_from_sitemap_xml(xml_text: str) -> list[str]:
    soup = BeautifulSoup(xml_text, "xml")
    urls: list[str] = []
    for loc_tag in soup.find_all("loc"):
        href = loc_tag.get_text(strip=True)
        if href.startswith(("http://", "https://")):
            urls.append(href)
    return urls


def _is_sitemap_loc(url: str) -> bool:
    path = urlparse(url).path.lower()
    return path.endswith(".xml") or "sitemap" in path


def fetch_sitemap_urls(base_url: str, timeout: int = 5) -> list[str]:
    """Try to fetch /sitemap.xml and extract page URLs from it.

    Follows up to 3 nested sitemap index files. Returns only crawlable page URLs.
    """
    parsed = urlparse(base_url)
    sitemap_url = f"{parsed.scheme}://{parsed.netloc}/sitemap.xml"

    try:
        import requests
        resp = requests.get(sitemap_url, headers={"User-Agent": "ReconIQ/1.0"}, timeout=timeout)
        resp.raise_for_status()
    except Exception:
        logger.debug("Could not fetch sitemap from %s", sitemap_url)
        return []

    raw_locs = _locs_from_sitemap_xml(resp.text)
    nested_fetched = 0
    expanded: list[str] = []
    for href in raw_locs:
        if _is_sitemap_loc(href) and nested_fetched < 3:
            nested_fetched += 1
            try:
                import requests
                child = requests.get(href, headers={"User-Agent": "ReconIQ/1.0"}, timeout=timeout)
                child.raise_for_status()
                expanded.extend(_locs_from_sitemap_xml(child.text))
            except Exception:
                logger.debug("Could not fetch nested sitemap from %s", href)
            continue
        expanded.append(href)

    return [u for u in expanded if _is_crawlable_page_url(u)]


# ── URL normalization and deduplication ──────────────────────────────────────


def _normalize_url_for_dedup(url: str) -> str:
    """Normalize a URL for deduplication: strip fragment, trailing slash, lowercase."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    return f"{parsed.scheme}://{parsed.netloc.lower()}{path}"


def _is_same_domain(url: str, base_url: str) -> bool:
    """Check whether *url* belongs to the same domain as *base_url*."""
    url_domain = urlparse(url).netloc.lower().lstrip("www.")
    base_domain = urlparse(base_url).netloc.lower().lstrip("www.")
    return url_domain == base_domain


_SKIP_SUFFIXES = (
    ".xml", ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg",
    ".css", ".js", ".json", ".zip", ".mp4", ".mp3", ".ico",
)


def _is_crawlable_page_url(url: str) -> bool:
    """Return False for assets, sitemaps, and non-http URLs that must not occupy crawl slots."""
    if not url or url.startswith(("javascript:", "mailto:", "tel:")):
        return False
    parsed = urlparse(url)
    if parsed.scheme and not parsed.scheme.startswith("http"):
        return False
    path = parsed.path.lower().rstrip("/")
    if not path:
        # Fragment-only (https://example.com/#) is not a page.
        if "#" in url:
            return False
        return True
    if any(path.endswith(suf) for suf in _SKIP_SUFFIXES):
        return False
    if "sitemap" in path and path.endswith(".xml"):
        return False
    return True


_HOMEPAGE_PATHS = {"", "/", "/home", "/index", "/index.html", "/index.htm"}


def _is_homepage_url(url: str, base_url: str) -> bool:
    """True when *url* is the same document as the site homepage."""
    if not _is_same_domain(url, base_url):
        return False
    path = urlparse(url).path.lower().rstrip("/") or "/"
    if path == "/":
        return True
    return path in _HOMEPAGE_PATHS or path.lstrip("/") in {
        "home",
        "index",
        "index.html",
        "index.htm",
    }


_IMPORTANT_PATHS = (
    "/about", "/our-story", "/story", "/services", "/service",
    "/flavors", "/menu", "/pricing", "/contact", "/locations",
    "/hours", "/faq", "/reviews", "/testimonials",
)


def _score_path(url_or_path: str) -> int:
    """Lower score = crawl sooner."""
    path = urlparse(url_or_path).path.lower().rstrip("/") or "/"
    for i, pattern in enumerate(_IMPORTANT_PATHS):
        if path == pattern or path.startswith(pattern + "/"):
            return i
    if "/blog" in path or "/news" in path:
        return 80
    if any(tok in path for tok in ("career", "job", "team", "privacy", "terms", "cart", "login")):
        return 90
    return 50


# ── Seed URL discovery ───────────────────────────────────────────────────────


def _discover_seed_urls(
    soup: BeautifulSoup,
    base_url: str,
    robots_parser: RobotFileParser | None,
    sitemap_urls: list[str],
) -> list[str]:
    """Build a prioritized list of subpage URLs to crawl.

    Sources (in priority order):
    1. Links in <nav> and <footer> elements
    2. Internal links discovered by extract_links()
    3. URLs from /sitemap.xml (if available)
    4. Common probe paths (/about, /services, /contact, /blog)
    """
    seen: set[str] = set()
    urls: list[str] = []

    def _add(url: str) -> None:
        abs_url = urljoin(base_url, url)
        if not _is_crawlable_page_url(abs_url):
            return
        norm = _normalize_url_for_dedup(abs_url)
        if norm in seen:
            return
        if not _is_same_domain(abs_url, base_url):
            return
        if not is_allowed_by_robots(robots_parser, abs_url):
            logger.debug("Skipping %s (disallowed by robots.txt)", abs_url)
            return
        # Skip the homepage itself — we already scraped it
        if _is_homepage_url(abs_url, base_url):
            return
        seen.add(norm)
        urls.append(abs_url)

    # 1. Links in <nav> and <footer>
    for container_tag in soup.find_all(["nav", "footer"]):
        for a_tag in container_tag.find_all("a", href=True):
            _add(a_tag["href"])

    # 2. All internal links from the page
    internal_links, _ = extract_links(soup, base_url)
    for link in internal_links:
        _add(link.href)

    # 3. Sitemap URLs
    for sitemap_url in sitemap_urls:
        _add(sitemap_url)

    # 4. Common probe paths — only when the page didn't yield enough internal URLs
    if len(urls) < 4:
        base = urlparse(base_url)
        origin = f"{base.scheme}://{base.netloc}"
        for path in _SEED_PATHS:
            probe_url = f"{origin}{path}"
            _add(probe_url)

    urls.sort(key=_score_path)
    return urls


# ── Subpage scraping ─────────────────────────────────────────────────────────


def _scrape_subpage(url: str, base_url: str, timeout: int = 10) -> _SubpageResult | None:
    """Fetch and extract all structured data from a single subpage.

    Uses requests only (no Playwright) for speed. Returns None on failure.
    Returns a _SubpageResult with page data plus supplementary metadata
    for merging into the top-level ScrapeResult.
    """
    html = _fetch_html(url, timeout)
    if not html:
        logger.debug("Subpage fetch failed: %s", url)
        return None

    soup = BeautifulSoup(html, "html.parser")
    meta = extract_meta(soup)
    headings = extract_headings(soup)
    phones, emails = extract_contact_info(soup)
    social_links = extract_social_links(soup)
    internal_links, _ = extract_links(soup, base_url)
    text = _clean_html(html)

    page_data = PageData(
        url=url,
        title=meta["title"],
        text=text,
        headings=headings,
    )

    return _SubpageResult(
        page_data=page_data,
        emails=emails,
        phones=phones,
        social_links=social_links,
        internal_links=internal_links,
        html=html,
    )


# ── Main entry point ──────────────────────────────────────────────────────────


def crawl_site(
    url: str,
    max_pages: int = 5,
    max_depth: int = 2,
    timeout: int = 15,
    progress_callback=None,
) -> ScrapeResult:
    """Crawl a website and return a ScrapeResult with data from multiple pages.

    Args:
        url: Target website URL to crawl.
        max_pages: Maximum number of subpages to crawl (excluding the homepage).
                   Default 5.
        max_depth: Maximum crawl depth from the homepage. Default 2.
                   Depth 1 = direct links from homepage.
                   Depth 2 = links found on depth-1 pages.
        timeout: Request timeout in seconds per page. Default 15.
        progress_callback: Optional callable(message: str, percent: float) for
                           progress updates.

    Returns:
        A ScrapeResult with the homepage's structured data plus PageData
        for each successfully crawled subpage.
    """
    start = time.monotonic()
    normalized = normalize_url(url) if url else url

    def log(msg: str, pct: float) -> None:
        if progress_callback:
            progress_callback(msg, pct)

    log(f"Crawling {normalized}...", 5.0)

    # ── Parse homepage ────────────────────────────────────────────────────
    homepage_html = _fetch_html(normalized, timeout)
    body_preview = _clean_html(homepage_html) if homepage_html else ""
    if (not homepage_html or len(body_preview.strip()) < 200) and should_use_playwright():
        pw_html = fetch_html_with_playwright(normalized, timeout=25)
        if pw_html and len(_clean_html(pw_html).strip()) > len(body_preview.strip()):
            homepage_html = pw_html
    if not homepage_html:
        return ScrapeResult(
            url=normalized or url,
            title="",
            body_text="",
            raw_html_length=0,
            crawl_duration_s=time.monotonic() - start,
        )

    homepage_soup = BeautifulSoup(homepage_html, "html.parser")
    meta = extract_meta(homepage_soup)
    internal_links, external_links = extract_links(homepage_soup, normalized or url)
    social_links = extract_social_links(homepage_soup)
    phone_numbers, emails = extract_contact_info(homepage_soup)
    json_ld_data = extract_json_ld(homepage_soup)
    headings = extract_headings(homepage_soup)
    body_text = _clean_html(homepage_html)

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
        raw_html_length=len(homepage_html),
        crawl_duration_s=time.monotonic() - start,  # updated at end
    )

    log("Homepage scraped", 20.0)

    # ── Discover seed URLs ─────────────────────────────────────────────────
    robots_parser = fetch_robots_txt(normalized or url)
    sitemap_urls = fetch_sitemap_urls(normalized or url)
    seed_urls = _discover_seed_urls(homepage_soup, normalized or url, robots_parser, sitemap_urls)

    if not seed_urls:
        logger.info("No discoverable subpages for %s", normalized)
        result.crawl_duration_s = time.monotonic() - start
        return result

    # ── BFS crawl subpages ────────────────────────────────────────────────
    crawled_pages: list[PageData] = []
    pages_crawled = 0
    max_subpages = max_pages

    visited: set[str] = set()
    visited.add(_normalize_url_for_dedup(normalized or url))
    queue: list[tuple[str, int]] = [(u, 1) for u in seed_urls]
    queue_set: set[str] = {_normalize_url_for_dedup(u) for u, _ in queue}
    max_queue = max_subpages * 10

    while queue and pages_crawled < max_subpages:
        page_url, depth = queue.pop(0)
        norm = _normalize_url_for_dedup(page_url)
        if norm in visited:
            continue
        if depth > max_depth:
            continue
        if not _is_crawlable_page_url(page_url) or _is_homepage_url(page_url, normalized or url):
            continue
        visited.add(norm)

        pct = 20.0 + (pages_crawled / max(1, max_subpages)) * 60.0
        log(f"Crawling subpage ({pages_crawled + 1}/{max_subpages}): {page_url}", pct)

        sub_result = _scrape_subpage(page_url, normalized or url, timeout=10)

        if sub_result is None:
            logger.debug("Skipping failed subpage: %s", page_url)
            continue

        # Polite delay only after a successful fetch
        time.sleep(1.0)

        crawled_pages.append(sub_result.page_data)
        pages_crawled += 1

        # Merge supplementary metadata from subpage into top-level result
        for email in sub_result.emails:
            if email not in result.emails:
                result.emails.append(email)

        seen_phone_keys = {_phone_key(p) for p in result.phone_numbers}
        for phone in sub_result.phones:
            key = _phone_key(phone)
            if key and key not in seen_phone_keys:
                result.phone_numbers.append(phone)
                seen_phone_keys.add(key)

        seen_social_urls = {sl.url.rstrip("/") for sl in result.social_links}
        for sl in sub_result.social_links:
            if sl.url.rstrip("/") not in seen_social_urls:
                result.social_links.append(sl)
                seen_social_urls.add(sl.url.rstrip("/"))

        # Discover more links from this subpage (depth+1)
        if depth < max_depth and pages_crawled < max_subpages:
            sub_soup = BeautifulSoup(sub_result.html, "html.parser")
            sub_internal, _ = extract_links(sub_soup, page_url)
            for link in sub_internal:
                abs_link = urljoin(page_url, link.href)
                link_norm = _normalize_url_for_dedup(abs_link)
                if (
                    link_norm not in visited
                    and link_norm not in queue_set
                    and _is_same_domain(abs_link, normalized or url)
                    and _is_crawlable_page_url(abs_link)
                    and not _is_homepage_url(abs_link, normalized or url)
                    and len(queue) < max_queue
                ):
                    if is_allowed_by_robots(robots_parser, abs_link):
                        queue.append((abs_link, depth + 1))
                        queue_set.add(link_norm)

    result.pages = crawled_pages
    result.crawl_duration_s = time.monotonic() - start
    log(f"Crawled {pages_crawled} subpages", 85.0)

    return result