"""Locust load test: Full combined scenario.

All operations with weighted tasks and tags for selective execution.
"""

import os
import uuid

from locust import HttpUser, between, tag, task


class FullScenarioUser(HttpUser):
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

    @tag("health")
    @task(2)
    def health_check(self):
        self.client.get("/api/health")

    @tag("auth")
    @task(3)
    def login(self):
        username = os.environ.get("ADMIN_USER", "admin")
        password = os.environ.get("ADMIN_PASS", "admin123")
        self.client.post(
            "/api/auth/login",
            json={"username": username, "password": password},
            name="/api/auth/login",
        )

    @tag("members")
    @task(5)
    def list_members(self):
        self.client.get("/api/members", headers=self._headers())

    @tag("members")
    @task(2)
    def create_member(self):
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

    @tag("projects")
    @task(4)
    def list_projects(self):
        self.client.get("/api/projects", headers=self._headers())

    @tag("projects")
    @task(1)
    def create_project(self):
        name = f"loadtest_{uuid.uuid4().hex[:8]}"
        self.client.post(
            "/api/projects",
            json={"name": name, "description": "Load test project"},
            headers=self._headers(),
            name="/api/projects [create]",
        )

    @tag("roles")
    @task(3)
    def list_roles(self):
        self.client.get("/api/roles", headers=self._headers())
