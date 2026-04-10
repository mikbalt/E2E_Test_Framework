"""A09:2021 - Security Logging and Monitoring Failures.

Tests for consistent error messages, brute force resilience, and suspended user handling.
"""

import pytest

pytestmark = [pytest.mark.security, pytest.mark.owasp]


class TestConsistentErrorMessages:
    """Verify error messages don't leak user existence information."""

    def test_invalid_user_vs_invalid_password(self, api_client):
        """Error messages for wrong user vs wrong password must be identical."""
        resp_bad_user = api_client.post(
            "/api/auth/login",
            json={"username": "nonexistent_user_xyz", "password": "wrongpass"},
        )
        resp_bad_pass = api_client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrong_password_xyz"},
        )
        # Both should return 401
        assert resp_bad_user.status_code == resp_bad_pass.status_code == 401

        # Error messages should be generic and identical
        msg_bad_user = resp_bad_user.json().get("detail", resp_bad_user.json().get("message", ""))
        msg_bad_pass = resp_bad_pass.json().get("detail", resp_bad_pass.json().get("message", ""))
        assert msg_bad_user == msg_bad_pass, (
            f"Different error messages reveal user existence: "
            f"'{msg_bad_user}' vs '{msg_bad_pass}'"
        )


class TestBruteForceResilience:
    """Verify the API handles rapid failed login attempts."""

    def test_multiple_failed_logins(self, api_client):
        """Rapid failed logins should not cause server errors."""
        for _ in range(10):
            resp = api_client.post(
                "/api/auth/login",
                json={"username": "admin", "password": "wrong"},
            )
            # Should consistently return 401, not 500 or hang
            assert resp.status_code in (401, 429), (
                f"Unexpected status {resp.status_code} during brute force test"
            )


class TestSuspendedUserLogin:
    """Verify suspended/disabled users cannot authenticate."""

    def test_suspended_user_cannot_login(self, authed_api, api_client):
        """If a user is suspended, login must fail."""
        # Create a test user
        resp = authed_api.post(
            "/api/members",
            json={
                "username": "suspended_user",
                "email": "suspended@test.com",
                "role": "viewer",
                "is_active": False,
            },
        )
        if resp.status_code not in (200, 201):
            pytest.skip("Cannot create test user for suspension test")

        member_id = resp.json().get("id")

        # Try to login as suspended user
        login_resp = api_client.post(
            "/api/auth/login",
            json={"username": "suspended_user", "password": "any_password"},
        )
        assert login_resp.status_code in (401, 403)

        # Cleanup
        if member_id:
            authed_api.delete(f"/api/members/{member_id}")
