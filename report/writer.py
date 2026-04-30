"""Report Writer — convert research results into a Markdown report."""
from __future__ import annotations

import os
import re
import time
from pathlib import Path


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