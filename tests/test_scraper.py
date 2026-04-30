from __future__ import annotations

import requests
import responses

from scraper import scraper
from scraper.scraper import extract_domain_name, normalize_url, scrape


def test_scrape_extracts_visible_text_from_simple_html():
    html = """
    <html>
      <head><title>Acme Home</title></head>
      <body>
        <main>
          <h1>Acme Widgets</h1>
          <p>We build durable widgets for local businesses.</p>
        </main>
      </body>
    </html>
    """

    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, "https://example.com", body=html, status=200)

        text = scrape("https://example.com")

    assert "Acme Widgets" in text
    assert "We build durable widgets for local businesses." in text


def test_scrape_removes_noise_elements():
    html = """
    <html>
      <body>
        <header>Header noise</header>
        <nav>Navigation noise</nav>
        <aside>Aside noise</aside>
        <main><h1>Important content</h1></main>
        <footer>Footer noise</footer>
        <script>console.log('script noise')</script>
        <style>.noise { color: red; }</style>
        <noscript>Noscript noise</noscript>
      </body>
    </html>
    """

    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, "https://example.com", body=html, status=200)

        text = scrape("https://example.com")

    assert "Important content" in text
    assert "Header noise" not in text
    assert "Navigation noise" not in text
    assert "Aside noise" not in text
    assert "Footer noise" not in text
    assert "script noise" not in text
    assert "color: red" not in text
    assert "Noscript noise" not in text


def test_scrape_returns_empty_string_on_network_failure():
    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, "https://example.com", body=requests.Timeout("boom"))

        assert scrape("https://example.com") == ""


def test_scrape_normalizes_bare_domains_before_requesting():
    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, "https://example.com", body="<main>Hello</main>", status=200)

        text = scrape("example.com")

    assert text == "Hello"


def test_scrape_sets_clear_user_agent():
    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, "https://example.com", body="<main>Hello</main>", status=200)

        scrape("https://example.com", timeout=7)

        request = rsps.calls[0].request

    assert "ReconIQ/1.0" in request.headers["User-Agent"]


def test_scrape_caps_returned_text(monkeypatch):
    monkeypatch.setattr(scraper, "MAX_LENGTH", 12)
    html = "<main>abcdefghijklmnopqrstuvwxyz</main>"

    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, "https://example.com", body=html, status=200)

        text = scrape("https://example.com")

    assert text == "abcdefghijkl"


def test_extract_domain_name_handles_url_with_www_and_path():
    assert extract_domain_name("https://www.example.com/path") == "example.com"


def test_normalize_url_adds_https_to_bare_domain():
    assert normalize_url("example.com") == "https://example.com"


def test_normalize_url_preserves_existing_scheme():
    assert normalize_url("http://example.com") == "http://example.com"
    assert normalize_url("https://example.com") == "https://example.com"
