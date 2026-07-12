"""Module 2: SEO & Keywords — analyze search presence and content gaps."""
from __future__ import annotations

import re
from typing import Any

from scraper.models import ScrapeResult
from research.parsing import JSON_RESPONSE_RULES, llm_json_call
from research.schemas import SEOKeywordsSchema, validate_module_output
from research.scrape_context import format_seo_context
from research.evidence import attach_evidence, collect_scrape_evidence

SYSTEM_PROMPT = (
    "You are an expert SEO analyst. Based on the provided company profile, target URL, "
    "and any MEASURED SEED KEYWORDS extracted from the live site scrape, synthesize the "
    "company's SEO landscape.\n"
    "Return a JSON object with:\n"
    "- top_keywords: 8-12 organic search terms — prefer/include measured seed keywords "
    "when provided; do NOT claim the company 'ranks for' these unless measured ranking "
    "evidence is in the prompt (it is not)\n"
    "- content_gaps: 4-6 keyword areas they likely do NOT target well\n"
    "- seo_weaknesses: 4-5 specific weaknesses (technical, content, or backlink)\n"
    "- quick_wins: 3-4 SEO improvements they could make with moderate effort\n"
    "- estimated_traffic_tier: 'low', 'medium', or 'high' — PURE INFERENCE / low confidence "
    "only; never invent visit counts or growth percentages\n"
    "- local_seo_signals: 'strong', 'moderate', or 'weak' (Google Business Profile, local keywords)\n"
    "- data_confidence: 'low', 'medium', or 'high' with brief rationale\n"
    "- data_limitations: list of caveats; explicitly state that keyword/traffic/ranking claims "
    "are inferred unless backed by provided measured data\n\n"
    "HARD RULES:\n"
    "- Do NOT invent search volume, rankings, SERP positions, backlink counts, or traffic numbers.\n"
    "- Do NOT claim the site 'ranks for' keywords without measured ranking evidence (none is provided).\n"
    "- measured seed keywords are on-page phrases only — not proof of ranking or volume.\n"
    f"{JSON_RESPONSE_RULES}"
)

REQUIRED_KEYS = [
    "top_keywords", "content_gaps", "seo_weaknesses", "quick_wins",
    "estimated_traffic_tier", "local_seo_signals", "data_confidence", "data_limitations",
]

_MAX_SEEDS = 25

_STOP_ANCHORS = frozenset({
    "click here",
    "home",
    "contact",
    "contact us",
    "login",
    "log in",
    "sign in",
    "sign up",
    "register",
    "read more",
    "learn more",
    "about",
    "about us",
    "privacy",
    "privacy policy",
    "terms",
    "terms of service",
    "menu",
    "skip to content",
    "here",
    "more",
    "next",
    "previous",
    "submit",
    "buy now",
    "shop",
    "cart",
})

_INFERRED_ONLY_LIMITATION = (
    "No measured on-page keyword seeds extracted; keyword and traffic claims are pure "
    "LLM inference without ranking/SERP/traffic data."
)
_HYBRID_LIMITATION = (
    "Seed keywords are measured from on-page scrape; search volumes, rankings, and traffic "
    "estimates are inferred only (no SERP or traffic API)."
)


def extract_keyword_seeds(scrape_result: ScrapeResult | None) -> list[dict[str, str]]:
    """Extract measured on-page keyword seed phrases from a structured scrape.

    Each seed is ``{\"keyword\": str, \"source\": str}`` with source one of:
    title, h1, h2, meta_keywords, meta_description, internal_link,
    subpage_title, subpage_h1.
    """
    if scrape_result is None:
        return []

    seeds: list[dict[str, str]] = []
    seen: set[str] = set()

    def add(text: str, source: str, *, min_len: int = 1, max_len: int = 120) -> None:
        if len(seeds) >= _MAX_SEEDS:
            return
        cleaned = " ".join((text or "").split()).strip()
        if not cleaned or len(cleaned) < min_len or len(cleaned) > max_len:
            return
        key = cleaned.lower()
        if key in seen:
            return
        seen.add(key)
        # Prefer first-seen casing (readable original)
        seeds.append({"keyword": cleaned, "source": source})

    if scrape_result.title:
        add(scrape_result.title, "title")

    headings = scrape_result.headings or {}
    for h1 in headings.get("h1", []) or []:
        add(h1, "h1")
    for h2 in headings.get("h2", []) or []:
        add(h2, "h2")

    for kw in scrape_result.meta_keywords or []:
        add(kw, "meta_keywords")

    desc = (scrape_result.meta_description or "").strip()
    if desc:
        cleaned_desc = " ".join(desc.split()).strip()
        if len(cleaned_desc) <= 80:
            add(cleaned_desc, "meta_description")
        else:
            parts = re.split(r"[|.•–—;]|\s+-\s+", cleaned_desc)
            for part in parts:
                add(part.strip(), "meta_description", min_len=3, max_len=60)

    for link in scrape_result.internal_links or []:
        text = " ".join((link.text or "").split()).strip()
        if not text:
            continue
        if text.lower() in _STOP_ANCHORS:
            continue
        add(text, "internal_link", min_len=3, max_len=60)

    for page in scrape_result.pages or []:
        if page.title:
            add(page.title, "subpage_title")
        page_headings = page.headings or {}
        for h1 in page_headings.get("h1", []) or []:
            add(h1, "subpage_h1")

    return seeds[:_MAX_SEEDS]


def _format_seed_block(seeds: list[dict[str, str]]) -> str:
    if not seeds:
        return "MEASURED SEED KEYWORDS: (none — scrape empty or unavailable)"
    lines = ["MEASURED SEED KEYWORDS (on-page only; not rankings or volumes):"]
    for seed in seeds:
        lines.append(f"- [{seed['source']}] {seed['keyword']}")
    return "\n".join(lines)


def _ensure_data_limitation(data: dict[str, Any], caveat: str) -> None:
    limitations = data.get("data_limitations")
    if not isinstance(limitations, list):
        limitations = [] if limitations is None else [str(limitations)]
        data["data_limitations"] = limitations
    # Exact (case-insensitive) match only — hybrid vs inferred_only must both be allowed
    caveat_key = caveat.lower()
    for item in limitations:
        if isinstance(item, str) and item.lower() == caveat_key:
            return
    limitations.append(caveat)


def run(
    company_profile: dict,
    target_url: str,
    llm_complete,
    scrape_result: ScrapeResult | None = None,
) -> dict:
    seeds = extract_keyword_seeds(scrape_result)
    data_mode = "hybrid" if seeds else "inferred_only"

    profile_text = "\n".join(f"- {k}: {v}" for k, v in company_profile.items() if k != "error")
    parts = [f"TARGET URL: {target_url}", f"COMPANY PROFILE:\n{profile_text}"]
    if scrape_result is not None:
        parts.append("REAL ON-PAGE SEO SIGNALS:\n" + format_seo_context(scrape_result))
    parts.append(_format_seed_block(seeds))
    prompt = "\n\n".join(parts) + "\n\nInfer the SEO landscape as instructed."

    data = llm_json_call(
        llm_complete=llm_complete,
        prompt=prompt,
        module="seo_keywords",
        system=SYSTEM_PROMPT,
        required_keys=REQUIRED_KEYS,
        context="SEO keywords",
        max_tokens=1200,
    )
    # Inject provenance — never trust the LLM for these fields
    data["seed_keywords"] = seeds
    data["data_mode"] = data_mode
    _ensure_data_limitation(
        data,
        _HYBRID_LIMITATION if data_mode == "hybrid" else _INFERRED_ONLY_LIMITATION,
    )
    attach_evidence(data, collect_scrape_evidence(scrape_result, module="seo_keywords"))
    return validate_module_output(data, SEOKeywordsSchema, "SEO keywords")
