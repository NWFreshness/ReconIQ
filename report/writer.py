"""Report Writer — convert research results into Markdown, HTML, or PDF reports."""
from __future__ import annotations

import os
import re
import time
from pathlib import Path

from markdown import markdown as md_to_html


def write_report(results: dict, output_dir: str = "reports") -> str:
    """
    Convert research results dict into a formatted Markdown report.

    Args:
        results: Output from coordinator.run_all().
        output_dir: Base directory for reports.

    Returns:
        Absolute path to the written report file.
    """
    company_name = _infer_company_name(results.get("company_profile", {}))
    slug = re.sub(r"[^a-z0-9]+", "-", company_name.lower()).strip("-")
    timestamp = time.strftime("%Y-%m-%d-%H%M%S")

    report_dir = Path(os.path.expanduser(output_dir)) / slug
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{timestamp}.md"

    content = _build_markdown(results, company_name)
    report_path.write_text(content, encoding="utf-8")

    return str(report_path)


def _infer_company_name(profile: dict) -> str:
    name = profile.get("company_name", "Unknown Company")
    return str(name) if name is not None else "Unknown Company"


def _section_content(d: dict) -> str:
    """Render a flat module dict as readable Markdown."""
    if not d or d.get("error"):
        return "*Module did not return data.*"

    lines = []
    for k, v in d.items():
        if k in ("error", "raw_error"):
            continue
        display_key = k.replace("_", " ").title()
        if isinstance(v, list):
            lines.append(f"**{display_key}:**")
            for item in v:
                lines.append(f"- {item}")
            lines.append("")
        elif isinstance(v, dict):
            lines.append(f"**{display_key}:**")
            for sub_k, sub_v in v.items():
                lines.append(f"- **{sub_k.replace('_', ' ').title()}:** {sub_v}")
            lines.append("")
        else:
            lines.append(f"**{display_key}:** {v}")
    return "\n".join(lines).strip()


def _competitor_section(competitor: dict) -> str:
    competitors = competitor.get("competitors", [])
    if not competitors:
        return "*No competitor data available.*"

    lines = []
    for i, comp in enumerate(competitors, 1):
        if isinstance(comp, dict):
            lines.append(f"### {i}. {comp.get('name', 'Unknown Competitor')}")
            for k, v in comp.items():
                if k not in ("name",):
                    display_k = k.replace("_", " ").title()
                    if isinstance(v, list):
                        lines.append(f"- **{display_k}:** {', '.join(str(i) for i in v)}")
                    else:
                        lines.append(f"- **{display_k}:** {v}")
            lines.append("")
        else:
            lines.append(f"- {comp}")
    return "\n".join(lines).strip()


def _swot_section(swot: dict) -> str:
    sw = swot.get("swot", swot)
    if not sw:
        return "*SWOT data not available.*"

    def format_items(items):
        if isinstance(items, list):
            return "\n".join(f"- {i}" for i in items)
        return str(items)

    lines = [
        "### Strengths (Internal, Helpful)",
        format_items(sw.get("strengths", ["—"])),
        "",
        "### Weaknesses (Internal, Harmful)",
        format_items(sw.get("weaknesses", ["—"])),
        "",
        "### Opportunities (External, Helpful)",
        format_items(sw.get("opportunities", ["—"])),
        "",
        "### Threats (External, Harmful)",
        format_items(sw.get("threats", ["—"])),
    ]
    return "\n".join(lines)


def _acquisition_section(swot: dict) -> str:
    sections = []
    angle = swot.get("acquisition_angle")
    if angle:
        sections.append(f"**Recommended Angle:** {angle}")
    advantage = swot.get("competitive_advantage")
    if advantage:
        sections.append(f"**Your Competitive Edge:** {advantage}")
    lead_gen = swot.get("lead_generation_strategy")
    if lead_gen:
        sections.append(f"**Lead Generation Strategy:** {lead_gen}")
    close_rate = swot.get("close_rate_strategy")
    if close_rate:
        sections.append(f"**AI Close Rate Strategy:** {close_rate}")
    points = swot.get("talking_points", [])
    if points:
        sections.append("**Talking Points:**")
        for p in points:
            sections.append(f"- {p}")
    return "\n\n".join(sections) if sections else "*No acquisition data available.*"


def _next_steps_section(swot: dict) -> str:
    steps = swot.get("recommended_next_steps", [])
    if not steps:
        return "*No next steps available.*"
    return "\n".join(f"{i}. {s}" for i, s in enumerate(steps, 1))


def _build_markdown(results: dict, company_name: str) -> str:
    meta = results.get("metadata", {})
    target_url = meta.get("target_url", "Unknown URL")
    timestamp = meta.get("timestamp", time.strftime("%Y-%m-%d %H:%M:%S"))

    profile = results.get("company_profile", {})
    seo = results.get("seo_keywords", {})
    competitor = results.get("competitor", {})
    social = results.get("social_content", {})
    swot = results.get("swot", {})

    modules_run = ", ".join(meta.get("modules_run", [])) or "None"
    modules_skipped = ", ".join(meta.get("modules_skipped", [])) or "None"
    modules_failed = ", ".join(meta.get("modules_failed", [])) or "None"
    data_limitations = meta.get("data_limitations", [])

    lines = [
        f"# ReconIQ Report: {company_name}",
        "",
        f"**Target URL:** {target_url}",
        f"**Generated:** {timestamp}",
        f"**Modules Run:** {modules_run}",
        f"**Skipped:** {modules_skipped}",
        f"**Failed:** {modules_failed}",
        "",
        "---",
        "",
        "## Metadata",
        "",
        f"**Data Limitations:** {', '.join(data_limitations) or 'None recorded'}",
        "",
        "---",
        "",
        "## 1. Company Overview",
        "",
        _section_content(profile),
        "",
        "---",
        "",
        "## 2. SEO & Keyword Analysis",
        "",
        _section_content(seo),
        "",
        "---",
        "",
        "## 3. Competitor Landscape",
        "",
        _competitor_section(competitor),
        "",
        "---",
        "",
        "## 4. Social & Content Audit",
        "",
        _section_content(social),
        "",
        "---",
        "",
        "## 5. SWOT Analysis",
        "",
        _swot_section(swot),
        "",
        "---",
        "",
        "## 6. Client Acquisition Strategy",
        "",
        _acquisition_section(swot),
        "",
        "---",
        "",
        "## 7. Next Steps",
        "",
        _next_steps_section(swot),
        "",
        f"---\n*Report generated by ReconIQ | {timestamp}*",
    ]

    return "\n".join(lines)


# ── Export helpers ──────────────────────────────────────────────────────────────────────────────

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.6;
    max-width: 900px;
    margin: 2rem auto;
    padding: 0 1.5rem;
    color: #1a1a1a;
    background: #ffffff;
}}
h1 {{ color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.5rem; }}
h2 {{ color: #1e293b; margin-top: 2rem; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.3rem; }}
h3 {{ color: #334155; margin-top: 1.5rem; }}
strong {{ color: #0f172a; }}
hr {{ border: none; border-top: 1px solid #e2e8f0; margin: 2rem 0; }}
ul {{ padding-left: 1.5rem; }}
li {{ margin: 0.25rem 0; }}
pre {{ background: #f8fafc; padding: 1rem; border-radius: 0.5rem; overflow-x: auto; }}
code {{ background: #f1f5f9; padding: 0.15rem 0.35rem; border-radius: 0.25rem; font-size: 0.9em; }}
footer {{ margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #e2e8f0; color: #64748b; font-size: 0.85rem; }}
@media print {{
    body {{ margin: 0; padding: 1rem; }}
    h1, h2, h3 {{ page-break-after: avoid; }}
}}
</style>
</head>
<body>
{body}
<footer>Report generated by ReconIQ — {timestamp}</footer>
</body>
</html>
"""


def write_html_report(markdown_content: str, output_path: Path, title: str = "ReconIQ Report") -> str:
    """Convert Markdown content to HTML and write to disk.

    Returns the absolute path to the written HTML file.
    """
    body_html = md_to_html(markdown_content, extensions=["tables", "fenced_code"])
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    html = HTML_TEMPLATE.format(title=title, body=body_html, timestamp=timestamp)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return str(output_path)


def write_pdf_report(markdown_content: str, output_path: Path, title: str = "ReconIQ Report") -> str:
    """Convert Markdown content to PDF and write to disk.

    Returns the absolute path to the written PDF file.
    """
    body_html = md_to_html(markdown_content, extensions=["tables", "fenced_code"])
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    html = HTML_TEMPLATE.format(title=title, body=body_html, timestamp=timestamp)

    # Lazy import weasyprint to keep it off the critical path
    from weasyprint import HTML  # type: ignore[import-untyped]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html, base_url="").write_pdf(str(output_path))
    return str(output_path)


def write_report(results: dict, output_dir: str = "reports", fmt: str = "md") -> str:
    """
    Convert research results dict into a formatted report.

    Args:
        results: Output from coordinator.run_all().
        output_dir: Base directory for reports.
        fmt: Export format — "md", "html", or "pdf".

    Returns:
        Absolute path to the written report file.
    """
    company_name = _infer_company_name(results.get("company_profile", {}))
    slug = re.sub(r"[^a-z0-9]+", "-", company_name.lower()).strip("-")
    timestamp = time.strftime("%Y-%m-%d-%H%M%S")

    report_dir = Path(os.path.expanduser(output_dir)) / slug
    report_dir.mkdir(parents=True, exist_ok=True)

    markdown_content = _build_markdown(results, company_name)

    if fmt == "html":
        report_path = report_dir / f"{timestamp}.html"
        return write_html_report(markdown_content, report_path, title=f"ReconIQ Report: {company_name}")
    elif fmt == "pdf":
        report_path = report_dir / f"{timestamp}.pdf"
        return write_pdf_report(markdown_content, report_path, title=f"ReconIQ Report: {company_name}")
    else:
        report_path = report_dir / f"{timestamp}.md"
        report_path.write_text(markdown_content, encoding="utf-8")
        return str(report_path)