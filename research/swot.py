"""Module 5: SWOT Synthesis — combine all findings into a strategic acquisition report."""
from __future__ import annotations

import json

from research.parsing import JSON_RESPONSE_RULES, llm_json_call
from research.schemas import SWOTSchema, validate_module_output

SYSTEM_PROMPT = (
    "You are a senior marketing strategist at an AI automation agency. Synthesize all provided research into a "
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
    "- lead_generation_strategy: 2-3 sentences on how to generate qualified leads for this prospect (channels, hooks, offer types)\n"
    "- close_rate_strategy: 2-3 sentences on how AI-powered processes can increase their close rate. Focus on specific "
    "AI tactics such as: AI lead scoring to prioritize high-intent prospects, automated follow-up sequences triggered by "
    "behavior signals, AI chatbots for instant objection handling and 24/7 lead qualification, predictive analytics to "
    "identify deals most likely to close, AI-generated personalized proposals, or dynamic pricing optimization. Tailor "
    "the recommendation to what fits this prospect's weaknesses and opportunities.\n"
    "- data_confidence: 'low', 'medium', or 'high' with brief rationale\n"
    "- data_limitations: list of caveats about inferred strategy or incomplete module data\n\n"
    f"{JSON_RESPONSE_RULES}"
)

REQUIRED_KEYS = [
    "swot",
    "acquisition_angle",
    "talking_points",
    "recommended_next_steps",
    "competitive_advantage",
    "lead_generation_strategy",
    "close_rate_strategy",
    "data_confidence",
    "data_limitations",
]
REQUIRED_SWOT_KEYS = ["strengths", "weaknesses", "opportunities", "threats"]


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

    data = llm_json_call(
        llm_complete=llm_complete,
        prompt=prompt,
        module="swot",
        system=SYSTEM_PROMPT,
        required_keys=REQUIRED_KEYS,
        context="SWOT synthesis",
        max_tokens=2000,
    )

    return validate_module_output(data, SWOTSchema, "SWOT synthesis")


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