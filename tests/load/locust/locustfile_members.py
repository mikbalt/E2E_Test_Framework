"""Locust load test: Member CRUD operations.

Tasks:
  - list_members (weight=5): List all members
  - create_and_delete (weight=2): Create then delete a member
  - get_by_id (weight=1): Get member by ID
"""

import os

from locust import HttpUser, between, task


class MemberCRUDUser(HttpUser):
    wait_time = between(1, 3)
    host = os.environ.get("TARGET_HOST", "http://localhost:8000")
    token = None

    def on_start(self):
        username = os.environ.get("ADMIN_USER", "admin")
        password = os.environ.get("ADMIN_PASS", "admin123")
        resp = self.client.post(
            "/api/auth/login",
            json={"username": username, "password": password},
        )
        if resp.status_code == 200:
            self.token = resp.json().get("access_token")

    def _headers(self):
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    @task(5)
    def list_members(self):
        self.client.get("/api/members", headers=self._headers())

    @task(2)
    def create_and_delete(self):
        import uuid

        name = f"loadtest_{uuid.uuid4().hex[:8]}"
        resp = self.client.post(
            "/api/members",
            json={"username": name, "email": f"{name}@test.com", "role": "viewer"},
            headers=self._headers(),
            name="/api/members [create]",
        )
        if resp.status_code in (200, 201):
            member_id = resp.json().get("id")
            if member_id:
                self.client.delete(
                    f"/api/members/{member_id}",
                    headers=self._headers(),
                    name="/api/members/{id} [delete]",
                )

    @task(1)
    def get_by_id(self):
        self.client.get(
            "/api/members/1",
            headers=self._headers(),
            name="/api/members/{id}",
        )
