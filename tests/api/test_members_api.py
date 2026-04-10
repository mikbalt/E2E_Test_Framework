"""API tests for member management endpoints."""

import pytest


@pytest.mark.api
class TestMembersAPI:
    """Test /api/members CRUD + suspend/reactivate."""

    def test_list_members(self, authed_api):
        """GET /api/members should return a list."""
        resp = authed_api.get("/api/members")
        resp.assert_status(200)
        resp.assert_json_list_length(1)

    def test_create_member(self, authed_api):
        """POST /api/members should create a new member."""
        resp = authed_api.post("/api/members", json={
            "username": "api_test_member",
            "email": "api_test@example.com",
            "password": "test123",
            "role_id": 3,
        })
        resp.assert_status(201)
        resp.assert_json_key("id")
        resp.assert_json_key("username", "api_test_member")

    def test_get_member(self, authed_api):
        """GET /api/members/{id} should return member details."""
        # Get first member from list
        members = authed_api.get("/api/members").json()
        member_id = members[0]["id"]

        resp = authed_api.get(f"/api/members/{member_id}")
        resp.assert_status(200)
        resp.assert_json_key("username")

    def test_update_member(self, authed_api):
        """PUT /api/members/{id} should update member data."""
        # Create a member first
        create_resp = authed_api.post("/api/members", json={
            "username": "update_test",
            "email": "update@example.com",
            "password": "test123",
            "role_id": 3,
        })
        member_id = create_resp.json()["id"]

        resp = authed_api.put(f"/api/members/{member_id}", json={
            "email": "updated@example.com",
        })
        resp.assert_status(200)

    def test_delete_member(self, authed_api):
        """DELETE /api/members/{id} should remove the member."""
        create_resp = authed_api.post("/api/members", json={
            "username": "delete_test",
            "email": "delete@example.com",
            "password": "test123",
            "role_id": 3,
        })
        member_id = create_resp.json()["id"]

        resp = authed_api.delete(f"/api/members/{member_id}")
        resp.assert_status(200)

        # Verify deleted
        get_resp = authed_api.get(f"/api/members/{member_id}")
        assert get_resp.status_code == 404

    def test_suspend_member(self, authed_api):
        """POST /api/members/{id}/suspend should deactivate."""
        create_resp = authed_api.post("/api/members", json={
            "username": "suspend_test",
            "email": "suspend@example.com",
            "password": "test123",
            "role_id": 3,
        })
        member_id = create_resp.json()["id"]

        resp = authed_api.post(f"/api/members/{member_id}/suspend")
        resp.assert_status(200)

        get_resp = authed_api.get(f"/api/members/{member_id}")
        assert get_resp.json()["is_active"] is False

    def test_reactivate_member(self, authed_api):
        """POST /api/members/{id}/reactivate should reactivate."""
        create_resp = authed_api.post("/api/members", json={
            "username": "reactivate_test",
            "email": "reactivate@example.com",
            "password": "test123",
            "role_id": 3,
        })
        member_id = create_resp.json()["id"]

        authed_api.post(f"/api/members/{member_id}/suspend")
        resp = authed_api.post(f"/api/members/{member_id}/reactivate")
        resp.assert_status(200)

        get_resp = authed_api.get(f"/api/members/{member_id}")
        assert get_resp.json()["is_active"] is True

    def test_unauthorized_access(self, api_client):
        """Unauthenticated requests should return 401."""
        resp = api_client.get("/api/members")
        resp.assert_status(401)
