"""Tests for Phase 9I: Batch Analysis."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.batch import read_urls, run_batch
from core.models import AnalysisRequest


class TestReadUrls:
    def test_plain_text(self, tmp_path: Path) -> None:
        f = tmp_path / "urls.txt"
        f.write_text("https://a.com\nhttps://b.com\n")
        urls = read_urls(str(f))
        assert urls == ["https://a.com", "https://b.com"]

    def test_csv_with_header(self, tmp_path: Path) -> None:
        f = tmp_path / "urls.csv"
        f.write_text("url,note\nhttps://a.com,first\nhttps://b.com,second\n")
        urls = read_urls(str(f))
        assert urls == ["https://a.com", "https://b.com"]

    def test_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            read_urls(str(tmp_path / "missing.txt"))


class TestRunBatch:
    @patch("core.batch.run_analysis")
    def test_sequential_execution(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(report_path="/tmp/report.md")
        request = AnalysisRequest(target_url="dummy")
        results = run_batch(
            urls=["https://a.com", "https://b.com"],
            base_request=request,
            max_workers=1,
        )
        assert len(results) == 2
        assert mock_run.call_count == 2
        assert results[0]["error"] is None
        assert results[0]["report_path"] == "/tmp/report.md"

    @patch("core.batch.run_analysis")
    def test_error_handling(self, mock_run: MagicMock) -> None:
        mock_run.side_effect = [Exception("boom"), MagicMock(report_path="/tmp/report.md")]
        request = AnalysisRequest(target_url="dummy")
        results = run_batch(
            urls=["https://a.com", "https://b.com"],
            base_request=request,
            max_workers=1,
        )
        assert len(results) == 2
        assert results[0]["error"] is not None
        assert results[1]["error"] is None

    @patch("core.batch.run_analysis")
    def test_progress_callback(self, mock_run: MagicMock) -> None:
        def side_effect(request, progress_callback=None):
            if progress_callback:
                progress_callback("crawling", 50.0)
            return MagicMock(report_path="/tmp/report.md")

        mock_run.side_effect = side_effect
        progress_calls: list[tuple[str, float]] = []

        def progress(msg: str, pct: float) -> None:
            progress_calls.append((msg, pct))

        request = AnalysisRequest(target_url="dummy")
        run_batch(
            urls=["https://a.com"],
            base_request=request,
            max_workers=1,
            progress_callback=progress,
        )
        assert len(progress_calls) > 0
