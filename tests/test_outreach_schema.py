from __future__ import annotations

import pytest

from research.parsing import JsonParsingError
from research.schemas import OutreachPackSchema, validate_module_output


def test_outreach_pack_schema_accepts_all_sales_assets():
    data = {
        "cold_email": "Subject: Quick idea for Acme\n\nHi Sam, ...",
        "linkedin_dm": "Saw Acme's site and had a quick idea...",
        "discovery_call_opener": "I noticed three local SEO gaps worth exploring...",
        "proposal_outline": "1. Audit\n2. Automation roadmap\n3. Implementation sprint",
        "follow_up_sequence": [
            "Follow-up 1: sharing the audit angle",
            "Follow-up 2: relevant proof point",
        ],
        "data_confidence": "medium",
        "data_limitations": ["Generated from mocked analysis data."],
    }

    result = OutreachPackSchema.model_validate(data).model_dump(mode="python")

    assert result["cold_email"].startswith("Subject:")
    assert result["linkedin_dm"]
    assert result["discovery_call_opener"]
    assert result["proposal_outline"]
    assert result["follow_up_sequence"] == data["follow_up_sequence"]
    assert result["data_confidence"] == "medium"
    assert result["data_limitations"] == ["Generated from mocked analysis data."]


def test_outreach_pack_schema_defaults_missing_optional_fields():
    result = OutreachPackSchema.model_validate({}).model_dump(mode="python")

    assert result == {
        "cold_email": "",
        "linkedin_dm": "",
        "discovery_call_opener": "",
        "proposal_outline": "",
        "follow_up_sequence": [],
        "data_confidence": "",
        "data_limitations": [],
    }


def test_validate_module_output_supports_outreach_pack_schema():
    result = validate_module_output(
        {
            "cold_email": "Email body",
            "linkedin_dm": "DM body",
            "discovery_call_opener": "Call opener",
            "proposal_outline": "Proposal outline",
            "follow_up_sequence": ["Follow up tomorrow"],
        },
        OutreachPackSchema,
        "outreach",
    )

    assert result["cold_email"] == "Email body"
    assert result["follow_up_sequence"] == ["Follow up tomorrow"]
    assert result["data_confidence"] == ""


def test_validate_module_output_coerces_string_to_list():
    """String follow_up_sequence is coerced to a single-element list."""
    result = validate_module_output(
        {"follow_up_sequence": "not a list"},
        OutreachPackSchema,
        "outreach",
    )
    assert result["follow_up_sequence"] == ["not a list"]
