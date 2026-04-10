"""API tests for project management and approval endpoints."""

import pytest


@pytest.mark.api
class TestProjectsAPI:
    """Test /api/projects CRUD + approval workflow."""

    def test_list_projects(self, authed_api):
        """GET /api/projects should return a list."""
        resp = authed_api.get("/api/projects")
        resp.assert_status(200)
        assert isinstance(resp.json(), list)

    def test_create_project(self, authed_api):
        """POST /api/projects should create a project."""
        resp = authed_api.post("/api/projects", json={
            "name": "API Test Project",
            "description": "Created by API test",
            "required_approvals": 3,
        })
        resp.assert_status(201)
        resp.assert_json_key("id")
        resp.assert_json_key("name", "API Test Project")

    def test_get_project_with_approvals(self, authed_api):
        """GET /api/projects/{id} should include approval details."""
        create_resp = authed_api.post("/api/projects", json={
            "name": "Detail Test Project",
            "description": "For detail view test",
            "required_approvals": 2,
        })
        project_id = create_resp.json()["id"]

        resp = authed_api.get(f"/api/projects/{project_id}")
        resp.assert_status(200)
        resp.assert_json_key("name")
        resp.assert_json_key("status")

    def test_approve_project_step(self, authed_api):
        """POST /api/projects/{id}/approve should advance approval."""
        create_resp = authed_api.post("/api/projects", json={
            "name": "Approve Test Project",
            "description": "For approval test",
            "required_approvals": 1,
        })
        project_id = create_resp.json()["id"]

        resp = authed_api.post(f"/api/projects/{project_id}/approve", json={
            "comment": "Looks good",
        })
        assert resp.status_code in (200, 201)

    def test_reject_project(self, authed_api):
        """POST /api/projects/{id}/reject should reject the project."""
        create_resp = authed_api.post("/api/projects", json={
            "name": "Reject Test Project",
            "description": "For rejection test",
            "required_approvals": 3,
        })
        project_id = create_resp.json()["id"]

        resp = authed_api.post(f"/api/projects/{project_id}/reject", json={
            "comment": "Needs revision",
        })
        assert resp.status_code in (200, 201)
