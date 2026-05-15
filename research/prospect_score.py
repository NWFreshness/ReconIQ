"""Pure deterministic prospect scoring from module outputs.

Scores analyzed companies by agency opportunity quality using a rubric
based entirely on structured data already extracted by other modules.
No additional LLM calls are needed for the base score.

Score dimensions (0-100 each):
- marketing_gap_severity: How poor is their digital presence?
- ai_automation_fit: How much could they benefit from AI?
- local_relevance: How well do they fit the target local market?
- likely_budget: Estimated revenue/budget tier
- outreach_ease: How easy is it to contact decision-makers?
- urgency_signals: Indicators they may need help soon
- data_confidence: How reliable is the underlying data?

Weighted final score:
  marketing_gap_severity: 25%
  ai_automation_fit:       25%
  local_relevance:         10%
  likely_budget:           15%
  outreach_ease:           10%
  urgency_signals:         10%
  data_confidence:          5% (modifier, not a primary driver)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProspectScore:
    """Deterministic prospect scoring result."""

    overall: float = 0.0  # 0-100 weighted final score
    marketing_gap_severity: float = 0.0
    ai_automation_fit: float = 0.0
    local_relevance: float = 0.0
    likely_budget: float = 0.0
    outreach_ease: float = 0.0
    urgency_signals: float = 0.0
    data_confidence: float = 0.0
    grade: str = ""  # "A+", "A", "B+", "B", "C+", "C", "D", "F"
    summary: str = ""
    breakdown: list[str] = field(default_factory=list)


# ── Weight configuration ─────────────────────────────────────────────────────

WEIGHTS = {
    "marketing_gap_severity": 0.25,
    "ai_automation_fit": 0.25,
    "local_relevance": 0.10,
    "likely_budget": 0.15,
    "outreach_ease": 0.10,
    "urgency_signals": 0.10,
    "data_confidence": 0.05,  # modifier only
}

assert sum(WEIGHTS.values()) == 1.0, "Weights must sum to 1.0"


def grade_from_score(score: float) -> str:
    """Map a 0-100 score to a letter grade."""
    if score >= 90:
        return "A+"
    if score >= 80:
        return "A"
    if score >= 70:
        return "B+"
    if score >= 60:
        return "B"
    if score >= 50:
        return "C+"
    if score >= 40:
        return "C"
    if score >= 25:
        return "D"
    return "F"


def score_marketing_gap(profile: dict[str, Any], seo: dict[str, Any], social: dict[str, Any]) -> float:
    """Score 0-100 based on severity of marketing gaps.
    
    Higher = worse gaps = better opportunity for the agency.
    """
    points = 0.0

    # SEO weaknesses (each adds points, max ~40)
    seo_weaknesses = seo.get("seo_weaknesses", []) or []
    points += min(len(seo_weaknesses) * 8, 40)

    # Content gaps (each adds points, max ~20)
    content_gaps = seo.get("content_gaps", []) or []
    points += min(len(content_gaps) * 5, 20)

    # Missing social platforms (max ~15)
    social_platforms = social.get("platforms", []) or []
    if not social_platforms or len(social_platforms) < 2:
        points += 15
    elif len(social_platforms) < 3:
        points += 8

    # Weak engagement signals (max ~15)
    engagement = social.get("engagement_signals", "")
    if engagement and engagement.lower() in ("weak", "none", "low"):
        points += 15
    elif engagement and engagement.lower() in ("moderate", "sporadic"):
        points += 8

    # No blog or resources (max ~10)
    blog = social.get("blog_or_resources", "")
    if blog and blog.lower() in ("no", "none", ""):
        points += 10

    return min(points, 100)


def score_ai_fit(
    profile: dict[str, Any], social: dict[str, Any], swot: dict[str, Any]
) -> float:
    """Score 0-100 based on how well AI automation fits this company.
    
    Higher = better fit for AI automation services.
    """
    points = 0.0

    # No online ordering/delivery apparent
    brand_voice = profile.get("brand_voice", "")
    if isinstance(brand_voice, list):
        brand_voice = " ".join(brand_voice)
    services = profile.get("services_products", []) or []
    services_text = " ".join(services).lower()
    if "online order" not in services_text and "delivery" not in services_text and "ecommerce" not in services_text:
        points += 25

    # No email marketing / lead capture
    email_signals = social.get("email_signals", "")
    if email_signals and email_signals.lower() in ("absent", "none", "no"):
        points += 20
    elif email_signals and email_signals.lower() in ("present",):
        points += 10  # Has it but likely not automated

    # SWOT weaknesses mention automation/digital gaps
    swot_data = swot.get("swot", {}) if isinstance(swot.get("swot"), dict) else {}
    weaknesses = swot_data.get("weaknesses", []) or []
    weaknesses_text = " ".join(weaknesses).lower()
    automation_keywords = ["online", "automat", "digital", "ordering", "crm", "email", "social", "website", "seo"]
    for kw in automation_keywords:
        if kw in weaknesses_text:
            points += 5
    points = min(points, 50)  # cap at 50 for this dimension

    # Marketing channels are limited (relying on foot traffic / in-person)
    channels = profile.get("marketing_channels", []) or []
    channels_lower = [c.lower() for c in channels]
    if "in-person" in channels_lower or "foot traffic" in channels_lower:
        points += 15
    if len(channels) <= 2:
        points += 10

    # Content frequency is poor (needs automated content)
    frequency = social.get("content_frequency", "")
    if frequency and frequency.lower() in ("sporadic", "rare", "none", "inactive"):
        points += 15

    return min(points, 100)


def score_local_relevance(profile: dict[str, Any]) -> float:
    """Score 0-100 based on local market fit.
    
    Higher = better local target (SW Washington / Clark County focus).
    """
    points = 0.0

    # Has a physical location
    city = profile.get("location_city", "") or ""
    state = profile.get("location_state", "") or ""
    if city and state:
        points += 30

    # SW Washington / Clark County bonus
    target_areas = [
        "vancouver", "camas", "washougal", "battle ground", "ridgefield",
        "la center", "yelom", "brush prairie", "hazel dell",
        "felida", "orchards", "minnehaha", "salmon creek",
        "longview", "kelso", "castle rock", "woodland",
    ]
    city_lower = city.lower()
    for area in target_areas:
        if area in city_lower:
            points += 40
            break

    # Has a service area defined
    service_area = profile.get("service_area", []) or []
    if service_area and len(service_area) > 0:
        points += 15

    # WA state at minimum
    if state.upper() == "WA":
        points += 15

    return min(points, 100)


def score_likely_budget(profile: dict[str, Any]) -> float:
    """Score 0-100 based on estimated budget capacity.
    
    Higher = likely has budget for agency services.
    """
    points = 0.0

    # Services/products variety suggests established business
    services = profile.get("services_products", []) or []
    if len(services) >= 3:
        points += 30
    elif len(services) >= 1:
        points += 15

    # Multiple marketing channels suggests they invest in marketing
    channels = profile.get("marketing_channels", []) or []
    if len(channels) >= 3:
        points += 25
    elif len(channels) >= 2:
        points += 15

    # Established business (since date in name or value prop)
    value_prop = profile.get("value_proposition", "") or ""
    if "since" in value_prop.lower() or "est." in value_prop.lower():
        points += 20

    # Physical location suggests real revenue
    city = profile.get("location_city", "") or ""
    if city:
        points += 15

    # Professional email domain
    company_name = profile.get("company_name", "") or ""
    if company_name:
        points += 10

    return min(points, 100)


def score_outreach_ease(profile: dict[str, Any], social: dict[str, Any]) -> float:
    """Score 0-100 based on how easy it is to reach decision-makers.
    
    Higher = easier to contact = better for outreach.
    """
    points = 0.0

    # Has verified social accounts
    social_accounts = social.get("verified_social_accounts", []) or []
    if social_accounts and len(social_accounts) >= 2:
        points += 30
    elif social_accounts and len(social_accounts) >= 1:
        points += 15

    # Has contact info
    # Check various profile fields for contact information
    for field_name in ("company_name", "location_city", "location_state"):
        if profile.get(field_name):
            points += 10

    # Marketing channels include digital
    channels = profile.get("marketing_channels", []) or []
    channels_lower = [c.lower() for c in channels]
    if any(c in channels_lower for c in ("website", "email", "facebook", "instagram", "linkedin")):
        points += 20

    return min(points, 100)


def score_urgency(swot: dict[str, Any], seo: dict[str, Any]) -> float:
    """Score 0-100 based on urgency signals.
    
    Higher = more urgent need for help.
    """
    points = 0.0

    # SWOT threats mention competition or digital disruption
    swot_data = swot.get("swot", {}) if isinstance(swot.get("swot"), dict) else {}
    threats = swot_data.get("threats", []) or []
    threats_text = " ".join(threats).lower()
    urgency_keywords = ["compet", "chains", "cost", "downturn", "disrupt", "decline", "pressure", "rival"]
    for kw in urgency_keywords:
        if kw in threats_text:
            points += 8

    # SEO tier is low (needs help now)
    traffic_tier = seo.get("estimated_traffic_tier", "") or ""
    if isinstance(traffic_tier, dict):
        traffic_tier = traffic_tier.get("tier", "")
    if traffic_tier and traffic_tier.lower() in ("low", "very low"):
        points += 25

    # Weak local SEO signals
    local_seo = seo.get("local_seo_signals", "")
    if local_seo and local_seo.lower() in ("weak", "poor", "low", "none"):
        points += 20

    # SWOT opportunities exist but aren't being pursued
    opportunities = swot_data.get("opportunities", []) or []
    if len(opportunities) >= 3:
        points += 15

    return min(points, 100)


def score_data_confidence(
    profile: dict[str, Any], seo: dict[str, Any], 
    competitor: dict[str, Any], social: dict[str, Any],
    swot: dict[str, Any]
) -> float:
    """Score 0-100 based on how reliable the underlying data is.
    
    Higher = more confident in the analysis = more reliable score.
    This is a modifier, not a primary driver of the overall score.
    """
    points = 0.0

    # Check each module's data_confidence field
    modules = [profile, seo, competitor, social, swot]
    confidence_scores = []
    for m in modules:
        conf = m.get("data_confidence", "")
        if isinstance(conf, dict):
            conf = conf.get("level", conf.get("data_confidence", ""))
        conf_lower = (conf or "").lower()
        if "high" in conf_lower:
            confidence_scores.append(100)
        elif "medium" in conf_lower or "moderate" in conf_lower:
            confidence_scores.append(60)
        elif "low" in conf_lower:
            confidence_scores.append(30)
        else:
            confidence_scores.append(50)  # default unknown

    if confidence_scores:
        points = sum(confidence_scores) / len(confidence_scores)

    return min(max(points, 0), 100)


def compute_prospect_score(
    company_profile: dict[str, Any],
    seo_keywords: dict[str, Any],
    competitor: dict[str, Any],
    social_content: dict[str, Any],
    swot: dict[str, Any],
) -> ProspectScore:
    """Compute a deterministic prospect score from all module outputs."""

    marketing_gap = score_marketing_gap(company_profile, seo_keywords, social_content)
    ai_fit = score_ai_fit(company_profile, social_content, swot)
    local = score_local_relevance(company_profile)
    budget = score_likely_budget(company_profile)
    outreach = score_outreach_ease(company_profile, social_content)
    urgency = score_urgency(swot, seo_keywords)
    confidence = score_data_confidence(
        company_profile, seo_keywords, competitor, social_content, swot
    )

    # Weighted overall score
    overall = (
        marketing_gap * WEIGHTS["marketing_gap_severity"]
        + ai_fit * WEIGHTS["ai_automation_fit"]
        + local * WEIGHTS["local_relevance"]
        + budget * WEIGHTS["likely_budget"]
        + outreach * WEIGHTS["outreach_ease"]
        + urgency * WEIGHTS["urgency_signals"]
        + confidence * WEIGHTS["data_confidence"]
    )

    grade = grade_from_score(overall)

    # Build summary
    summary_parts: list[str] = []
    if marketing_gap >= 60:
        summary_parts.append("Significant marketing gaps present")
    if ai_fit >= 60:
        summary_parts.append("Strong fit for AI automation")
    if local >= 70:
        summary_parts.append("Well-aligned with target local market")
    if urgency >= 50:
        summary_parts.append("Urgent need for digital improvement")

    summary = ". ".join(summary_parts) if summary_parts else "Moderate prospect"

    # Build breakdown
    breakdown = [
        f"Marketing gap severity: {marketing_gap:.0f}/100",
        f"AI automation fit: {ai_fit:.0f}/100",
        f"Local relevance: {local:.0f}/100",
        f"Likely budget: {budget:.0f}/100",
        f"Outreach ease: {outreach:.0f}/100",
        f"Urgency signals: {urgency:.0f}/100",
        f"Data confidence: {confidence:.0f}/100",
    ]

    return ProspectScore(
        overall=round(overall, 1),
        marketing_gap_severity=round(marketing_gap, 1),
        ai_automation_fit=round(ai_fit, 1),
        local_relevance=round(local, 1),
        likely_budget=round(budget, 1),
        outreach_ease=round(outreach, 1),
        urgency_signals=round(urgency, 1),
        data_confidence=round(confidence, 1),
        grade=grade,
        summary=summary,
        breakdown=breakdown,
    )
