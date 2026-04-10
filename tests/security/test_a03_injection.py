"""A03:2021 - Injection.

Tests for SQL injection, command injection, path traversal, and integer overflow.
"""

import pytest

from tests.security.payloads import (
    COMMAND_INJECTION_PAYLOADS,
    PATH_TRAVERSAL_PAYLOADS,
    SQL_INJECTION_PAYLOADS,
)

pytestmark = [pytest.mark.security, pytest.mark.owasp]


class TestSQLInjectionLogin:
    """SQL injection via login endpoint."""

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS[:4])
    def test_sqli_username(self, api_client, payload):
        """SQL injection in username field must not authenticate."""
        resp = api_client.post(
            "/api/auth/login",
            json={"username": payload, "password": "anything"},
        )
        assert resp.status_code in (400, 401, 422)

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS[:4])
    def test_sqli_password(self, api_client, payload):
        """SQL injection in password field must not authenticate."""
        resp = api_client.post(
            "/api/auth/login",
            json={"username": "admin", "password": payload},
        )
        assert resp.status_code in (400, 401, 422)


class TestSQLInjectionMemberCreation:
    """SQL injection via member creation."""

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS[:4])
    def test_sqli_member_username(self, authed_api, payload):
        """SQL injection in member username must be rejected or sanitized."""
        resp = authed_api.post(
            "/api/members",
            json={"username": payload, "email": "test@test.com", "role": "viewer"},
        )
        # Should either reject (400/422) or store safely (201 with sanitized data)
        assert resp.status_code in (201, 400, 422)
        if resp.status_code == 201:
            data = resp.json()
            member_id = data.get("id")
            if member_id:
                authed_api.delete(f"/api/members/{member_id}")


class TestCommandInjection:
    """Command injection via input fields."""

    @pytest.mark.parametrize("payload", COMMAND_INJECTION_PAYLOADS)
    def test_command_injection_in_search(self, authed_api, payload):
        """Command injection payloads in query params must not execute."""
        resp = authed_api.get(f"/api/members?search={payload}")
        # Should return normal response, not system command output
        assert resp.status_code in (200, 400, 422)
        if resp.status_code == 200:
            text = resp.text
            assert "/bin/" not in text
            assert "root:" not in text
            assert "uid=" not in text


class TestPathTraversal:
    """Path traversal attack tests."""

    @pytest.mark.parametrize("payload", PATH_TRAVERSAL_PAYLOADS)
    def test_path_traversal_rejected(self, authed_api, payload):
        """Path traversal payloads must not expose system files."""
        resp = authed_api.get(f"/api/files/{payload}")
        assert resp.status_code in (400, 403, 404)
        assert "root:" not in resp.text


class TestIntegerOverflow:
    """Integer overflow / boundary tests."""

    def test_large_id_handled(self, authed_api):
        """Extremely large IDs must not cause server errors."""
        resp = authed_api.get("/api/members/99999999999999999")
        assert resp.status_code in (400, 404, 422)
