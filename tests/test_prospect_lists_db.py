"""Tests for prospect list database models and operations (Phase 15A)."""
from __future__ import annotations

import pytest
from pathlib import Path
from api.db import Database, reset_db, ProspectList, ProspectListMembership
from api.db import ProspectListRecord


@pytest.fixture
def db(tmp_path: Path) -> Database:
    db_path = str(tmp_path / "test_reconiq.db")
    return reset_db(db_path)


@pytest.fixture
def db_with_job(db: Database) -> Database:
    """Create a DB with one analysis job for membership testing."""
    db.create_job(
        target_url="https://example.com",
        modules=["company_profile"],
        provider="deepseek",
        model=None,
    )
    return db


# ── ListRecord dataclass ────────────────────────────────────────────────────


def test_prospect_list_record_defaults():
    record = ProspectListRecord(
        id="test-id",
        name="Test List",
    )
    assert record.id == "test-id"
    assert record.name == "Test List"
    assert record.description is None
    assert record.analysis_count == 0
    # Timestamps are None when creating records directly (only set by DB methods)
    assert record.created_at is None
    assert record.updated_at is None


# ── CRUD: create / get / list / update / delete ─────────────────────────────


def test_create_list(db: Database):
    rec = db.create_list("Vancouver HVAC", "Local HVAC companies in Vancouver WA")
    assert rec.id is not None
    assert rec.name == "Vancouver HVAC"
    assert rec.description == "Local HVAC companies in Vancouver WA"
    assert rec.analysis_count == 0


def test_create_list_minimal(db: Database):
    rec = db.create_list("Quick List")
    assert rec.name == "Quick List"
    assert rec.description is None


def test_get_list(db: Database):
    created = db.create_list("Test List")
    fetched = db.get_list(created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.name == "Test List"


def test_get_list_not_found(db: Database):
    assert db.get_list("nonexistent") is None


def test_list_lists_empty(db: Database):
    assert db.list_lists() == []


def test_list_lists(db: Database):
    db.create_list("List A")
    db.create_list("List B")
    lists = db.list_lists()
    assert len(lists) == 2
    names = [l.name for l in lists]
    assert "List A" in names
    assert "List B" in names


def test_update_list_name(db: Database):
    rec = db.create_list("Old Name")
    updated = db.update_list(rec.id, name="New Name")
    assert updated is not None
    assert updated.name == "New Name"
    # Fetch again to confirm persistence
    fetched = db.get_list(rec.id)
    assert fetched is not None
    assert fetched.name == "New Name"


def test_update_list_description(db: Database):
    rec = db.create_list("Test", "original desc")
    updated = db.update_list(rec.id, description="updated desc")
    assert updated is not None
    assert updated.description == "updated desc"


def test_update_list_not_found(db: Database):
    assert db.update_list("nonexistent", name="X") is None


def test_delete_list(db: Database):
    rec = db.create_list("To Delete")
    assert db.delete_list(rec.id) is True
    assert db.get_list(rec.id) is None


def test_delete_list_not_found(db: Database):
    assert db.delete_list("nonexistent") is False


# ── Membership: add / remove / list ─────────────────────────────────────────


def test_add_to_list(db_with_job: Database):
    job = db_with_job.list_jobs()[0]
    lst = db_with_job.create_list("Test List")
    result = db_with_job.add_to_list(lst.id, job.id)
    assert result is True


def test_add_to_list_not_found(db_with_job: Database):
    job = db_with_job.list_jobs()[0]
    assert db_with_job.add_to_list("nonexistent", job.id) is False


def test_add_to_list_analysis_not_found(db: Database):
    lst = db.create_list("Test List")
    assert db.add_to_list(lst.id, "nonexistent-job") is False


def test_add_duplicate_to_list(db_with_job: Database):
    job = db_with_job.list_jobs()[0]
    lst = db_with_job.create_list("Test List")
    assert db_with_job.add_to_list(lst.id, job.id) is True
    assert db_with_job.add_to_list(lst.id, job.id) is True  # idempotent


def test_remove_from_list(db_with_job: Database):
    job = db_with_job.list_jobs()[0]
    lst = db_with_job.create_list("Test List")
    db_with_job.add_to_list(lst.id, job.id)
    assert db_with_job.remove_from_list(lst.id, job.id) is True
    # Should be gone
    analyses = db_with_job.list_analyses_in_list(lst.id)
    assert len(analyses) == 0


def test_remove_from_list_not_found(db: Database):
    assert db.remove_from_list("nonexistent", "job-id") is False


def test_remove_nonexistent_membership(db_with_job: Database):
    job = db_with_job.list_jobs()[0]
    lst = db_with_job.create_list("Test List")
    assert db_with_job.remove_from_list(lst.id, job.id) is False


def test_list_analyses_in_list(db_with_job: Database):
    job = db_with_job.list_jobs()[0]
    lst = db_with_job.create_list("Test List")
    db_with_job.add_to_list(lst.id, job.id)
    analyses = db_with_job.list_analyses_in_list(lst.id)
    assert len(analyses) == 1
    assert analyses[0].id == job.id
    assert analyses[0].target_url == "https://example.com"


def test_list_analyses_in_empty_list(db: Database):
    lst = db.create_list("Empty List")
    assert db.list_analyses_in_list(lst.id) == []


def test_list_analyses_in_list_not_found(db: Database):
    assert db.list_analyses_in_list("nonexistent") == []


def test_list_lists_for_analysis(db_with_job: Database):
    job = db_with_job.list_jobs()[0]
    lst = db_with_job.create_list("Test List")
    db_with_job.add_to_list(lst.id, job.id)
    lists = db_with_job.list_lists_for_analysis(job.id)
    assert len(lists) == 1
    assert lists[0].name == "Test List"


def test_list_lists_for_analysis_none(db_with_job: Database):
    job = db_with_job.list_jobs()[0]
    assert db_with_job.list_lists_for_analysis(job.id) == []


# ── Cascade delete: deleting a list removes memberships ─────────────────────


def test_delete_list_removes_memberships(db_with_job: Database):
    job = db_with_job.list_jobs()[0]
    lst = db_with_job.create_list("Test List")
    db_with_job.add_to_list(lst.id, job.id)
    db_with_job.delete_list(lst.id)
    # Verify membership is gone
    assert db_with_job.list_lists_for_analysis(job.id) == []


# ── Analysis count tracking ────────────────────────────────────────────────


def test_list_analysis_count_updates(db_with_job: Database):
    job = db_with_job.list_jobs()[0]
    lst = db_with_job.create_list("Test List")
    assert lst.analysis_count == 0
    db_with_job.add_to_list(lst.id, job.id)
    fetched = db_with_job.get_list(lst.id)
    assert fetched is not None
    assert fetched.analysis_count == 1
    db_with_job.remove_from_list(lst.id, job.id)
    fetched = db_with_job.get_list(lst.id)
    assert fetched is not None
    assert fetched.analysis_count == 0
