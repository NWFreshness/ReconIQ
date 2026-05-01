"""Playwright smoke test for the Streamlit UI."""
from __future__ import annotations

import subprocess
import time

import pytest
from playwright.sync_api import sync_playwright


@pytest.fixture(scope="module")
def streamlit_app():
    """Start the Streamlit app in background and yield the base URL."""
    import sys
    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8599", "--server.headless", "true", "--browser.gatherUsageStats", "false"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    base_url = "http://localhost:8599"
    # Wait for server to start
    for _ in range(30):
        try:
            import urllib.request
            urllib.request.urlopen(base_url, timeout=1)
            break
        except Exception:
            time.sleep(0.5)
    else:
        proc.terminate()
        raise RuntimeError("Streamlit did not start in time")
    yield base_url
    proc.terminate()
    proc.wait()


def test_streamlit_ui_loads(streamlit_app):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(streamlit_app)
        # Wait for Streamlit to render
        page.wait_for_selector("text=Marketing Intelligence", timeout=15000)
        assert "ReconIQ" in page.title()
        assert page.locator("text=Analyze ").count() >= 1
        browser.close()
