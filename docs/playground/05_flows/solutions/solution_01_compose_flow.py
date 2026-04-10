"""Solution: Compose a Flow."""

import pytest


class MemberCreationFlow:
    def __init__(self, api_driver):
        self.api = api_driver
        self.created_member = None

    def execute(self, admin_user="admin", admin_pass="admin123", member_data=None):
        self.api.login(admin_user, admin_pass)
        data = member_data or {
            "username": "sol_flow_user",
            "email": "sol_flow@test.com",
            "full_name": "Solution Flow User",
            "role": "member",
            "password": "Test@12345",
        }
        resp = self.api.post("/api/members", json=data)
        resp.assert_status(201)
        self.created_member = resp.json()
        return self

    def cleanup(self):
        if self.created_member:
            self.api.delete(f"/api/members/{self.created_member['id']}")


@pytest.mark.api
class TestFlowsSolution:
    def test_member_creation_flow(self, api_driver):
        flow = MemberCreationFlow(api_driver)
        try:
            flow.execute()
            assert flow.created_member["username"] == "sol_flow_user"
        finally:
            flow.cleanup()
