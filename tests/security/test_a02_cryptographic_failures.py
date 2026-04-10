"""A02:2021 - Cryptographic Failures.

Tests for JWT algorithm confusion, weak secrets, and sensitive data exposure.
"""

import base64
import json

import pytest

pytestmark = [pytest.mark.security, pytest.mark.owasp]


class TestJWTAlgorithm:
    """Verify JWT algorithm enforcement."""

    def _make_jwt(self, payload: dict, header: dict | None = None) -> str:
        """Build a manually crafted JWT (unsigned or with none algo)."""
        hdr = header or {"alg": "none", "typ": "JWT"}
        h = base64.urlsafe_b64encode(json.dumps(hdr).encode()).rstrip(b"=").decode()
        p = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
        return f"{h}.{p}."

    def test_algo_none_rejected(self, api_client):
        """JWT with alg=none must be rejected."""
        token = self._make_jwt({"sub": "admin", "exp": 9999999999})
        api_client._token = token
        resp = api_client.get("/api/members")
        assert resp.status_code == 401

    def test_wrong_algorithm_rejected(self, api_client):
        """JWT signed with unexpected algorithm must be rejected."""
        token = self._make_jwt(
            {"sub": "admin", "exp": 9999999999},
            header={"alg": "HS384", "typ": "JWT"},
        )
        api_client._token = token
        resp = api_client.get("/api/members")
        assert resp.status_code == 401

    def test_wrong_secret_rejected(self, api_client):
        """JWT signed with wrong secret must be rejected."""
        try:
            import jwt

            token = jwt.encode(
                {"sub": "admin", "exp": 9999999999},
                "wrong-secret-key",
                algorithm="HS256",
            )
            api_client._token = token
            resp = api_client.get("/api/members")
            assert resp.status_code == 401
        except ImportError:
            pytest.skip("PyJWT not installed")


class TestSensitiveDataExposure:
    """Verify sensitive data is not leaked in responses."""

    def test_login_response_has_no_password(self, api_client):
        """Login response must not contain the password field."""
        resp = api_client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        if resp.status_code == 200:
            data = resp.json()
            assert "password" not in data
            # Check token payload doesn't contain password
            token = data.get("access_token", "")
            if token and token.count(".") == 2:
                payload_b64 = token.split(".")[1]
                # Add padding
                payload_b64 += "=" * (4 - len(payload_b64) % 4)
                payload = json.loads(base64.urlsafe_b64decode(payload_b64))
                assert "password" not in payload
