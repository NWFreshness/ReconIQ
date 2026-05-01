"""Tests for Phase 9H: CLI Interface."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cli import main, _parse_modules, _read_urls_from_file


class TestParseModules:
    def test_default_returns_all_enabled(self) -> None:
        result = _parse_modules(None)
        assert result["company_profile"] is True
        assert result["seo_keywords"] is True
        assert result["competitor"] is True
        assert result["social_content"] is True
        assert result["swot"] is True

    def test_subset(self) -> None:
        result = _parse_modules("company_profile,swot")
        assert result["company_profile"] is True
        assert result["swot"] is True
        assert result["seo_keywords"] is False

    def test_invalid_module_ignored(self) -> None:
        result = _parse_modules("company_profile,invalid_module")
        assert result["company_profile"] is True
        assert result.get("invalid_module") is None


class TestReadUrlsFromFile:
    def test_plain_text(self, tmp_path: Path) -> None:
        f = tmp_path / "urls.txt"
        f.write_text("https://a.com\nhttps://b.com\n")
        urls = _read_urls_from_file(str(f))
        assert urls == ["https://a.com", "https://b.com"]

    def test_csv(self, tmp_path: Path) -> None:
        f = tmp_path / "urls.csv"
        f.write_text("url\nhttps://a.com\nhttps://b.com\n")
        urls = _read_urls_from_file(str(f))
        assert urls == ["https://a.com", "https://b.com"]

    def test_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            _read_urls_from_file(str(tmp_path / "missing.txt"))


class TestCLIMain:
    @patch("cli.run_analysis")
    def test_single_url(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(report_path="/tmp/report.md")
        rc = main(["https://example.com", "--quiet"])
        assert rc == 0
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args.target_url == "https://example.com"

    @patch("cli.run_analysis")
    def test_format_html(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(report_path="/tmp/report.html")
        rc = main(["https://example.com", "--format", "html", "--quiet"])
        assert rc == 0
        call_args = mock_run.call_args[0][0]
        assert call_args.fmt == "html"

    @patch("cli.run_analysis")
    def test_batch_mode(self, mock_run: MagicMock, tmp_path: Path) -> None:
        batch_file = tmp_path / "urls.txt"
        batch_file.write_text("https://a.com\nhttps://b.com\n")
        mock_run.return_value = MagicMock(report_path="/tmp/report.md")
        rc = main(["--batch", str(batch_file), "--quiet"])
        assert rc == 0
        assert mock_run.call_count == 2

    def test_no_args_shows_help(self, capsys: pytest.CaptureFixture) -> None:
        rc = main([])
        captured = capsys.readouterr()
        assert rc == 1
        assert "usage:" in captured.out or "usage:" in captured.err

    @patch("cli.run_analysis")
    def test_provider_override(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(report_path="/tmp/report.md")
        rc = main(["https://example.com", "--provider", "openai", "--quiet"])
        assert rc == 0
        call_args = mock_run.call_args[0][0]
        assert call_args.provider_override == "openai"

    @patch("cli.run_analysis")
    def test_model_override(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(report_path="/tmp/report.md")
        rc = main(["https://example.com", "--model", "gpt-4o", "--quiet"])
        assert rc == 0
        call_args = mock_run.call_args[0][0]
        assert call_args.model_override == "gpt-4o"
