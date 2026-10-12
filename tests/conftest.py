"""Shared pytest fixtures."""
from __future__ import annotations

import ipaddress

import pytest


def _fake_resolve(host: str) -> list[str]:
    try:
        ipaddress.ip_address(host)
        return [host]
    except ValueError:
        return ["93.184.216.34"]


@pytest.fixture(autouse=True)
def _no_real_dns(monkeypatch):
    """Keep the SSRF guard off the network: every hostname resolves to a public IP."""
    monkeypatch.setattr("scraper.scraper._resolve_ips", _fake_resolve, raising=False)
