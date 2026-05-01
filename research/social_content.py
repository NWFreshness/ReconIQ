"""Module 4: Social & Content — infer social presence and content quality."""
from __future__ import annotations

from scraper.models import ScrapeResult
from research.parsing import JSON_RESPONSE_RULES, llm_json_call
from research.schemas import SocialContentSchema, validate_module_output
from research.scrape_context import format_social_context

SYSTEM_PROMPT = (
    "You are a content and social media analyst. Based on the company profile and target URL, "
    "infer their social media presence and content strategy. Return a JSON object with:\n"
    "- platforms: list of social platforms they likely use (e.g. LinkedIn, Facebook, Instagram, Twitter/X)\n"
    "- verified_social_accounts: list of objects with platform and url for each account discovered from the site HTML\n"
    "- inferred_platforms: list of platforms they likely use but could not be verified from the site\n"
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
    "platforms", "verified_social_accounts", "inferred_platforms", "content_quality",
    "content_frequency", "engagement_signals", "review_sites", "blog_or_resources",
    "content_gaps", "email_signals", "data_confidence", "data_limitations",
]


def run(company_profile: dict, target_url: str, llm_complete, scrape_result: ScrapeResult | None = None) -> dict:
    profile_text = "\n".join(f"- {k}: {v}" for k, v in company_profile.items() if k != "error")
    parts = [f"TARGET URL: {target_url}", f"COMPANY PROFILE:\n{profile_text}"]
    if scrape_result is not None:
        parts.append("SOCIAL DISCOVERY FROM SITE:\n" + format_social_context(scrape_result))
    prompt = "\n\n".join(parts) + "\n\nAnalyze social and content presence as instructed."

    data = llm_json_call(
        llm_complete=llm_complete,
        prompt=prompt,
        module="social_content",
        system=SYSTEM_PROMPT,
        required_keys=REQUIRED_KEYS,
        context="social content",
        max_tokens=1200,
    )
    return validate_module_output(data, SocialContentSchema, "social content")
