"""API tests for authentication endpoints."""

import pytest


@pytest.mark.api
class TestAuth:
    """Test /api/auth endpoints."""

    def test_login_success(self, api_client):
        """Valid credentials should return a JWT token."""
        resp = api_client.login("admin", "admin123")
        resp.assert_status(200)
        resp.assert_json_key("access_token")
        assert api_client.is_authenticated

    def test_login_invalid_credentials(self, api_client):
        """Invalid credentials should return 401."""
        resp = api_client.login("admin", "wrongpassword")
        resp.assert_status(401)
        assert not api_client.is_authenticated

    def test_login_nonexistent_user(self, api_client):
        """Non-existent user should return 401."""
        resp = api_client.login("nonexistent", "password")
        resp.assert_status(401)

    def test_logout(self, authed_api):
        """Logout should clear the auth token."""
        assert authed_api.is_authenticated
        authed_api.logout()
        assert not authed_api.is_authenticated

    @pytest.mark.smoke
    def test_auth_endpoint_available(self, api_client):
        """Auth endpoint should be reachable."""
        resp = api_client.post("/api/auth/login", json={
            "username": "admin", "password": "admin123"
        })
        assert resp.status_code in (200, 401, 422)
