"""Tests for Phase 15B: Prospect Lists API routes."""
from __future__ import annotations

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
    db.reset_db(str(tmp_path / "test.db"))
    yield
    db._db = None


class TestCreateProspectList:
    def test_create_list(self) -> None:
        response = client.post(
            "/prospect-lists",
            json={"name": "Vancouver HVAC Companies"},
            headers=HEADERS,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Vancouver HVAC Companies"
        assert data["description"] is None
        assert data["analysis_count"] == 0
        assert data["id"] is not None

    def test_create_list_with_description(self) -> None:
        response = client.post(
            "/prospect-lists",
            json={
                "name": "Clark County Dental",
                "description": "Dental offices in Clark County WA",
            },
            headers=HEADERS,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["description"] == "Dental offices in Clark County WA"

    def test_create_list_missing_name(self) -> None:
        response = client.post(
            "/prospect-lists",
            json={},
            headers=HEADERS,
        )
        assert response.status_code == 422

    def test_create_list_requires_auth(self) -> None:
        response = client.post(
            "/prospect-lists",
            json={"name": "No Auth List"},
        )
        assert response.status_code == 401


class TestGetProspectList:
    def test_get_list(self) -> None:
        create_resp = client.post(
            "/prospect-lists",
            json={"name": "Test List", "description": "A test"},
            headers=HEADERS,
        )
        list_id = create_resp.json()["id"]

        response = client.get(f"/prospect-lists/{list_id}", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == list_id
        assert data["name"] == "Test List"
        assert data["description"] == "A test"

    def test_get_list_not_found(self) -> None:
        response = client.get("/prospect-lists/nonexistent", headers=HEADERS)
        assert response.status_code == 404


class TestListProspectLists:
    def test_list_lists_empty(self) -> None:
        response = client.get("/prospect-lists", headers=HEADERS)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_lists(self) -> None:
        client.post("/prospect-lists", json={"name": "List A"}, headers=HEADERS)
        client.post("/prospect-lists", json={"name": "List B"}, headers=HEADERS)

        response = client.get("/prospect-lists", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        names = [d["name"] for d in data]
        assert "List A" in names
        assert "List B" in names

    def test_list_lists_requires_auth(self) -> None:
        response = client.get("/prospect-lists")
        assert response.status_code == 401


class TestUpdateProspectList:
    def test_update_list_name(self) -> None:
        create_resp = client.post(
            "/prospect-lists",
            json={"name": "Old Name"},
            headers=HEADERS,
        )
        list_id = create_resp.json()["id"]

        response = client.put(
            f"/prospect-lists/{list_id}",
            json={"name": "New Name"},
            headers=HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"

        # Verify persistence
        get_resp = client.get(f"/prospect-lists/{list_id}", headers=HEADERS)
        assert get_resp.json()["name"] == "New Name"

    def test_update_list_description(self) -> None:
        create_resp = client.post(
            "/prospect-lists",
            json={"name": "Test", "description": "Original"},
            headers=HEADERS,
        )
        list_id = create_resp.json()["id"]

        response = client.put(
            f"/prospect-lists/{list_id}",
            json={"description": "Updated description"},
            headers=HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"

    def test_update_list_not_found(self) -> None:
        response = client.put(
            "/prospect-lists/nonexistent",
            json={"name": "New"},
            headers=HEADERS,
        )
        assert response.status_code == 404

    def test_update_requires_auth(self) -> None:
        create_resp = client.post(
            "/prospect-lists",
            json={"name": "Test"},
            headers=HEADERS,
        )
        list_id = create_resp.json()["id"]
        response = client.put(
            f"/prospect-lists/{list_id}",
            json={"name": "New"},
        )
        assert response.status_code == 401


class TestDeleteProspectList:
    def test_delete_list(self) -> None:
        create_resp = client.post(
            "/prospect-lists",
            json={"name": "To Delete"},
            headers=HEADERS,
        )
        list_id = create_resp.json()["id"]

        response = client.delete(f"/prospect-lists/{list_id}", headers=HEADERS)
        assert response.status_code == 204

        # Verify it's gone
        get_resp = client.get(f"/prospect-lists/{list_id}", headers=HEADERS)
        assert get_resp.status_code == 404

    def test_delete_list_not_found(self) -> None:
        response = client.delete("/prospect-lists/nonexistent", headers=HEADERS)
        assert response.status_code == 404

    def test_delete_requires_auth(self) -> None:
        create_resp = client.post(
            "/prospect-lists",
            json={"name": "Test"},
            headers=HEADERS,
        )
        list_id = create_resp.json()["id"]
        response = client.delete(f"/prospect-lists/{list_id}")
        assert response.status_code == 401


class TestListAnalysesInProspectList:
    @pytest.fixture
    def list_with_analyses(self) -> str:
        """Create a list with two analyses in it."""
        from api.db import get_db

        # Create analyses first
        create_a = client.post(
            "/analyses",
            json={"target_url": "https://example-a.com", "modules": ["company_profile"]},
            headers=HEADERS,
        )
        create_b = client.post(
            "/analyses",
            json={"target_url": "https://example-b.com", "modules": ["company_profile"]},
            headers=HEADERS,
        )
        analysis_id_a = create_a.json()["id"]
        analysis_id_b = create_b.json()["id"]

        # Create the list
        create_list = client.post(
            "/prospect-lists",
            json={"name": "Test List"},
            headers=HEADERS,
        )
        list_id = create_list.json()["id"]

        # Add analyses to the list
        db = get_db()
        db.add_to_list(list_id, analysis_id_a)
        db.add_to_list(list_id, analysis_id_b)

        return list_id

    def test_list_analyses_in_list(self, list_with_analyses: str) -> None:
        response = client.get(
            f"/prospect-lists/{list_with_analyses}/analyses",
            headers=HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        urls = [d["target_url"] for d in data]
        assert "https://example-a.com/" in urls
        assert "https://example-b.com/" in urls

    def test_list_analyses_empty_list(self) -> None:
        create_resp = client.post(
            "/prospect-lists",
            json={"name": "Empty List"},
            headers=HEADERS,
        )
        list_id = create_resp.json()["id"]

        response = client.get(f"/prospect-lists/{list_id}/analyses", headers=HEADERS)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_analyses_not_found(self) -> None:
        response = client.get("/prospect-lists/nonexistent/analyses", headers=HEADERS)
        assert response.status_code == 404


class TestAddAnalysisToList:
    @pytest.fixture
    def analysis_and_list(self) -> tuple[str, str]:
        """Create an analysis and a list."""
        create_analysis = client.post(
            "/analyses",
            json={"target_url": "https://example.com", "modules": ["company_profile"]},
            headers=HEADERS,
        )
        create_list = client.post(
            "/prospect-lists",
            json={"name": "Test List"},
            headers=HEADERS,
        )
        return create_analysis.json()["id"], create_list.json()["id"]

    def test_add_analysis_to_list(self, analysis_and_list: tuple[str, str]) -> None:
        analysis_id, list_id = analysis_and_list

        response = client.post(
            f"/prospect-lists/{list_id}/analyses",
            json={"analysis_id": analysis_id},
            headers=HEADERS,
        )
        assert response.status_code == 201

        # Verify it shows up
        get_resp = client.get(f"/prospect-lists/{list_id}/analyses", headers=HEADERS)
        assert len(get_resp.json()) == 1

    def test_add_analysis_analysis_not_found(self, analysis_and_list: tuple[str, str]) -> None:
        _, list_id = analysis_and_list

        response = client.post(
            f"/prospect-lists/{list_id}/analyses",
            json={"analysis_id": "nonexistent-analysis"},
            headers=HEADERS,
        )
        assert response.status_code == 404

    def test_add_analysis_list_not_found(self, analysis_and_list: tuple[str, str]) -> None:
        analysis_id, _ = analysis_and_list

        response = client.post(
            "/prospect-lists/nonexistent/analyses",
            json={"analysis_id": analysis_id},
            headers=HEADERS,
        )
        assert response.status_code == 404

    def test_add_duplicate_analysis(self, analysis_and_list: tuple[str, str]) -> None:
        analysis_id, list_id = analysis_and_list

        first = client.post(
            f"/prospect-lists/{list_id}/analyses",
            json={"analysis_id": analysis_id},
            headers=HEADERS,
        )
        assert first.status_code == 201

        # Adding again is idempotent (200, not error)
        second = client.post(
            f"/prospect-lists/{list_id}/analyses",
            json={"analysis_id": analysis_id},
            headers=HEADERS,
        )
        assert second.status_code == 200


class TestRemoveAnalysisFromList:
    @pytest.fixture
    def populated_list(self) -> tuple[str, str]:
        """Create a list with an analysis in it."""
        from api.db import get_db

        create_analysis = client.post(
            "/analyses",
            json={"target_url": "https://example.com", "modules": ["company_profile"]},
            headers=HEADERS,
        )
        create_list = client.post(
            "/prospect-lists",
            json={"name": "Test List"},
            headers=HEADERS,
        )
        analysis_id = create_analysis.json()["id"]
        list_id = create_list.json()["id"]

        db = get_db()
        db.add_to_list(list_id, analysis_id)

        return list_id, analysis_id

    def test_remove_analysis(self, populated_list: tuple[str, str]) -> None:
        list_id, analysis_id = populated_list

        response = client.delete(
            f"/prospect-lists/{list_id}/analyses/{analysis_id}",
            headers=HEADERS,
        )
        assert response.status_code == 204

        # Verify it's gone
        get_resp = client.get(f"/prospect-lists/{list_id}/analyses", headers=HEADERS)
        assert len(get_resp.json()) == 0

    def test_remove_not_found(self) -> None:
        response = client.delete(
            "/prospect-lists/nonexistent/analyses/nonexistent",
            headers=HEADERS,
        )
        assert response.status_code == 404
