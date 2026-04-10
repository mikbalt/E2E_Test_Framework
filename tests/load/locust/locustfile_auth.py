"""Locust load test: Authentication flow.

Tasks:
  - login_success (weight=3): Successful admin login
  - login_failure (weight=1): Failed login attempt
  - health_check (weight=2): Health endpoint check
"""

import os

from locust import HttpUser, between, task


class AuthUser(HttpUser):
    wait_time = between(1, 3)
    host = os.environ.get("TARGET_HOST", "http://localhost:8000")

    @task(3)
    def login_success(self):
        username = os.environ.get("ADMIN_USER", "admin")
        password = os.environ.get("ADMIN_PASS", "admin123")
        self.client.post(
            "/api/auth/login",
            json={"username": username, "password": password},
            name="/api/auth/login [success]",
        )

    @task(1)
    def login_failure(self):
        self.client.post(
            "/api/auth/login",
            json={"username": "invalid", "password": "invalid"},
            name="/api/auth/login [failure]",
            catch_response=True,
        )

    @task(2)
    def health_check(self):
        self.client.get("/api/health")
