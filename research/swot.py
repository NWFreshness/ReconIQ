"""Module 5: SWOT Synthesis — combine all findings into a strategic acquisition report."""
from __future__ import annotations

import json
import re


SYSTEM_PROMPT = (
    "You are a senior marketing strategist. Synthesize all provided research into a "
    "client acquisition strategy. Return a JSON object with:\n\n"
    "- swot:\n"
    "  - strengths: list of 3-5 internal strengths (what they do well)\n"
    "  - weaknesses: list of 3-5 internal weaknesses (marketing gaps, inefficiencies)\n"
    "  - opportunities: list of 3-5 external opportunities (market gaps, trends they ignore)\n"
    "  - threats: list of 3-5 external threats (competitors, market shifts, risks)\n\n"
    "- acquisition_angle: 2-3 sentence summary of the best way to pitch YOUR agency to them\n"
    "- talking_points: 4-6 specific talking points for outreach (what to say, what to offer)\n"
    "- recommended_next_steps: 3-5 specific tactical actions (email sequence, content, offer)\n"
    "- competitive_advantage: 1-2 sentences on what you'd offer that their current provider lacks\n"
    "Return ONLY the JSON object, no preamble."
)


def run(
    company_profile: dict,
    seo_keywords: dict,
    competitor: dict,
    social_content: dict,
    target_url: str,
    llm_complete,
) -> dict:
    """
    Run the SWOT synthesis module.

    Args:
        company_profile: Output from Module 1.
        seo_keywords: Output from Module 2.
        competitor: Output from Module 3.
        social_content: Output from Module 4.
        target_url: Original target URL.
        llm_complete: LLM completion callable.

    Returns:
        Dict with SWOT and acquisition strategy fields.
    """
    prompt = (
        f"TARGET URL: {target_url}\n\n"
        f"--- COMPANY PROFILE ---\n{_format_dict(company_profile)}\n\n"
        f"--- SEO & KEYWORDS ---\n{_format_dict(seo_keywords)}\n\n"
        f"--- COMPETITOR INTELLIGENCE ---\n{_format_dict(competitor)}\n\n"
        f"--- SOCIAL & CONTENT ---\n{_format_dict(social_content)}\n\n"
        f"Synthesize into an acquisition strategy as instructed."
    )

    raw = llm_complete(prompt, module="swot", system=SYSTEM_PROMPT, max_tokens=2000)
    return _parse_response(raw)


def _format_dict(d: dict) -> str:
    """Format a dict for prompt consumption, handling nested structures."""
    lines = []
    for k, v in d.items():
        if k in ("error", "raw_error"):
            continue
        if isinstance(v, list):
            lines.append(f"- {k}:")
            for item in v:
                if isinstance(item, dict):
                    lines.append(f"  - {json.dumps(item)}")
                else:
                    lines.append(f"  - {item}")
        elif isinstance(v, dict):
            lines.append(f"- {k}:")
            for sub_k, sub_v in v.items():
                lines.append(f"  - {sub_k}: {sub_v}")
        else:
            lines.append(f"- {k}: {v}")
    return "\n".join(lines)


def _parse_response(raw: str) -> dict:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    result = {}
    for line in raw.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            result[key.strip().lower().replace(" ", "_")] = val.strip()
    return result if result else {"error": raw}