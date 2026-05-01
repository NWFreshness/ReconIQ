"""Typed Pydantic schemas for research module outputs."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from research.parsing import JsonParsingError


class ReconIQBaseModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="python")


class CompanyProfileSchema(ReconIQBaseModel):
    company_name: str
    what_they_do: str
    target_audience: str
    value_proposition: str
    brand_voice: str | list[str]
    primary_cta: str
    services_products: list[str]
    marketing_channels: list[str]
    data_confidence: str
    data_limitations: list[str]


class SEOKeywordsSchema(ReconIQBaseModel):
    top_keywords: list[str]
    content_gaps: list[str]
    seo_weaknesses: list[str]
    quick_wins: list[str]
    estimated_traffic_tier: str
    local_seo_signals: str
    data_confidence: str
    data_limitations: list[str]


class CompetitorItem(ReconIQBaseModel):
    name: str
    url: str
    positioning: str
    estimated_pricing_tier: str
    key_messaging: str
    weaknesses: list[str]
    inferred_services: list[str]


class CompetitorSchema(ReconIQBaseModel):
    competitors: list[CompetitorItem]
    scraped_competitors: list[CompetitorItem] = []
    inferred_competitors: list[CompetitorItem] = []
    data_confidence: str
    data_limitations: list[str]


class SocialAccount(ReconIQBaseModel):
    platform: str
    url: str


class SocialContentSchema(ReconIQBaseModel):
    platforms: list[str]
    verified_social_accounts: list[SocialAccount] = []
    inferred_platforms: list[str] = []
    content_quality: str
    content_frequency: str
    engagement_signals: str
    review_sites: list[str]
    blog_or_resources: str
    content_gaps: list[str]
    email_signals: str
    data_confidence: str
    data_limitations: list[str]


class SWOTQuadrants(ReconIQBaseModel):
    strengths: list[str]
    weaknesses: list[str]
    opportunities: list[str]
    threats: list[str]


class SWOTSchema(ReconIQBaseModel):
    swot: SWOTQuadrants
    acquisition_angle: str
    talking_points: list[str]
    recommended_next_steps: list[str]
    competitive_advantage: str
    lead_generation_strategy: str
    close_rate_strategy: str
    data_confidence: str
    data_limitations: list[str]


def validate_module_output(data: dict[str, Any], schema_type: type[BaseModel], context: str) -> dict[str, Any]:
    """Validate module output and return a plain dict for existing callers."""
    try:
        model = schema_type.model_validate(data)
    except ValidationError as exc:
        errors = "; ".join(
            f"{'.'.join(str(part) for part in err.get('loc', ()))}: {err.get('msg')}"
            for err in exc.errors()
        )
        raise JsonParsingError(f"{context} schema validation failed: {errors}") from exc
    return model.model_dump(mode="python")
