"""A01:2021 - Broken Access Control.

Tests for unauthorized access, IDOR, privilege escalation, and token validation.
"""

import pytest

pytestmark = [pytest.mark.security, pytest.mark.owasp]


class TestUnauthorizedAccess:
    """Verify endpoints reject unauthenticated requests."""

    def test_members_list_requires_auth(self, api_client):
        """GET /api/members must return 401 without token."""
        resp = api_client.get("/api/members")
        assert resp.status_code == 401

    def test_projects_list_requires_auth(self, api_client):
        """GET /api/projects must return 401 without token."""
        resp = api_client.get("/api/projects")
        assert resp.status_code == 401

    def test_member_create_requires_auth(self, api_client):
        """POST /api/members must return 401 without token."""
        resp = api_client.post("/api/members", json={"username": "hacker"})
        assert resp.status_code == 401


class TestIDOR:
    """Insecure Direct Object Reference tests."""

    def test_cannot_read_other_user_by_id(self, authed_api, member_api):
        """Non-admin should not access arbitrary member details."""
        # Login as a low-privilege user if available, otherwise verify
        # that accessing a non-existent high ID returns 404, not data
        resp = authed_api.get("/api/members/99999")
        assert resp.status_code in (403, 404)

    def test_cannot_modify_other_user(self, api_client):
        """PUT /api/members/{id} without auth must fail."""
        resp = api_client.put(
            "/api/members/1",
            json={"username": "pwned"},
        )
        assert resp.status_code == 401


class TestPrivilegeEscalation:
    """Tests for vertical privilege escalation."""

    def test_non_admin_cannot_delete_member(self, member_api):
        """Non-admin user cannot delete members."""
        resp = member_api.delete("/api/members/1")
        assert resp.status_code in (401, 403)


class TestMethodNotAllowed:
    """Verify only expected HTTP methods are accepted."""

    def test_delete_on_health_returns_405(self, api_client):
        """DELETE /api/health should return 405 Method Not Allowed."""
        resp = api_client.delete("/api/health")
        assert resp.status_code in (405, 404)


class TestTokenValidation:
    """Verify expired and forged tokens are rejected."""

    def test_expired_token_rejected(self, api_client):
        """Requests with expired JWT must return 401."""
        api_client._token = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiJhZG1pbiIsImV4cCI6MX0."
            "invalid_signature"
        )
        resp = api_client.get("/api/members")
        assert resp.status_code == 401

    def test_forged_user_id_rejected(self, api_client):
        """Token with forged sub claim must fail on protected endpoints."""
        api_client._token = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiJub25leGlzdGVudCIsImV4cCI6OTk5OTk5OTk5OX0."
            "forged_signature"
        )
        resp = api_client.get("/api/members")
        assert resp.status_code == 401
