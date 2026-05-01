"""Framework-neutral request and result models for ReconIQ."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

DEFAULT_ENABLED_MODULES = {
    "company_profile": True,
    "seo_keywords": True,
    "competitor": True,
    "social_content": True,
    "swot": True,
}


@dataclass(slots=True)
class AnalysisRequest:
    """Input for a ReconIQ analysis run."""

    target_url: str
    enabled_modules: dict[str, bool] = field(default_factory=lambda: DEFAULT_ENABLED_MODULES.copy())
    provider_override: str | None = None
    model_override: str | None = None
    output_dir: str | None = None
    fmt: str = "md"  # "md", "html", or "pdf"
    # Crawler settings (Phase 9J-2)
    max_pages: int = 5       # max subpages to crawl (excluding homepage)
    max_depth: int = 2       # max crawl depth from homepage


@dataclass(slots=True)
class AnalysisResult:
    """Output from a ReconIQ analysis run."""

    results: dict[str, Any]
    report_path: str | None
