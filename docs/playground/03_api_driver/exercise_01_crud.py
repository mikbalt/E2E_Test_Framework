"""Exercise: API CRUD Operations.

TODO: Complete the CRUD test for the members API.
"""

import pytest


@pytest.mark.api
class TestAPICrud:
    """Members API CRUD exercises."""

    def test_list_members(self, authenticated_api):
        """TODO: GET /api/members and assert status 200."""
        resp = authenticated_api.get("/api/members")
        resp.assert_status(200)
        resp.assert_json_list_length(min_length=1)

    def test_create_and_delete_member(self, authenticated_api):
        """TODO: Create a member via POST, then delete it."""
        # Step 1: Create
        payload = {
            "username": "playground_test_user",
            "email": "playground@test.com",
            "full_name": "Playground User",
            "role": "member",
            "password": "Test@12345",
        }
        resp = authenticated_api.post("/api/members", json=payload)
        resp.assert_status(201)
        member_id = resp.json().get("id")

        # Step 2: Verify it exists
        get_resp = authenticated_api.get(f"/api/members/{member_id}")
        get_resp.assert_status(200)

        # Step 3: Delete
        del_resp = authenticated_api.delete(f"/api/members/{member_id}")
        assert del_resp.status_code in (200, 204)
