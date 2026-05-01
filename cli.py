"""ReconIQ CLI — run analysis from the command line without Streamlit."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from core.models import AnalysisRequest, DEFAULT_ENABLED_MODULES
from core.services import run_analysis


MODULE_CHOICES = ["company_profile", "seo_keywords", "competitor", "social_content", "swot"]
FORMAT_CHOICES = ["md", "html", "pdf"]


def _parse_modules(modules_str: str | None) -> dict[str, bool]:
    """Parse a comma-separated module list into an enabled-modules dict."""
    if not modules_str:
        return DEFAULT_ENABLED_MODULES.copy()
    enabled = {m: False for m in MODULE_CHOICES}
    for m in modules_str.split(","):
        key = m.strip()
        if key in enabled:
            enabled[key] = True
    return enabled


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reconiq",
        description="ReconIQ — Marketing Intelligence from the command line.",
    )
    parser.add_argument(
        "target_url",
        nargs="?",
        help="Target company URL to analyze (e.g. https://example.com).",
    )
    parser.add_argument(
        "--modules",
        type=str,
        default=",".join(MODULE_CHOICES),
        help=f"Comma-separated list of modules to run. Choices: {', '.join(MODULE_CHOICES)}. Default: all.",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="deepseek",
        help="LLM provider to use. Default: deepseek.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="",
        help="Model override (leave blank for provider default).",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="reports",
        help="Output directory for reports. Default: reports/",
    )
    parser.add_argument(
        "--format",
        "-f",
        type=str,
        choices=FORMAT_CHOICES,
        default="md",
        help="Export format. Default: md.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=5,
        help="Max subpages to crawl. Default: 5.",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=2,
        help="Max crawl depth. Default: 2.",
    )
    parser.add_argument(
        "--batch",
        type=str,
        default=None,
        help="Path to a CSV or text file with one URL per line for batch analysis.",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress progress output.",
    )
    return parser


def _run_single(url: str, args: argparse.Namespace) -> str:
    """Run a single analysis and return the report path."""
    request = AnalysisRequest(
        target_url=url,
        enabled_modules=_parse_modules(args.modules),
        provider_override=args.provider if args.provider != "deepseek" else None,
        model_override=args.model or None,
        output_dir=args.output,
        fmt=args.format,
        max_pages=args.max_pages,
        max_depth=args.max_depth,
    )

    def progress(msg: str, pct: float) -> None:
        if not args.quiet:
            print(f"  [{pct:>3.0f}%] {msg}")

    result = run_analysis(request, progress_callback=progress)
    return result.report_path or ""


def _read_urls_from_file(path: str) -> list[str]:
    """Read URLs from a CSV or plain text file."""
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
        # Fall back to plain text (one URL per line)
        for line in text.splitlines():
            stripped = line.strip()
            if stripped and not stripped.lower().startswith("url"):
                urls.append(stripped)
    return urls


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Batch mode
    if args.batch:
        urls = _read_urls_from_file(args.batch)
        if not urls:
            print("No URLs found in batch file.", file=sys.stderr)
            return 1
        if not args.quiet:
            print(f"Running batch analysis for {len(urls)} URL(s)...")
        report_paths: list[str] = []
        for i, url in enumerate(urls, 1):
            if not args.quiet:
                print(f"\n[{i}/{len(urls)}] Analyzing {url}...")
            try:
                path = _run_single(url, args)
                report_paths.append(path)
                if not args.quiet:
                    print(f"  ✓ Report: {path}")
            except Exception as exc:
                print(f"  ✗ Error: {exc}", file=sys.stderr)
                report_paths.append("")
        if not args.quiet:
            print(f"\nBatch complete. {sum(1 for p in report_paths if p)}/{len(urls)} reports generated.")
        return 0

    # Single URL mode
    if not args.target_url:
        parser.print_help()
        return 1

    if not args.quiet:
        print(f"Analyzing {args.target_url}...")
    report_path = _run_single(args.target_url, args)
    if not args.quiet:
        print(f"\n✓ Report saved to: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
