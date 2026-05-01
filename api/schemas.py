"""FastAPI request/response schemas for ReconIQ."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator
from urllib.parse import urlparse


def _normalize_url(url: str) -> str:
    url = url.strip()
    parsed = urlparse(url)
    if not parsed.scheme:
        # Only prepend https if no scheme present at all (allows bare domains)
        url = "https://" + url
        parsed = urlparse(url)
    if parsed.netloc and not parsed.path:
        url = url.rstrip("/") + "/"
    return url


class AnalysisStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class ExportFormat(str, Enum):
    md = "md"
    html = "html"
    pdf = "pdf"


class AnalysisCreateRequest(BaseModel):
    target_url: str
    modules: list[str] = Field(default_factory=lambda: [
        "company_profile", "seo_keywords", "competitor", "social_content", "swot"
    ])
    provider: str | None = "deepseek"
    model: str | None = None
    fmt: ExportFormat = ExportFormat.md
    max_pages: int = Field(default=5, ge=1, le=20)
    max_depth: int = Field(default=2, ge=1, le=5)

    @field_validator("target_url", mode="before")
    @classmethod
    def target_url_must_be_valid(cls, v: str) -> str:
        url = _normalize_url(v)
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("target_url must be a valid URL with a scheme and host")
        if parsed.scheme not in ("http", "https"):
            raise ValueError("target_url must use http or https scheme")
        return url


class AnalysisResponse(BaseModel):
    id: str
    target_url: str
    status: AnalysisStatus
    modules: list[str]
    provider: str | None
    model: str | None
    fmt: str
    created_at: datetime
    updated_at: datetime
    progress_pct: float = 0.0
    progress_msg: str | None = None
    report_path: str | None = None
    error: str | None = None


class AnalysisResultResponse(BaseModel):
    id: str
    target_url: str
    status: AnalysisStatus
    results: dict[str, Any] | None = None
    report_path: str | None = None
    error: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    timestamp: datetime


class ReportDownloadResponse(BaseModel):
    filename: str
    content_type: str
