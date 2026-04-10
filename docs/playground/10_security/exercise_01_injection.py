"""Exercise: Security Testing.

TODO: Test the sample API for common vulnerabilities.
"""

import pytest

from ankole.driver.api_driver import APIDriver
from ankole.testing.security import (
    SecurityHeadersReport,
    test_auth_endpoints_require_token,
    test_injection_resilience,
)


@pytest.fixture
def api(playground_config):
    cfg = playground_config.get("workspace", {}).get("api", {})
    driver = APIDriver(base_url=cfg.get("base_url", "http://localhost:8000"))
    driver.start()
    driver.login("admin", "admin123")
    yield driver
    driver.close()


@pytest.fixture
def unauth_api(playground_config):
    cfg = playground_config.get("workspace", {}).get("api", {})
    driver = APIDriver(base_url=cfg.get("base_url", "http://localhost:8000"))
    driver.start()
    yield driver
    driver.close()


@pytest.mark.api
@pytest.mark.security
class TestSecurityPlayground:
    """Security testing exercises."""

    def test_sql_injection_resilience(self, api):
        """TODO: Test the members endpoint for SQL injection."""
        vulns = test_injection_resilience(api, "/api/members", "username")
        assert len(vulns) == 0, f"Vulnerabilities found: {vulns}"

    def test_auth_required(self, unauth_api):
        """TODO: Verify protected endpoints reject unauthenticated requests."""
        endpoints = [
            {"method": "GET", "path": "/api/members"},
            {"method": "GET", "path": "/api/projects"},
        ]
        unprotected = test_auth_endpoints_require_token(unauth_api, endpoints)
        assert len(unprotected) == 0, f"Unprotected: {unprotected}"

    def test_security_headers(self, api):
        """TODO: Check security headers on API responses."""
        resp = api.get("/api/members")
        report = SecurityHeadersReport.from_response("/api/members", resp)
        # In development, some headers may be missing
        report.assert_secure(allow_missing=[
            "Strict-Transport-Security",
            "Content-Security-Policy",
            "Referrer-Policy",
        ])
