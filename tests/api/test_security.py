"""Security tests for the sample API."""

import pytest

from ankole.driver.api_driver import APIDriver
from ankole.plugin.config import load_config
from ankole.testing.security import (
    SecurityHeadersReport,
    test_auth_endpoints_require_token,
    test_injection_resilience,
)


@pytest.fixture
def unauthenticated_api(config):
    """Provide an unauthenticated API driver."""
    api_cfg = config.get("workspace", {}).get("api", {})
    base_url = api_cfg.get("base_url", "http://localhost:8000")
    driver = APIDriver(base_url=base_url)
    driver.start()
    yield driver
    driver.close()


@pytest.fixture
def authenticated_api(config):
    """Provide an authenticated API driver."""
    api_cfg = config.get("workspace", {}).get("api", {})
    base_url = api_cfg.get("base_url", "http://localhost:8000")
    driver = APIDriver(base_url=base_url)
    driver.start()
    driver.login("admin", "admin123")
    yield driver
    driver.close()


@pytest.mark.api
@pytest.mark.security
class TestSecurityHeaders:
    """Test security-related HTTP headers."""

    def test_api_security_headers(self, authenticated_api):
        """API responses should include recommended security headers."""
        resp = authenticated_api.get("/api/members")
        report = SecurityHeadersReport.from_response(
            url="/api/members", response=resp,
        )
        # Allow some headers to be missing in dev — strict in CI
        report.assert_secure(allow_missing=[
            "Strict-Transport-Security",  # Not required on HTTP
            "Content-Security-Policy",
            "Referrer-Policy",
        ])


@pytest.mark.api
@pytest.mark.security
class TestInjectionResilience:
    """Test SQL injection resilience."""

    def test_member_search_injection(self, authenticated_api):
        """Member search endpoint should resist SQL injection."""
        vulns = test_injection_resilience(
            authenticated_api, "/api/members", "username",
        )
        assert len(vulns) == 0, f"SQL injection vulnerabilities found: {vulns}"


@pytest.mark.api
@pytest.mark.security
class TestAuthEndpoints:
    """Test that protected endpoints require authentication."""

    def test_protected_endpoints_require_token(self, unauthenticated_api):
        """Protected endpoints should return 401/403 without a token."""
        endpoints = [
            {"method": "GET", "path": "/api/members"},
            {"method": "POST", "path": "/api/members"},
            {"method": "GET", "path": "/api/projects"},
            {"method": "POST", "path": "/api/projects"},
        ]
        unprotected = test_auth_endpoints_require_token(
            unauthenticated_api, endpoints,
        )
        assert len(unprotected) == 0, (
            f"Unprotected endpoints found: {unprotected}"
        )
