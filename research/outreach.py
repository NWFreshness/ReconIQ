"""Module 6: Outreach Pack — generate ready-to-use sales assets."""
from __future__ import annotations

import json
from typing import Any

from research.parsing import JSON_RESPONSE_RULES, llm_json_call
from research.schemas import OutreachPackSchema, validate_module_output

SYSTEM_PROMPT = (
    "You are a senior B2B sales strategist for a local AI automation agency. "
    "Use the provided ReconIQ intelligence to generate practical, copy-ready outreach assets. "
    "Keep the tone consultative, specific, and useful; do not exaggerate unsupported claims. "
    "Return a JSON object with:\n\n"
    "- cold_email: a concise cold email with a subject line and clear CTA\n"
    "- linkedin_dm: a short LinkedIn direct message under 500 characters\n"
    "- discovery_call_opener: a natural 1-2 sentence opener for a sales discovery call\n"
    "- proposal_outline: a one-page proposal outline with recommended sections and deliverables\n"
    "- follow_up_sequence: list of 3-5 concise follow-up messages or angles\n"
    "- data_confidence: 'low', 'medium', or 'high' with brief rationale\n"
    "- data_limitations: list of caveats about inferred claims, incomplete data, or missing evidence\n\n"
    "Ground every asset in the supplied company profile, SEO, competitor, social/content, and SWOT data. "
    "If a detail is inferred, phrase it cautiously.\n\n"
    f"{JSON_RESPONSE_RULES}"
)

REQUIRED_KEYS = [
    "cold_email",
    "linkedin_dm",
    "discovery_call_opener",
    "proposal_outline",
    "follow_up_sequence",
    "data_confidence",
    "data_limitations",
]


def run(
    company_profile: dict[str, Any],
    seo_keywords: dict[str, Any],
    competitor: dict[str, Any],
    social_content: dict[str, Any],
    swot: dict[str, Any],
    target_url: str,
    llm_complete,
) -> dict[str, Any]:
    """Generate a copy-ready outreach pack from completed research outputs."""
    prompt = (
        f"TARGET URL: {target_url}\n\n"
        f"--- COMPANY PROFILE ---\n{_format_dict(company_profile)}\n\n"
        f"--- SEO & KEYWORDS ---\n{_format_dict(seo_keywords)}\n\n"
        f"--- COMPETITOR INTELLIGENCE ---\n{_format_dict(competitor)}\n\n"
        f"--- SOCIAL & CONTENT ---\n{_format_dict(social_content)}\n\n"
        f"--- SWOT & ACQUISITION STRATEGY ---\n{_format_dict(swot)}\n\n"
        "Generate the outreach pack as instructed."
    )

    data = llm_json_call(
        llm_complete=llm_complete,
        prompt=prompt,
        module="outreach",
        system=SYSTEM_PROMPT,
        required_keys=REQUIRED_KEYS,
        context="outreach pack",
        max_tokens=2200,
    )

    return validate_module_output(data, OutreachPackSchema, "outreach pack")


def _format_dict(data: dict[str, Any]) -> str:
    """Format nested module output for prompt consumption."""
    lines: list[str] = []
    for key, value in data.items():
        if key in ("error", "raw_error"):
            continue
        if isinstance(value, list):
            lines.append(f"- {key}:")
            for item in value:
                if isinstance(item, dict):
                    lines.append(f"  - {json.dumps(item, sort_keys=True)}")
                else:
                    lines.append(f"  - {item}")
        elif isinstance(value, dict):
            lines.append(f"- {key}:")
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, (dict, list)):
                    lines.append(f"  - {sub_key}: {json.dumps(sub_value, sort_keys=True)}")
                else:
                    lines.append(f"  - {sub_key}: {sub_value}")
        else:
            lines.append(f"- {key}: {value}")
    return "\n".join(lines)
