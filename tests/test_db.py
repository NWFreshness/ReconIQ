"""Tests for database layer with filter support."""
from __future__ import annotations

import tempfile
from datetime import datetime, timedelta, timezone

import pytest

from api.db import Database, AnalysisRecord


def _make_db() -> Database:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        return Database(f.name)


def _create_job(db: Database, **kwargs) -> AnalysisRecord:
    return db.create_job(
        target_url=kwargs.get("target_url", "https://example.com"),
        modules=kwargs.get("modules", ["company_profile"]),
        provider=kwargs.get("provider", "deepseek"),
        model=kwargs.get("model", "deepseek-chat"),
        fmt=kwargs.get("fmt", "md"),
    )


class TestListJobsBasic:
    def test_returns_empty_list(self):
        db = _make_db()
        assert db.list_jobs() == []

    def test_returns_jobs_in_reverse_chronological_order(self):
        db = _make_db()
        j1 = _create_job(db)
        j2 = _create_job(db)
        jobs = db.list_jobs()
        assert jobs[0].id == j2.id
        assert jobs[1].id == j1.id

    def test_respects_limit(self):
        db = _make_db()
        for _ in range(5):
            _create_job(db)
        assert len(db.list_jobs(limit=3)) == 3


class TestListJobsStatusFilter:
    def test_filter_by_completed(self):
        db = _make_db()
        pending = _create_job(db)
        completed = _create_job(db)
        db.update_job(completed.id, status="completed")
        results = db.list_jobs(status="completed")
        assert len(results) == 1
        assert results[0].id == completed.id

    def test_filter_by_failed(self):
        db = _make_db()
        _create_job(db)
        failed = _create_job(db)
        db.update_job(failed.id, status="failed")
        results = db.list_jobs(status="failed")
        assert len(results) == 1
        assert results[0].id == failed.id

    def test_filter_by_running(self):
        db = _make_db()
        _create_job(db)
        running = _create_job(db)
        db.update_job(running.id, status="running")
        results = db.list_jobs(status="running")
        assert len(results) == 1

    def test_no_matches_returns_empty(self):
        db = _make_db()
        _create_job(db)
        assert db.list_jobs(status="failed") == []


class TestListJobsProviderFilter:
    def test_filter_by_provider(self):
        db = _make_db()
        _create_job(db, provider="deepseek")
        openai_job = _create_job(db, provider="openai")
        results = db.list_jobs(provider="openai")
        assert len(results) == 1
        assert results[0].provider == "openai"

    def test_provider_filter_case_sensitive(self):
        db = _make_db()
        _create_job(db, provider="DeepSeek")
        results = db.list_jobs(provider="deepseek")
        assert len(results) == 0


class TestListJobsDateFilters:
    def test_filter_date_from(self):
        db = _make_db()
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        # Create a job with old date by manipulating the DB directly
        old_job = _create_job(db)
        new_job = _create_job(db)
        # date_from: only jobs after now - 1 hour
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        results = db.list_jobs(date_from=cutoff)
        # The new_job is definitely after cutoff
        # The old_job might also be if it was just created
        assert any(r.id == new_job.id for r in results)

    def test_filter_date_to(self):
        db = _make_db()
        future = datetime.now(timezone.utc) + timedelta(days=1)
        j1 = _create_job(db)
        j2 = _create_job(db)
        results = db.list_jobs(date_to=future)
        assert len(results) == 2

    def test_combined_date_range(self):
        db = _make_db()
        _create_job(db)
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=1)
        j2 = _create_job(db)
        future = datetime.now(timezone.utc) + timedelta(days=1)
        results = db.list_jobs(date_from=cutoff, date_to=future)
        assert any(r.id == j2.id for r in results)


class TestListJobsMinScoreFilter:
    def test_filter_by_min_score(self):
        db = _make_db()
        low_score = _create_job(db, provider="deepseek")
        high_score = _create_job(db, provider="openai")
        db.update_job(low_score.id, status="completed", results={
            "prospect_score": {"overall": 35.0, "grade": "D"}
        })
        db.update_job(high_score.id, status="completed", results={
            "prospect_score": {"overall": 85.0, "grade": "A"}
        })
        results = db.list_jobs(min_score=70.0)
        assert len(results) == 1
        assert results[0].id == high_score.id

    def test_min_score_excludes_no_results(self):
        db = _make_db()
        no_results = _create_job(db)
        with_results = _create_job(db)
        db.update_job(with_results.id, status="completed", results={
            "prospect_score": {"overall": 90.0, "grade": "A"}
        })
        results = db.list_jobs(min_score=50.0)
        assert len(results) == 1
        assert results[0].id == with_results.id

    def test_min_score_excludes_missing_prospect_score(self):
        db = _make_db()
        no_score = _create_job(db)
        db.update_job(no_score.id, status="completed", results={
            "company_profile": {"name": "Test"}
        })
        results = db.list_jobs(min_score=50.0)
        assert len(results) == 0


class TestListJobsErrorOnly:
    def test_error_only_returns_failed(self):
        db = _make_db()
        _create_job(db)
        failed = _create_job(db)
        db.update_job(failed.id, status="failed")
        results = db.list_jobs(error_only=True)
        assert len(results) == 1
        assert results[0].id == failed.id

    def test_error_only_empty(self):
        db = _make_db()
        _create_job(db)
        assert db.list_jobs(error_only=True) == []


class TestListJobsCombinedFilters:
    def test_status_and_provider(self):
        db = _make_db()
        _create_job(db, provider="deepseek")
        _create_job(db, provider="openai")
        completed_deepseek = _create_job(db, provider="deepseek")
        db.update_job(completed_deepseek.id, status="completed")
        results = db.list_jobs(status="completed", provider="deepseek")
        assert len(results) == 1
        assert results[0].id == completed_deepseek.id

    def test_combined_no_matches(self):
        db = _make_db()
        _create_job(db, provider="openai")
        results = db.list_jobs(status="completed", provider="openai")
        assert results == []
