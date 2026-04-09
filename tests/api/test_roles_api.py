"""API tests for role management endpoints."""

import pytest


@pytest.mark.api
class TestRolesAPI:
    """Test /api/roles CRUD."""

    def test_list_roles(self, authed_api):
        """GET /api/roles should return seeded roles."""
        resp = authed_api.get("/api/roles")
        resp.assert_status(200)
        resp.assert_json_list_length(3)

    def test_create_role(self, authed_api):
        """POST /api/roles should create a new role."""
        resp = authed_api.post("/api/roles", json={
            "name": "api_test_role",
            "description": "Created by API test",
        })
        resp.assert_status(201)
        resp.assert_json_key("name", "api_test_role")

    def test_get_role(self, authed_api):
        """GET /api/roles/{id} should return role details."""
        roles = authed_api.get("/api/roles").json()
        role_id = roles[0]["id"]

        resp = authed_api.get(f"/api/roles/{role_id}")
        resp.assert_status(200)
        resp.assert_json_key("name")

    def test_delete_role(self, authed_api):
        """DELETE /api/roles/{id} should remove the role."""
        create_resp = authed_api.post("/api/roles", json={
            "name": "delete_role_test",
            "description": "To be deleted",
        })
        role_id = create_resp.json()["id"]

        resp = authed_api.delete(f"/api/roles/{role_id}")
        resp.assert_status(200)
