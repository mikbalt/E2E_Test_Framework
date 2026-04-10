"""Exercise: Compose a Flow.

TODO: Create a flow that performs login + member creation via API.
"""

import pytest


class MemberCreationFlow:
    """Flow: Login and create a new member via API."""

    def __init__(self, api_driver):
        self.api = api_driver
        self.created_member = None

    def execute(self, admin_user="admin", admin_pass="admin123", member_data=None):
        """Run the full flow: login -> create member."""
        # Step 1: Login
        self.api.login(admin_user, admin_pass)

        # Step 2: Create member
        if member_data is None:
            member_data = {
                "username": "flow_test_user",
                "email": "flow@test.com",
                "full_name": "Flow User",
                "role": "member",
                "password": "Test@12345",
            }
        resp = self.api.post("/api/members", json=member_data)
        resp.assert_status(201)
        self.created_member = resp.json()
        return self

    def cleanup(self):
        """Delete the created member."""
        if self.created_member:
            member_id = self.created_member.get("id")
            self.api.delete(f"/api/members/{member_id}")


@pytest.mark.api
class TestFlows:
    """Flow composition exercises."""

    def test_member_creation_flow(self, api_driver):
        """TODO: Execute the MemberCreationFlow and verify the result."""
        flow = MemberCreationFlow(api_driver)
        try:
            flow.execute()
            assert flow.created_member is not None
            assert flow.created_member.get("username") == "flow_test_user"
        finally:
            flow.cleanup()
