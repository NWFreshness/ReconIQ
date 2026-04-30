"""Module 4: Social & Content — infer social presence and content quality."""
from __future__ import annotations

from research.parsing import JSON_RESPONSE_RULES, extract_json_object, require_keys


SYSTEM_PROMPT = (
    "You are a content and social media analyst. Based on the company profile and target URL, "
    "infer their social media presence and content strategy. Return a JSON object with:\n"
    "- platforms: list of social platforms they likely use (e.g. LinkedIn, Facebook, Instagram, Twitter/X)\n"
    "- content_quality: 'low', 'moderate', or 'high' with 1-sentence explanation\n"
    "- content_frequency: 'sporadic', 'consistent', or 'heavy' publishing cadence\n"
    "- engagement_signals: 'weak', 'moderate', or 'strong' (likes, comments, shares)\n"
    "- review_sites: list of review platforms they likely appear on (Google, Yelp, Trustpilot, etc.)\n"
    "- blog_or_resources: 'yes' or 'no' — do they maintain a blog or resource center\n"
    "- content_gaps: 3-4 types of content they likely don't produce well\n"
    "- email_signals: 'prominent', 'present', or 'minimal' — how visible is their email list/CTAs\n"
    "- data_confidence: 'low', 'medium', or 'high' with brief rationale\n"
    "- data_limitations: list of caveats; explicitly label inferred social/content signals\n\n"
    f"{JSON_RESPONSE_RULES}"
)

REQUIRED_KEYS = [
    "platforms",
    "content_quality",
    "content_frequency",
    "engagement_signals",
    "review_sites",
    "blog_or_resources",
    "content_gaps",
    "email_signals",
    "data_confidence",
    "data_limitations",
]


def run(company_profile: dict, target_url: str, llm_complete) -> dict:
    """
    Run the social & content module.

    Args:
        company_profile: Output from Module 1.
        target_url: Original target URL.
        llm_complete: LLM completion callable.

    Returns:
        Dict with social/content analysis fields.
    """
    profile_text = "\n".join(f"- {k}: {v}" for k, v in company_profile.items() if k != "error")

    prompt = (
        f"TARGET URL: {target_url}\n"
        f"COMPANY PROFILE:\n{profile_text}\n\n"
        f"Analyze social and content presence as instructed."
    )

    raw = llm_complete(prompt, module="social_content", system=SYSTEM_PROMPT, max_tokens=1200)
    return _parse_response(raw)


def _parse_response(raw: str) -> dict:
    data = extract_json_object(raw)
    return require_keys(data, REQUIRED_KEYS, context="social content")
