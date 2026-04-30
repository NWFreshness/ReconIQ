"""Tests for scraper/crawler.py — Phase 9J-2: Multi-Page Crawler."""
from __future__ import annotations

import pytest
import responses

from scraper.crawler import (
    _discover_seed_urls,
    _is_same_domain,
    _normalize_url_for_dedup,
    crawl_site,
    fetch_robots_txt,
    fetch_sitemap_urls,
    is_allowed_by_robots,
)
from scraper.models import PageData, ScrapeResult

from bs4 import BeautifulSoup


# ── Fixtures and helpers ──────────────────────────────────────────────────────

HOMEPAGE_HTML = """
<html>
<head>
    <title>Acme Corp</title>
    <meta name="description" content="Acme makes widgets">
</head>
<body>
    <nav>
        <a href="/about">About Us</a>
        <a href="/services">Services</a>
        <a href="/contact">Contact</a>
        <a href="https://facebook.com/acme">Facebook</a>
    </nav>
    <main>
        <h1>Welcome to Acme</h1>
        <p>Call us at (555) 123-4567 or email info@acme.com</p>
    </main>
    <footer>
        <a href="/about">About</a>
        <a href="/privacy">Privacy Policy</a>
    </footer>
</body>
</html>
"""

ABOUT_PAGE_HTML = """
<html>
<head><title>About Acme</title></head>
<body>
    <h1>About Us</h1>
    <p>Acme has been making widgets since 2010.</p>
    <a href="/about/team">Our Team</a>
    <a href="https://instagram.com/acme">Instagram</a>
    <p>Contact: about@acme.com</p>
</body>
</html>
"""

SERVICES_PAGE_HTML = """
<html>
<head><title>Acme Services</title></head>
<body>
    <h1>Our Services</h1>
    <p>We offer widget repair and custom design.</p>
</body>
</html>
"""

SITEMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://acme.com/</loc></url>
  <url><loc>https://acme.com/services</loc></url>
  <url><loc>https://acme.com/about</loc></url>
  <url><loc>https://acme.com/blog</loc></url>
</urlset>
"""

ROBOTS_TXT = """User-agent: *
Allow: /
Disallow: /private/

User-agent: ReconBot
Disallow: /
"""


@pytest.fixture(autouse=True)
def _disable_playwright(monkeypatch):
    """Disable Playwright fallback for all crawler tests."""
    monkeypatch.setattr("scraper.crawler.should_use_playwright", lambda: False)


# ── _normalize_url_for_dedup ──────────────────────────────────────────────────


class TestNormalizeUrlForDedup:
    def test_strips_trailing_slash(self):
        assert _normalize_url_for_dedup("https://acme.com/about/") == "https://acme.com/about"

    def test_strips_fragment(self):
        # urlparse doesn't include fragment in path, but let's verify
        result = _normalize_url_for_dedup("https://acme.com/about#section")
        assert "#section" not in result

    def test_lowercases_domain(self):
        assert _normalize_url_for_dedup("https://Acme.Com/About") == "https://acme.com/About"

    def test_preserves_path(self):
        assert _normalize_url_for_dedup("https://acme.com/services") == "https://acme.com/services"

    def test_root_path(self):
        result = _normalize_url_for_dedup("https://acme.com/")
        assert result == "https://acme.com"


# ── _is_same_domain ───────────────────────────────────────────────────────────


class TestIsSameDomain:
    def test_same_domain(self):
        assert _is_same_domain("https://acme.com/about", "https://acme.com") is True

    def test_www_stripped(self):
        assert _is_same_domain("https://www.acme.com/about", "https://acme.com") is True

    def test_different_domain(self):
        assert _is_same_domain("https://other.com/page", "https://acme.com") is False

    def test_subdomain_different(self):
        assert _is_same_domain("https://blog.acme.com/post", "https://acme.com") is False


# ── is_allowed_by_robots ────────────────────────────────────────────────────


class TestIsAllowedByRobots:
    def test_none_parser_allows_all(self):
        assert is_allowed_by_robots(None, "https://acme.com/anything") is True

    def test_allowed_path(self):
        from urllib.robotparser import RobotFileParser
        parser = RobotFileParser()
        parser.set_url("https://acme.com/robots.txt")
        # Manually set entries for testing without network
        parser.allow_all = True
        assert is_allowed_by_robots(parser, "https://acme.com/about") is True


# ── fetch_robots_txt ─────────────────────────────────────────────────────────


class TestFetchRobotsTxt:
    @responses.activate
    def test_returns_parser_when_robots_txt_exists(self):
        responses.add(
            responses.GET,
            "https://acme.com/robots.txt",
            body=ROBOTS_TXT,
            status=200,
        )
        result = fetch_robots_txt("https://acme.com")
        assert result is not None
        # Basic check: parser was created successfully
        assert hasattr(result, "can_fetch")

    @responses.activate
    def test_returns_none_when_robots_txt_missing(self):
        responses.add(
            responses.GET,
            "https://acme.com/robots.txt",
            status=404,
        )
        result = fetch_robots_txt("https://acme.com")
        assert result is None


# ── fetch_sitemap_urls ───────────────────────────────────────────────────────


class TestFetchSitemapUrls:
    @responses.activate
    def test_extracts_urls_from_sitemap(self):
        responses.add(
            responses.GET,
            "https://acme.com/sitemap.xml",
            body=SITEMAP_XML,
            status=200,
        )
        urls = fetch_sitemap_urls("https://acme.com")
        assert "https://acme.com/" in urls
        assert "https://acme.com/services" in urls
        assert "https://acme.com/about" in urls
        assert "https://acme.com/blog" in urls

    @responses.activate
    def test_returns_empty_on_404(self):
        responses.add(
            responses.GET,
            "https://acme.com/sitemap.xml",
            status=404,
        )
        urls = fetch_sitemap_urls("https://acme.com")
        assert urls == []


# ── _discover_seed_urls ──────────────────────────────────────────────────────


class TestDiscoverSeedUrls:
    def test_discovers_nav_links(self):
        soup = BeautifulSoup(HOMEPAGE_HTML, "html.parser")
        urls = _discover_seed_urls(soup, "https://acme.com", None, [])
        # /about, /services, /contact are in <nav>
        assert any("/about" in u for u in urls)
        assert any("/services" in u for u in urls)
        assert any("/contact" in u for u in urls)

    def test_discovers_footer_links(self):
        soup = BeautifulSoup(HOMEPAGE_HTML, "html.parser")
        urls = _discover_seed_urls(soup, "https://acme.com", None, [])
        assert any("/privacy" in u for u in urls)

    def test_excludes_homepage_url(self):
        soup = BeautifulSoup(HOMEPAGE_HTML, "html.parser")
        urls = _discover_seed_urls(soup, "https://acme.com", None, [])
        # Should not include the homepage itself
        assert _normalize_url_for_dedup("https://acme.com") not in {
            _normalize_url_for_dedup(u) for u in urls
        }

    def test_excludes_external_links(self):
        soup = BeautifulSoup(HOMEPAGE_HTML, "html.parser")
        urls = _discover_seed_urls(soup, "https://acme.com", None, [])
        for u in urls:
            assert "facebook.com" not in u

    def test_includes_sitemap_urls(self):
        soup = BeautifulSoup("<html><body></body></html>", "html.parser")
        sitemap_urls = ["https://acme.com/blog/post-1", "https://acme.com/blog/post-2"]
        urls = _discover_seed_urls(soup, "https://acme.com", None, sitemap_urls)
        assert any("post-1" in u for u in urls)

    def test_includes_seed_paths_as_fallback(self):
        # Page with no links and no sitemap should still get /about, /services, etc.
        soup = BeautifulSoup("<html><body></body></html>", "html.parser")
        urls = _discover_seed_urls(soup, "https://acme.com", None, [])
        assert any("/about" in u for u in urls)
        assert any("/services" in u for u in urls)
        assert any("/contact" in u for u in urls)
        assert any("/blog" in u for u in urls)

    def test_deduplicates_urls(self):
        # Two nav links pointing to the same URL
        html = '<html><body><nav><a href="/about">About</a><a href="/about">About Again</a></nav></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        urls = _discover_seed_urls(soup, "https://acme.com", None, [])
        about_count = sum(1 for u in urls if "/about" in u and "acme.com" in u)
        assert about_count == 1


# ── crawl_site ───────────────────────────────────────────────────────────────


class TestCrawlSite:
    @responses.activate
    def test_crawl_single_page_returns_homepage_data(self):
        """When no subpages are reachable, returns just homepage data."""
        responses.add(responses.GET, "https://acme.com", body=HOMEPAGE_HTML, status=200)
        responses.add(responses.GET, "https://acme.com/robots.txt", status=404)
        responses.add(responses.GET, "https://acme.com/sitemap.xml", status=404)
        # Seed paths will 404
        for path in ("/about", "/services", "/contact", "/blog"):
            responses.add(responses.GET, f"https://acme.com{path}", status=404)

        # Speed up tests by disabling sleep
        import scraper.crawler as crawler_mod
        original_sleep = crawler_mod.time.sleep
        crawler_mod.time.sleep = lambda s: None

        try:
            result = crawl_site("https://acme.com", max_pages=3, max_depth=1)
        finally:
            crawler_mod.time.sleep = original_sleep

        assert isinstance(result, ScrapeResult)
        assert result.url == "https://acme.com"
        assert result.title == "Acme Corp"
        assert "Acme makes widgets" in result.meta_description
        assert len(result.pages) == 0  # All subpages 404'd
        assert "(555) 123-4567" in result.phone_numbers
        assert "info@acme.com" in result.emails

    @responses.activate
    def test_crawl_discovers_and_crawls_subpages(self):
        """Crawls reachable subpages and merges their data."""
        responses.add(responses.GET, "https://acme.com", body=HOMEPAGE_HTML, status=200)
        responses.add(responses.GET, "https://acme.com/robots.txt", status=404)
        responses.add(responses.GET, "https://acme.com/sitemap.xml", status=404)
        responses.add(responses.GET, "https://acme.com/about", body=ABOUT_PAGE_HTML, status=200)
        responses.add(responses.GET, "https://acme.com/services", body=SERVICES_PAGE_HTML, status=200)
        # Some seed paths will fail
        responses.add(responses.GET, "https://acme.com/contact", status=404)
        responses.add(responses.GET, "https://acme.com/blog", status=404)
        # /about/team link discovered from /about page
        responses.add(responses.GET, "https://acme.com/about/team", status=404)
        # /privacy link from footer
        responses.add(responses.GET, "https://acme.com/privacy", status=404)

        import scraper.crawler as crawler_mod
        original_sleep = crawler_mod.time.sleep
        crawler_mod.time.sleep = lambda s: None

        try:
            result = crawl_site("https://acme.com", max_pages=3, max_depth=2)
        finally:
            crawler_mod.time.sleep = original_sleep

        assert isinstance(result, ScrapeResult)
        assert result.title == "Acme Corp"
        # Should have crawled at least the /about and /services pages
        assert len(result.pages) >= 1
        page_urls = [p.url for p in result.pages]
        assert "https://acme.com/about" in page_urls

    @responses.activate
    def test_crawl_merges_emails_from_subpages(self):
        """Emails found on subpages are merged into the top-level result."""
        responses.add(responses.GET, "https://acme.com", body=HOMEPAGE_HTML, status=200)
        responses.add(responses.GET, "https://acme.com/robots.txt", status=404)
        responses.add(responses.GET, "https://acme.com/sitemap.xml", status=404)
        responses.add(responses.GET, "https://acme.com/about", body=ABOUT_PAGE_HTML, status=200)
        # Other seed URLs will fail
        for path in ("/services", "/contact", "/blog", "/privacy"):
            responses.add(responses.GET, f"https://acme.com{path}", status=404)

        import scraper.crawler as crawler_mod
        original_sleep = crawler_mod.time.sleep
        crawler_mod.time.sleep = lambda s: None

        try:
            result = crawl_site("https://acme.com", max_pages=5, max_depth=1)
        finally:
            crawler_mod.time.sleep = original_sleep

        # Homepage has info@acme.com, about page has about@acme.com
        assert "info@acme.com" in result.emails
        assert "about@acme.com" in result.emails

    @responses.activate
    def test_crawl_merges_social_links_from_subpages(self):
        """Social links found on subpages are merged into the top-level result."""
        responses.add(responses.GET, "https://acme.com", body=HOMEPAGE_HTML, status=200)
        responses.add(responses.GET, "https://acme.com/robots.txt", status=404)
        responses.add(responses.GET, "https://acme.com/sitemap.xml", status=404)
        responses.add(responses.GET, "https://acme.com/about", body=ABOUT_PAGE_HTML, status=200)
        for path in ("/services", "/contact", "/blog", "/privacy"):
            responses.add(responses.GET, f"https://acme.com{path}", status=404)

        import scraper.crawler as crawler_mod
        original_sleep = crawler_mod.time.sleep
        crawler_mod.time.sleep = lambda s: None

        try:
            result = crawl_site("https://acme.com", max_pages=5, max_depth=1)
        finally:
            crawler_mod.time.sleep = original_sleep

        # Homepage has facebook, about page has instagram
        social_platforms = [sl.platform for sl in result.social_links]
        assert "facebook" in social_platforms
        assert "instagram" in social_platforms

    @responses.activate
    def test_crawl_respects_max_pages_limit(self):
        """Only max_pages subpages are crawled, even if more are discoverable."""
        responses.add(responses.GET, "https://acme.com", body=HOMEPAGE_HTML, status=200)
        responses.add(responses.GET, "https://acme.com/robots.txt", status=404)
        responses.add(responses.GET, "https://acme.com/sitemap.xml", status=404)
        # Have 4 reachable subpages
        for path in ("/about", "/services", "/contact", "/blog", "/privacy"):
            responses.add(responses.GET, f"https://acme.com{path}", body=SERVICES_PAGE_HTML, status=200)

        import scraper.crawler as crawler_mod
        original_sleep = crawler_mod.time.sleep
        crawler_mod.time.sleep = lambda s: None

        try:
            result = crawl_site("https://acme.com", max_pages=2, max_depth=1)
        finally:
            crawler_mod.time.sleep = original_sleep

        assert len(result.pages) <= 2

    @responses.activate
    def test_crawl_respects_max_depth(self):
        """With max_depth=1, only direct links from homepage are crawled — not links found on subpages."""
        responses.add(responses.GET, "https://acme.com", body=HOMEPAGE_HTML, status=200)
        responses.add(responses.GET, "https://acme.com/robots.txt", status=404)
        responses.add(responses.GET, "https://acme.com/sitemap.xml", status=404)
        responses.add(responses.GET, "https://acme.com/about", body=ABOUT_PAGE_HTML, status=200)
        for path in ("/services", "/contact", "/blog", "/privacy"):
            responses.add(responses.GET, f"https://acme.com{path}", status=404)
        # /about/team should NOT be reached at depth=1
        responses.add(responses.GET, "https://acme.com/about/team", body=SERVICES_PAGE_HTML, status=200)

        import scraper.crawler as crawler_mod
        original_sleep = crawler_mod.time.sleep
        crawler_mod.time.sleep = lambda s: None

        try:
            result = crawl_site("https://acme.com", max_pages=10, max_depth=1)
        finally:
            crawler_mod.time.sleep = original_sleep

        page_urls = [p.url for p in result.pages]
        assert "https://acme.com/about/team" not in page_urls

    @responses.activate
    def test_crawl_empty_homepage_returns_minimal_result(self):
        """When the homepage returns no content, returns an empty ScrapeResult."""
        responses.add(responses.GET, "https://acme.com", status=500)

        result = crawl_site("https://acme.com")

        assert result.url == "https://acme.com"
        assert result.body_text == ""
        assert len(result.pages) == 0
        assert result.raw_html_length == 0

    @responses.activate
    def test_crawl_progress_callback(self):
        """Progress callback receives messages during crawl."""
        responses.add(responses.GET, "https://acme.com", body=HOMEPAGE_HTML, status=200)
        responses.add(responses.GET, "https://acme.com/robots.txt", status=404)
        responses.add(responses.GET, "https://acme.com/sitemap.xml", status=404)
        for path in ("/about", "/services", "/contact", "/blog", "/privacy"):
            responses.add(responses.GET, f"https://acme.com{path}", status=404)

        import scraper.crawler as crawler_mod
        original_sleep = crawler_mod.time.sleep
        crawler_mod.time.sleep = lambda s: None

        progress_calls = []

        try:
            result = crawl_site(
                "https://acme.com",
                max_pages=2,
                progress_callback=lambda msg, pct: progress_calls.append((msg, pct)),
            )
        finally:
            crawler_mod.time.sleep = original_sleep

        assert len(progress_calls) >= 2  # At least "Crawling..." and "Homepage scraped"
        assert any("Crawling" in msg for msg, _ in progress_calls)
        assert any("Homepage scraped" in msg for msg, _ in progress_calls)

    @responses.activate
    def test_crawl_with_sitemap(self):
        """Sitemap URLs are included in the seed pool."""
        responses.add(responses.GET, "https://acme.com", body=HOMEPAGE_HTML, status=200)
        responses.add(responses.GET, "https://acme.com/robots.txt", status=404)
        responses.add(responses.GET, "https://acme.com/sitemap.xml", body=SITEMAP_XML, status=200)
        responses.add(responses.GET, "https://acme.com/services", body=SERVICES_PAGE_HTML, status=200)
        for path in ("/about", "/blog"):
            responses.add(responses.GET, f"https://acme.com{path}", status=404)
        # Contact from nav
        responses.add(responses.GET, "https://acme.com/contact", status=404)

        import scraper.crawler as crawler_mod
        original_sleep = crawler_mod.time.sleep
        crawler_mod.time.sleep = lambda s: None

        try:
            result = crawl_site("https://acme.com", max_pages=5, max_depth=1)
        finally:
            crawler_mod.time.sleep = original_sleep

        assert isinstance(result, ScrapeResult)
        page_urls = [p.url for p in result.pages]
        assert "https://acme.com/services" in page_urls

    @responses.activate
    def test_crawl_duration_is_recorded(self):
        """crawl_duration_s is always set and positive."""
        responses.add(responses.GET, "https://acme.com", body=HOMEPAGE_HTML, status=200)
        responses.add(responses.GET, "https://acme.com/robots.txt", status=404)
        responses.add(responses.GET, "https://acme.com/sitemap.xml", status=404)
        for path in ("/about", "/services", "/contact", "/blog", "/privacy"):
            responses.add(responses.GET, f"https://acme.com{path}", status=404)

        import scraper.crawler as crawler_mod
        original_sleep = crawler_mod.time.sleep
        crawler_mod.time.sleep = lambda s: None

        try:
            result = crawl_site("https://acme.com")
        finally:
            crawler_mod.time.sleep = original_sleep

        assert result.crawl_duration_s >= 0

    @responses.activate
    def test_social_link_dedup_across_pages(self):
        """Same social link on homepage and subpage appears only once."""
        html_with_dup_social = """
        <html><body>
            <nav><a href="/about">About</a></nav>
            <a href="https://facebook.com/acme">FB</a>
        </body></html>
        """
        about_with_dup_social = """
        <html><body>
            <h1>About</h1>
            <a href="https://facebook.com/acme">FB Again</a>
        </body></html>
        """
        responses.add(responses.GET, "https://acme.com", body=html_with_dup_social, status=200)
        responses.add(responses.GET, "https://acme.com/robots.txt", status=404)
        responses.add(responses.GET, "https://acme.com/sitemap.xml", status=404)
        responses.add(responses.GET, "https://acme.com/about", body=about_with_dup_social, status=200)
        for path in ("/services", "/contact", "/blog", "/privacy"):
            responses.add(responses.GET, f"https://acme.com{path}", status=404)

        import scraper.crawler as crawler_mod
        original_sleep = crawler_mod.time.sleep
        crawler_mod.time.sleep = lambda s: None

        try:
            result = crawl_site("https://acme.com", max_pages=5, max_depth=1)
        finally:
            crawler_mod.time.sleep = original_sleep

        facebook_count = sum(1 for sl in result.social_links if sl.platform == "facebook")
        assert facebook_count == 1, f"Expected 1 facebook link, got {facebook_count}"


# ── AnalysisRequest additions ────────────────────────────────────────────────


class TestAnalysisRequestCrawlerFields:
    def test_default_max_pages(self):
        from core.models import AnalysisRequest
        req = AnalysisRequest(target_url="https://acme.com")
        assert req.max_pages == 5
        assert req.max_depth == 2

    def test_custom_max_pages(self):
        from core.models import AnalysisRequest
        req = AnalysisRequest(target_url="https://acme.com", max_pages=10, max_depth=3)
        assert req.max_pages == 10
        assert req.max_depth == 3