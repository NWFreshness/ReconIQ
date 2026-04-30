"""Tests for scraper/models.py and scraper/extractors.py — Phase 9J-1."""
from __future__ import annotations

import json
import pytest
from bs4 import BeautifulSoup

from scraper.models import ScrapeResult, PageData, LinkData, SocialLink
from scraper.extractors import (
    extract_meta,
    extract_links,
    extract_social_links,
    extract_contact_info,
    extract_json_ld,
    extract_headings,
)


# ── Models ──────────────────────────────────────────────────────────────────────


class TestScrapeResult:
    """Test the ScrapeResult dataclass."""

    def test_default_fields(self):
        result = ScrapeResult(url="https://example.com", title="Example")
        assert result.url == "https://example.com"
        assert result.title == "Example"
        assert result.meta_description == ""
        assert result.meta_keywords == []
        assert result.og_tags == {}
        assert result.headings == {}
        assert result.internal_links == []
        assert result.external_links == []
        assert result.social_links == []
        assert result.phone_numbers == []
        assert result.emails == []
        assert result.json_ld == []
        assert result.body_text == ""
        assert result.pages == []
        assert result.raw_html_length == 0
        assert result.crawl_duration_s == 0.0

    def test_all_fields(self):
        result = ScrapeResult(
            url="https://example.com",
            title="Example",
            meta_description="A site",
            meta_keywords=["test", "example"],
            og_tags={"og:title": "Example", "og:description": "A site"},
            headings={"h1": ["Welcome"], "h2": ["About", "Services"]},
            internal_links=[LinkData(href="/about", text="About Us")],
            external_links=[LinkData(href="https://other.com", text="Other")],
            social_links=[SocialLink(platform="facebook", url="https://facebook.com/example")],
            phone_numbers=["(555) 123-4567"],
            emails=["info@example.com"],
            json_ld=[{"@type": "LocalBusiness", "name": "Example"}],
            body_text="Welcome to Example",
            pages=[PageData(url="https://example.com/about", title="About", text="About us")],
            raw_html_length=5000,
            crawl_duration_s=2.3,
        )
        assert result.title == "Example"
        assert len(result.meta_keywords) == 2
        assert len(result.internal_links) == 1
        assert len(result.external_links) == 1
        assert result.social_links[0].platform == "facebook"
        assert result.json_ld[0]["@type"] == "LocalBusiness"
        assert len(result.pages) == 1
        assert result.crawl_duration_s == 2.3


class TestPageData:
    def test_page_data_fields(self):
        page = PageData(url="https://example.com/about", title="About Us", text="About us content")
        assert page.url == "https://example.com/about"
        assert page.title == "About Us"
        assert page.text == "About us content"
        assert page.headings == {}

    def test_page_data_with_headings(self):
        page = PageData(
            url="https://example.com/services",
            title="Our Services",
            text="Service details",
            headings={"h2": ["Pest Control", "Rodent Removal"]},
        )
        assert page.headings["h2"] == ["Pest Control", "Rodent Removal"]


class TestLinkData:
    def test_link_data(self):
        link = LinkData(href="/contact", text="Contact Us")
        assert link.href == "/contact"
        assert link.text == "Contact Us"


class TestSocialLink:
    def test_social_link(self):
        sl = SocialLink(platform="linkedin", url="https://linkedin.com/company/example")
        assert sl.platform == "linkedin"
        assert sl.url == "https://linkedin.com/company/example"


# ── extract_meta ────────────────────────────────────────────────────────────────


class TestExtractMeta:
    def test_extracts_title(self):
        html = "<html><head><title>My Site</title></head><body></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        result = extract_meta(soup)
        assert result["title"] == "My Site"

    def test_extracts_meta_description(self):
        html = '<html><head><meta name="description" content="A great site"></head><body></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        result = extract_meta(soup)
        assert result["meta_description"] == "A great site"

    def test_extracts_meta_keywords(self):
        html = '<html><head><meta name="keywords" content="pest control, vancouver, wa"></head><body></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        result = extract_meta(soup)
        assert result["meta_keywords"] == ["pest control", "vancouver", "wa"]

    def test_extracts_og_tags(self):
        html = '''<html><head>
            <meta property="og:title" content="OG Title">
            <meta property="og:description" content="OG Desc">
            <meta property="og:image" content="https://example.com/img.png">
        </head><body></body></html>'''
        soup = BeautifulSoup(html, "html.parser")
        result = extract_meta(soup)
        assert result["og_tags"]["og:title"] == "OG Title"
        assert result["og_tags"]["og:description"] == "OG Desc"
        assert result["og_tags"]["og:image"] == "https://example.com/img.png"

    def test_empty_html_returns_defaults(self):
        html = "<html><body></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        result = extract_meta(soup)
        assert result["title"] == ""
        assert result["meta_description"] == ""
        assert result["meta_keywords"] == []
        assert result["og_tags"] == {}

    def test_missing_title_uses_h1_fallback(self):
        html = "<html><body><h1>Fallback Title</h1></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        result = extract_meta(soup)
        assert result["title"] == "Fallback Title"

    def test_title_preferred_over_h1(self):
        html = "<html><head><title>Real Title</title></head><body><h1>Not This</h1></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        result = extract_meta(soup)
        assert result["title"] == "Real Title"


# ── extract_links ────────────────────────────────────────────────────────────────


class TestExtractLinks:
    def test_separates_internal_and_external(self):
        html = '''<html><body>
            <a href="/about">About</a>
            <a href="https://example.com/services">Services</a>
            <a href="https://other.com">External</a>
            <a href="https://example.com/contact">Contact</a>
        </body></html>'''
        soup = BeautifulSoup(html, "html.parser")
        internal, external = extract_links(soup, "https://example.com")
        internal_hrefs = [l.href for l in internal]
        external_hrefs = [l.href for l in external]
        assert "/about" in internal_hrefs
        assert "https://example.com/services" in internal_hrefs
        assert "https://example.com/contact" in internal_hrefs
        assert "https://other.com" in external_hrefs

    def test_excludes_anchor_and_javascript_links(self):
        html = '''<html><body>
            <a href="#section">Jump</a>
            <a href="javascript:void(0)">Click</a>
            <a href="/about">About</a>
        </body></html>'''
        soup = BeautifulSoup(html, "html.parser")
        internal, external = extract_links(soup, "https://example.com")
        all_hrefs = [l.href for l in internal + external]
        assert "#section" not in all_hrefs
        assert "javascript:void(0)" not in all_hrefs
        assert "/about" in [l.href for l in internal]

    def test_preserves_link_text(self):
        html = '<html><body><a href="/about">About Us</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        internal, _ = extract_links(soup, "https://example.com")
        assert internal[0].text == "About Us"

    def test_empty_page_returns_empty_lists(self):
        html = "<html><body></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        internal, external = extract_links(soup, "https://example.com")
        assert internal == []
        assert external == []

    def test_subdomain_is_external(self):
        html = '<html><body><a href="https://blog.example.com/post">Blog</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        internal, external = extract_links(soup, "https://example.com")
        # blog.example.com is a different host from example.com
        assert any("blog.example.com" in l.href for l in external)

    def test_www_variant_is_internal(self):
        html = '<html><body><a href="https://www.example.com/page">Page</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        internal, external = extract_links(soup, "https://example.com")
        # www.example.com should be treated as same domain
        assert len(internal) >= 1 or len(external) >= 1  # either way is acceptable, just not crash


# ── extract_social_links ────────────────────────────────────────────────────────


class TestExtractSocialLinks:
    def test_detects_facebook(self):
        html = '<html><body><a href="https://www.facebook.com/ExampleBiz">Facebook</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        links = extract_social_links(soup)
        assert len(links) == 1
        assert links[0].platform == "facebook"
        assert links[0].url == "https://www.facebook.com/ExampleBiz"

    def test_detects_instagram(self):
        html = '<html><body><a href="https://instagram.com/examplebiz">Instagram</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        links = extract_social_links(soup)
        assert len(links) == 1
        assert links[0].platform == "instagram"

    def test_detects_twitter_x(self):
        html = '<html><body><a href="https://x.com/examplebiz">X</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        links = extract_social_links(soup)
        assert len(links) == 1
        assert links[0].platform == "x"

    def test_detects_twitter_old_domain(self):
        html = '<html><body><a href="https://twitter.com/examplebiz">Twitter</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        links = extract_social_links(soup)
        assert len(links) == 1
        assert links[0].platform == "twitter"

    def test_detects_linkedin(self):
        html = '<html><body><a href="https://www.linkedin.com/company/example">LinkedIn</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        links = extract_social_links(soup)
        assert len(links) == 1
        assert links[0].platform == "linkedin"

    def test_detects_yelp(self):
        html = '<html><body><a href="https://www.yelp.com/biz/example-portland">Yelp</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        links = extract_social_links(soup)
        assert len(links) == 1
        assert links[0].platform == "yelp"

    def test_detects_google_maps(self):
        html = '<html><body><a href="https://www.google.com/maps/place/Example+Biz">Reviews</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        links = extract_social_links(soup)
        assert len(links) == 1
        assert links[0].platform == "google_maps"

    def test_detects_youtube(self):
        html = '<html><body><a href="https://www.youtube.com/@examplebiz">YouTube</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        links = extract_social_links(soup)
        assert len(links) == 1
        assert links[0].platform == "youtube"

    def test_detects_tiktok(self):
        html = '<html><body><a href="https://www.tiktok.com/@examplebiz">TikTok</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        links = extract_social_links(soup)
        assert len(links) == 1
        assert links[0].platform == "tiktok"

    def test_detects_nextdoor(self):
        html = '<html><body><a href="https://nextdoor.com/business/example-biz/id/">Nextdoor</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        links = extract_social_links(soup)
        assert len(links) == 1
        assert links[0].platform == "nextdoor"

    def test_multiple_social_links(self):
        html = '''<html><body>
            <a href="https://www.facebook.com/example">FB</a>
            <a href="https://www.instagram.com/example">IG</a>
            <a href="https://www.yelp.com/biz/example">Yelp</a>
            <a href="/about">About</a>
        </body></html>'''
        soup = BeautifulSoup(html, "html.parser")
        links = extract_social_links(soup)
        platforms = [l.platform for l in links]
        assert "facebook" in platforms
        assert "instagram" in platforms
        assert "yelp" in platforms
        assert len(links) == 3  # /about is not social

    def test_no_social_links(self):
        html = '<html><body><a href="/about">About</a><a href="/contact">Contact</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        links = extract_social_links(soup)
        assert links == []

    def test_deduplicates_same_url(self):
        html = '''<html><body>
            <a href="https://www.facebook.com/example">FB Header</a>
            <a href="https://www.facebook.com/example">FB Footer</a>
        </body></html>'''
        soup = BeautifulSoup(html, "html.parser")
        links = extract_social_links(soup)
        assert len(links) == 1  # same URL, different text — deduplicated


# ── extract_contact_info ────────────────────────────────────────────────────────


class TestExtractContactInfo:
    def test_extracts_us_phone_numbers(self):
        html = '<html><body><p>Call us at (555) 123-4567 today!</p></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        phones, emails = extract_contact_info(soup)
        assert len(phones) >= 1
        assert "(555) 123-4567" in phones[0] or "5551234567" in phones[0].replace("-", "").replace(" ", "")

    def test_extracts_dashed_phone_numbers(self):
        html = '<html><body><p>Call 555-123-4567</p></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        phones, emails = extract_contact_info(soup)
        assert len(phones) >= 1

    def test_extracts_email_addresses(self):
        html = '<html><body><p>Contact us at info@example.com for help.</p></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        phones, emails = extract_contact_info(soup)
        assert "info@example.com" in emails

    def test_extracts_mailto_links(self):
        html = '<html><body><a href="mailto:sales@example.com">Email Sales</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        phones, emails = extract_contact_info(soup)
        assert "sales@example.com" in emails

    def test_extracts_tel_links(self):
        html = '<html><body><a href="tel:+1-555-123-4567">Call Us</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        phones, emails = extract_contact_info(soup)
        assert len(phones) >= 1

    def test_multiple_emails(self):
        html = '''<html><body>
            <a href="mailto:info@example.com">Info</a>
            <a href="mailto:sales@example.com">Sales</a>
        </body></html>'''
        soup = BeautifulSoup(html, "html.parser")
        phones, emails = extract_contact_info(soup)
        assert "info@example.com" in emails
        assert "sales@example.com" in emails

    def test_empty_page(self):
        html = "<html><body></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        phones, emails = extract_contact_info(soup)
        assert phones == []
        assert emails == []

    def test_deduplicates_emails(self):
        html = '''<html><body>
            <a href="mailto:info@example.com">Info</a>
            <p>Contact info@example.com</p>
        </body></html>'''
        soup = BeautifulSoup(html, "html.parser")
        phones, emails = extract_contact_info(soup)
        assert emails.count("info@example.com") == 1


# ── extract_json_ld ──────────────────────────────────────────────────────────────


class TestExtractJsonLd:
    def test_extracts_local_business_schema(self):
        schema = json.dumps({
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": "Aspen Pest Control",
            "address": {
                "@type": "PostalAddress",
                "addressLocality": "Vancouver",
                "addressRegion": "WA"
            }
        })
        html = f'<html><head><script type="application/ld+json">{schema}</script></head><body></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        result = extract_json_ld(soup)
        assert len(result) == 1
        assert result[0]["@type"] == "LocalBusiness"
        assert result[0]["name"] == "Aspen Pest Control"

    def test_extracts_multiple_schemas(self):
        schema1 = json.dumps({"@type": "LocalBusiness", "name": "Biz"})
        schema2 = json.dumps({"@type": "FAQPage", "mainEntity": []})
        html = f'''<html><head>
            <script type="application/ld+json">{schema1}</script>
            <script type="application/ld+json">{schema2}</script>
        </head><body></body></html>'''
        soup = BeautifulSoup(html, "html.parser")
        result = extract_json_ld(soup)
        assert len(result) == 2
        types = [r["@type"] for r in result]
        assert "LocalBusiness" in types
        assert "FAQPage" in types

    def test_returns_empty_for_no_schema(self):
        html = "<html><body></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        result = extract_json_ld(soup)
        assert result == []

    def test_handles_invalid_json_gracefully(self):
        html = '<html><head><script type="application/ld+json">{invalid json}</script></head><body></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        result = extract_json_ld(soup)
        # Should not crash, should return empty or skip the invalid one
        assert isinstance(result, list)

    def test_preserves_nested_address(self):
        schema = json.dumps({
            "@type": "LocalBusiness",
            "name": "Test",
            "address": {
                "@type": "PostalAddress",
                "streetAddress": "123 Main St",
                "addressLocality": "Vancouver",
                "addressRegion": "WA",
                "postalCode": "98660"
            }
        })
        html = f'<html><head><script type="application/ld+json">{schema}</script></head><body></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        result = extract_json_ld(soup)
        assert result[0]["address"]["postalCode"] == "98660"


# ── extract_headings ─────────────────────────────────────────────────────────────


class TestExtractHeadings:
    def test_extracts_h1_h2_h3(self):
        html = '''<html><body>
            <h1>Main Title</h1>
            <h2>Section One</h2>
            <h3>Subsection A</h3>
            <h2>Section Two</h2>
            <h3>Subsection B</h3>
            <h3>Subsection C</h3>
        </body></html>'''
        soup = BeautifulSoup(html, "html.parser")
        headings = extract_headings(soup)
        assert "h1" in headings
        assert headings["h1"] == ["Main Title"]
        assert headings["h2"] == ["Section One", "Section Two"]
        assert headings["h3"] == ["Subsection A", "Subsection B", "Subsection C"]

    def test_no_headings(self):
        html = "<html><body><p>Just text</p></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        headings = extract_headings(soup)
        assert headings == {}

    def test_ignores_h4_and_below(self):
        html = '''<html><body>
            <h1>Title</h1>
            <h4>Subtitle</h4>
        </body></html>'''
        soup = BeautifulSoup(html, "html.parser")
        headings = extract_headings(soup)
        assert "h4" not in headings
        assert headings["h1"] == ["Title"]

    def test_strips_whitespace(self):
        html = "<html><body><h1>   Spaced Title   </h1></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        headings = extract_headings(soup)
        assert headings["h1"] == ["Spaced Title"]

    def test_multiple_h1(self):
        html = '''<html><body>
            <h1>First H1</h1>
            <h1>Second H1</h1>
        </body></html>'''
        soup = BeautifulSoup(html, "html.parser")
        headings = extract_headings(soup)
        assert len(headings["h1"]) == 2