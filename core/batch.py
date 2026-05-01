"""Batch analysis — run ReconIQ against multiple URLs."""
from __future__ import annotations

import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable

from core.models import AnalysisRequest
from core.services import run_analysis


ProgressCallback = Callable[[str, float], None] | None


def read_urls(path: str | Path) -> list[str]:
    """Read URLs from a CSV or plain text file.

    CSV files should have the URL in the first column.
    Plain text files should have one URL per line.
    Header rows starting with 'url' are skipped.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Batch file not found: {path}")

    urls: list[str] = []
    text = p.read_text(encoding="utf-8").strip()
    # Try CSV first
    try:
        reader = csv.reader(text.splitlines())
        for row in reader:
            if row:
                first = row[0].strip()
                if first and not first.lower().startswith("url"):
                    urls.append(first)
    except Exception:
        # Fall back to plain text
        for line in text.splitlines():
            stripped = line.strip()
            if stripped and not stripped.lower().startswith("url"):
                urls.append(stripped)
    return urls


def run_batch(
    urls: list[str],
    base_request: AnalysisRequest,
    max_workers: int = 1,
    progress_callback: ProgressCallback = None,
) -> list[dict]:
    """Run analysis for multiple URLs.

    Args:
        urls: List of target URLs to analyze.
        base_request: Template AnalysisRequest (target_url will be overridden per URL).
        max_workers: Number of parallel analyses. Use 1 for sequential execution.
        progress_callback: Optional callback(msg, pct) for overall progress.

    Returns:
        List of result dicts with keys: url, report_path, error (if any).
    """
    results: list[dict] = []
    total = len(urls)

    def run_one(url: str, idx: int) -> dict:
        request = AnalysisRequest(
            target_url=url,
            enabled_modules=base_request.enabled_modules,
            provider_override=base_request.provider_override,
            model_override=base_request.model_override,
            output_dir=base_request.output_dir,
            fmt=base_request.fmt,
            max_pages=base_request.max_pages,
            max_depth=base_request.max_depth,
        )

        def inner_progress(msg: str, pct: float) -> None:
            if progress_callback:
                overall = ((idx - 1) + pct / 100.0) / total * 100.0
                progress_callback(f"[{idx}/{total}] {msg}", overall)

        try:
            result = run_analysis(request, progress_callback=inner_progress)
            return {"url": url, "report_path": result.report_path, "error": None}
        except Exception as exc:
            return {"url": url, "report_path": None, "error": str(exc)}

    if max_workers <= 1:
        for i, url in enumerate(urls, 1):
            results.append(run_one(url, i))
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(run_one, url, i): url for i, url in enumerate(urls, 1)}
            for future in as_completed(futures):
                results.append(future.result())

    return results
