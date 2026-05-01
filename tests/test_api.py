"""Tests for Phase 9A: FastAPI backend."""
from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.auth import get_api_key

client = TestClient(app)

API_KEY = get_api_key()
HEADERS = {"X-API-Key": API_KEY}


@pytest.fixture(autouse=True)
def reset_db(monkeypatch, tmp_path):
    from api import db
    test_db = db.reset_db(str(tmp_path / "test.db"))
    yield test_db
    db._db = None


class TestHealth:
    def test_health_check(self) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestAuth:
    def test_missing_api_key(self) -> None:
        response = client.post("/analyses", json={"target_url": "https://example.com"})
        assert response.status_code == 401

    def test_invalid_api_key(self) -> None:
        response = client.post(
            "/analyses",
            json={"target_url": "https://example.com"},
            headers={"X-API-Key": "wrong-key"},
        )
        assert response.status_code == 401


class TestCreateAnalysis:
    @patch("api.routes.analyses.start_analysis_job")
    def test_create_analysis(self, mock_start: MagicMock) -> None:
        response = client.post(
            "/analyses",
            json={"target_url": "https://example.com"},
            headers=HEADERS,
        )
        assert response.status_code == 202
        data = response.json()
        assert data["target_url"] == "https://example.com/"
        assert data["status"] == "pending"
        assert data["id"]
        mock_start.assert_called_once_with(data["id"])

    def test_create_analysis_invalid_url(self) -> None:
        response = client.post(
            "/analyses",
            json={"target_url": "ftp://not-a-url"},
            headers=HEADERS,
        )
        assert response.status_code == 422


class TestGetAnalysis:
    @patch("api.routes.analyses.start_analysis_job")
    def test_get_analysis(self, mock_start: MagicMock) -> None:
        create = client.post(
            "/analyses",
            json={"target_url": "https://example.com"},
            headers=HEADERS,
        )
        job_id = create.json()["id"]

        response = client.get(f"/analyses/{job_id}", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == job_id
        assert data["target_url"] == "https://example.com/"

    def test_get_analysis_not_found(self) -> None:
        response = client.get("/analyses/nonexistent-id", headers=HEADERS)
        assert response.status_code == 404


class TestListAnalyses:
    @patch("api.routes.analyses.start_analysis_job")
    def test_list_analyses(self, mock_start: MagicMock) -> None:
        for i in range(3):
            client.post(
                "/analyses",
                json={"target_url": f"https://example{i}.com"},
                headers=HEADERS,
            )
        response = client.get("/analyses?limit=10", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3


class TestGetResults:
    @patch("api.routes.analyses.start_analysis_job")
    def test_get_results(self, mock_start: MagicMock) -> None:
        create = client.post(
            "/analyses",
            json={"target_url": "https://example.com"},
            headers=HEADERS,
        )
        job_id = create.json()["id"]

        response = client.get(f"/analyses/{job_id}/results", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == job_id
        assert data["status"] == "pending"

    def test_get_results_not_found(self) -> None:
        response = client.get("/analyses/nonexistent-id/results", headers=HEADERS)
        assert response.status_code == 404


class TestDownloadReport:
    def test_download_report_not_found(self) -> None:
        response = client.get("/reports/nonexistent-id", headers=HEADERS)
        assert response.status_code == 404

    @patch("api.routes.analyses.start_analysis_job")
    def test_download_report_no_report(self, mock_start: MagicMock) -> None:
        create = client.post(
            "/analyses",
            json={"target_url": "https://example.com"},
            headers=HEADERS,
        )
        job_id = create.json()["id"]
        response = client.get(f"/reports/{job_id}", headers=HEADERS)
        assert response.status_code == 404


class TestWorker:
    @patch("api.worker.run_analysis")
    def test_worker_completes_job(self, mock_run: MagicMock) -> None:
        from api.db import get_db
        from api.worker import run_analysis_job

        db = get_db()
        record = db.create_job(
            target_url="https://example.com",
            modules=["company_profile"],
            provider="deepseek",
            model=None,
            fmt="md",
        )

        mock_run.return_value = MagicMock(
            report_path="/tmp/report.md",
            results={"company_profile": {"company_name": "Example"}},
        )

        run_analysis_job(record.id)

        updated = db.get_job(record.id)
        assert updated is not None
        assert updated.status == "completed"
        assert updated.report_path == "/tmp/report.md"
        assert updated.results is not None

    @patch("api.worker.run_analysis")
    def test_worker_handles_failure(self, mock_run: MagicMock) -> None:
        from api.db import get_db
        from api.worker import run_analysis_job

        db = get_db()
        record = db.create_job(
            target_url="https://example.com",
            modules=["company_profile"],
            provider="deepseek",
            model=None,
            fmt="md",
        )

        mock_run.side_effect = RuntimeError("boom")

        run_analysis_job(record.id)

        updated = db.get_job(record.id)
        assert updated is not None
        assert updated.status == "failed"
        assert "boom" in (updated.error or "")


class TestDatabase:
    def test_create_and_get_job(self, tmp_path) -> None:
        from api.db import Database

        db = Database(str(tmp_path / "test.db"))
        record = db.create_job(
            target_url="https://example.com",
            modules=["company_profile"],
            provider="deepseek",
            model=None,
            fmt="md",
        )
        assert record.id
        assert record.status == "pending"

        fetched = db.get_job(record.id)
        assert fetched is not None
        assert fetched.target_url == "https://example.com"

    def test_update_job(self, tmp_path) -> None:
        from api.db import Database

        db = Database(str(tmp_path / "test.db"))
        record = db.create_job(
            target_url="https://example.com",
            modules=["company_profile"],
            provider="deepseek",
            model=None,
            fmt="md",
        )
        db.update_job(record.id, status="running", progress_pct=50.0)
        updated = db.get_job(record.id)
        assert updated is not None
        assert updated.status == "running"
        assert updated.progress_pct == 50.0

    def test_list_jobs(self, tmp_path) -> None:
        from api.db import Database

        db = Database(str(tmp_path / "test.db"))
        for i in range(3):
            db.create_job(
                target_url=f"https://example{i}.com",
                modules=["company_profile"],
                provider="deepseek",
                model=None,
                fmt="md",
            )
        jobs = db.list_jobs(limit=10)
        assert len(jobs) == 3
