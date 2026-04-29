"""Web scraper — extracts clean text from URLs."""
from __future__ import annotations

import requests
from bs4 import BeautifulSoup


MAX_LENGTH = 50_000  # chars


def scrape(url: str, timeout: int = 15) -> str:
    """
    Fetch and extract clean text from a URL.

    Falls back to empty string if the domain can't be reached.

    Args:
        url: The target URL.
        timeout: Request timeout in seconds.

    Returns:
        Cleaned text content from the page.
    """
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

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove noise elements
        for tag in soup.find_all(["script", "style", "nav", "header", "footer", "aside", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        # Collapse blank lines
        lines = [line for line in text.splitlines() if line.strip()]
        return "\n".join(lines)[:MAX_LENGTH]

    except Exception:
        return ""


def extract_domain_name(url: str) -> str:
    """Extract a readable domain name for fallback LLM inference."""
    from urllib.parse import urlparse
    parsed = urlparse(url if "://" in url else f"https://{url}")
    domain = parsed.netloc or parsed.path
    return domain.replace("www.", "").split(":")[0]