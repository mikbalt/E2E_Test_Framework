"""Solution: API CRUD Operations."""

import pytest


@pytest.mark.api
class TestAPICrudSolution:
    def test_list_members(self, authenticated_api):
        resp = authenticated_api.get("/api/members")
        resp.assert_status(200).assert_json_list_length(min_length=1)

    def test_create_and_delete_member(self, authenticated_api):
        payload = {
            "username": "sol_test_user",
            "email": "sol@test.com",
            "full_name": "Solution User",
            "role": "member",
            "password": "Test@12345",
        }
        resp = authenticated_api.post("/api/members", json=payload)
        resp.assert_status(201)
        member_id = resp.json()["id"]
        authenticated_api.delete(f"/api/members/{member_id}")
