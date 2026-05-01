"""Module 4: Social & Content — report only verified social presence from scraped links and search."""
from __future__ import annotations

from scraper.models import ScrapeResult
from research.parsing import JSON_RESPONSE_RULES, llm_json_call
from research.schemas import SocialContentSchema, validate_module_output
from research.scrape_context import format_social_context
from research.search import discover_social_accounts

SYSTEM_PROMPT = (
    "You are a content and social media analyst. Based ONLY on verified evidence from the company's website "
    "and search results, report their social media presence and content strategy. Do NOT infer or guess. "
    "Return a JSON object with:\n"
    "- platforms: list of social platforms with VERIFIED links (e.g. LinkedIn, Facebook, Instagram, Twitter/X)\n"
    "- verified_social_accounts: list of objects with platform and url for each account discovered from the site HTML or search\n"
    "- content_quality: 'low', 'moderate', or 'high' based on visible site content quality\n"
    "- content_frequency: 'sporadic', 'consistent', or 'heavy' based on blog/post dates if visible\n"
    "- engagement_signals: 'weak', 'moderate', or 'strong' based on visible reviews/testimonials\n"
    "- review_sites: list of review platforms with verified links found on the site\n"
    "- blog_or_resources: 'yes' or 'no' — do they have a blog or resource center visible on the site\n"
    "- content_gaps: 3-4 types of content they visibly don't produce well\n"
    "- email_signals: 'prominent', 'present', or 'minimal' — how visible are email CTAs on the site\n"
    "- data_confidence: 'low', 'medium', or 'high' with brief rationale\n"
    "- data_limitations: list of caveats; explicitly state when social accounts could not be verified\n\n"
    f"{JSON_RESPONSE_RULES}"
)

REQUIRED_KEYS = [
    "platforms", "verified_social_accounts", "content_quality",
    "content_frequency", "engagement_signals", "review_sites", "blog_or_resources",
    "content_gaps", "email_signals", "data_confidence", "data_limitations",
]


def run(company_profile: dict, target_url: str, llm_complete, scrape_result: ScrapeResult | None = None) -> dict:
    profile_text = "\n".join(f"- {k}: {v}" for k, v in company_profile.items() if k != "error")
    parts = [f"TARGET URL: {target_url}", f"COMPANY PROFILE:\n{profile_text}"]

    verified_accounts: list[dict] = []
    search_limitations: list[str] = []

    if scrape_result is not None:
        parts.append("VERIFIED SOCIAL LINKS DISCOVERED FROM SITE HTML:\n" + format_social_context(scrape_result))
        # Build verified list from scraped links
        for link in scrape_result.social_links:
            verified_accounts.append({"platform": link.platform, "url": link.url})

    # Also try to verify via search for any platforms not found in scrape
    company_name = company_profile.get("company_name", "")
    search_results = discover_social_accounts(company_name, target_url)
    for acct in search_results.get("accounts", []):
        # Only add if not already in verified list
        if not any(a["url"] == acct["url"] for a in verified_accounts):
            verified_accounts.append(acct)
    search_limitations.extend(search_results.get("data_limitations", []))

    prompt = "\n\n".join(parts) + "\n\nReport ONLY verified social and content signals. Do not infer or guess."

    data = llm_json_call(
        llm_complete=llm_complete,
        prompt=prompt,
        module="social_content",
        system=SYSTEM_PROMPT,
        required_keys=REQUIRED_KEYS,
        context="social content",
        max_tokens=1200,
    )

    # Override with our verified accounts — don't let LLM hallucinate
    data["verified_social_accounts"] = verified_accounts
    data["platforms"] = list({a["platform"] for a in verified_accounts})

    limitations = data.setdefault("data_limitations", [])
    for lim in search_limitations:
        if lim and lim not in limitations:
            limitations.append(lim)
    if not verified_accounts:
        msg = "No verified social media accounts were found on the website or via search."
        if msg not in limitations:
            limitations.append(msg)
    if not data.get("platforms"):
        data["platforms"] = sorted({a["platform"] for a in verified_accounts})

    return validate_module_output(data, SocialContentSchema, "social content")
