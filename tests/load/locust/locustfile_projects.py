"""Locust load test: Project workflow operations.

Tasks:
  - list_projects (weight=5): List all projects
  - create_project (weight=2): Create a project
  - list_roles (weight=3): List available roles
"""

import os

from locust import HttpUser, between, task


class ProjectWorkflowUser(HttpUser):
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
    def list_projects(self):
        self.client.get("/api/projects", headers=self._headers())

    @task(2)
    def create_project(self):
        import uuid

        name = f"loadtest_{uuid.uuid4().hex[:8]}"
        self.client.post(
            "/api/projects",
            json={"name": name, "description": "Load test project"},
            headers=self._headers(),
            name="/api/projects [create]",
        )

    @task(3)
    def list_roles(self):
        self.client.get("/api/roles", headers=self._headers())
