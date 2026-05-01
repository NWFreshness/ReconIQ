"""Tests for Phase 9F: Export Formats (HTML, PDF)."""
from __future__ import annotations

from pathlib import Path

import pytest

from report.writer import (
    write_html_report,
    write_pdf_report,
    write_report,
    _build_markdown,
)


SAMPLE_RESULTS = {
    "company_profile": {"company_name": "TestCo", "industry": "Software"},
    "seo_keywords": {"primary_keywords": ["ai", "automation"]},
    "competitor": {"competitors": [{"name": "RivalCo", "url": "https://rival.co"}]},
    "social_content": {"platforms": ["LinkedIn"]},
    "swot": {
        "swot": {
            "strengths": ["Fast"],
            "weaknesses": ["Small"],
            "opportunities": ["Growth"],
            "threats": ["Competition"],
        }
    },
    "metadata": {
        "target_url": "https://testco.example",
        "timestamp": "2026-01-01 12:00:00",
        "modules_run": ["company_profile", "seo_keywords", "competitor", "social_content", "swot"],
        "modules_skipped": [],
        "modules_failed": [],
        "data_limitations": [],
    },
}


@pytest.fixture
def tmp_output_dir(tmp_path: Path) -> Path:
    return tmp_path / "reports"


class TestMarkdownExport:
    def test_write_report_default_md(self, tmp_output_dir: Path) -> None:
        path = write_report(SAMPLE_RESULTS, output_dir=str(tmp_output_dir), fmt="md")
        assert path.endswith(".md")
        assert Path(path).exists()
        content = Path(path).read_text(encoding="utf-8")
        assert "TestCo" in content
        assert "# ReconIQ Report: TestCo" in content


class TestHTMLExport:
    def test_write_html_report(self, tmp_output_dir: Path) -> None:
        md = _build_markdown(SAMPLE_RESULTS, "TestCo")
        html_path = tmp_output_dir / "test.html"
        result = write_html_report(md, html_path, title="Test Report")
        assert result.endswith(".html")
        assert html_path.exists()
        content = html_path.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert "Test Report" in content
        assert "TestCo" in content

    def test_write_report_html_format(self, tmp_output_dir: Path) -> None:
        path = write_report(SAMPLE_RESULTS, output_dir=str(tmp_output_dir), fmt="html")
        assert path.endswith(".html")
        assert Path(path).exists()
        content = Path(path).read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content


class TestPDFExport:
    def test_write_pdf_report(self, tmp_output_dir: Path) -> None:
        md = _build_markdown(SAMPLE_RESULTS, "TestCo")
        pdf_path = tmp_output_dir / "test.pdf"
        result = write_pdf_report(md, pdf_path, title="Test Report")
        assert result.endswith(".pdf")
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0

    def test_write_report_pdf_format(self, tmp_output_dir: Path) -> None:
        path = write_report(SAMPLE_RESULTS, output_dir=str(tmp_output_dir), fmt="pdf")
        assert path.endswith(".pdf")
        assert Path(path).exists()
        assert Path(path).stat().st_size > 0


class TestExportBackwardCompat:
    def test_default_format_is_md(self, tmp_output_dir: Path) -> None:
        path = write_report(SAMPLE_RESULTS, output_dir=str(tmp_output_dir))
        assert path.endswith(".md")
