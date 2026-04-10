"""A05:2021 - Security Misconfiguration.

Tests for CORS, security headers, debug endpoints, version disclosure, and default creds.
"""

import pytest

from tests.security.payloads import DEFAULT_CREDENTIALS, REQUIRED_SECURITY_HEADERS

pytestmark = [pytest.mark.security, pytest.mark.owasp]


class TestCORS:
    """Cross-Origin Resource Sharing configuration tests."""

    def test_cors_no_wildcard(self, api_client):
        """Access-Control-Allow-Origin must not be wildcard '*'."""
        resp = api_client.get("/api/health")
        allow_origin = resp.headers.get("access-control-allow-origin", "")
        assert allow_origin != "*", "CORS wildcard '*' allows any origin"


class TestSecurityHeaders:
    """Verify security headers are present on API responses."""

    @pytest.mark.parametrize("header", REQUIRED_SECURITY_HEADERS)
    def test_security_header_present(self, api_client, header):
        """Required security header must be present."""
        resp = api_client.get("/api/health")
        # Note: many sample apps won't have all headers; this documents the gap
        assert header.lower() in {
            k.lower() for k in resp.headers
        }, f"Missing security header: {header}"


class TestDebugEndpoints:
    """Verify debug/admin endpoints are not exposed."""

    @pytest.mark.parametrize(
        "path",
        ["/debug", "/admin", "/_debug", "/api/debug", "/swagger.json", "/docs"],
    )
    def test_debug_endpoint_not_exposed(self, api_client, path):
        """Debug and admin endpoints must not be publicly accessible."""
        resp = api_client.get(path)
        # 404 or 401/403 are acceptable; 200 means it's exposed
        assert resp.status_code in (401, 403, 404, 405), (
            f"{path} returned {resp.status_code} — may be exposed"
        )


class TestServerVersionDisclosure:
    """Verify server does not disclose version information."""

    def test_no_server_version_header(self, api_client):
        """Server header should not reveal version details."""
        resp = api_client.get("/api/health")
        server = resp.headers.get("server", "")
        # Presence of version numbers is a concern
        import re

        version_pattern = re.compile(r"\d+\.\d+")
        assert not version_pattern.search(server), (
            f"Server header discloses version: {server}"
        )


class TestStackTraceExposure:
    """Verify error responses don't leak stack traces."""

    def test_invalid_json_no_stack_trace(self, api_client):
        """Malformed requests must not expose stack traces."""
        # Send raw malformed JSON
        client = api_client._client
        resp = client.post(
            "/api/auth/login",
            content=b"{{invalid json}}",
            headers={"Content-Type": "application/json"},
        )
        assert "Traceback" not in resp.text
        assert "File \"" not in resp.text


class TestDefaultCredentials:
    """Verify default/common credentials don't work."""

    @pytest.mark.parametrize("username,password", DEFAULT_CREDENTIALS)
    def test_default_creds_rejected(self, api_client, username, password):
        """Common default credentials must not grant access."""
        resp = api_client.post(
            "/api/auth/login",
            json={"username": username, "password": password},
        )
        # 401 means rejected; we only flag if status is 200
        if resp.status_code == 200:
            pytest.fail(
                f"Default credentials accepted: {username}/{password}"
            )
