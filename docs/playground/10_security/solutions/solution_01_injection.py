"""Solution: Security Testing."""

import pytest
from ankole.driver.api_driver import APIDriver
from ankole.testing.security import (
    SecurityHeadersReport,
    test_injection_resilience,
    test_auth_endpoints_require_token,
)


@pytest.fixture
def api(playground_config):
    cfg = playground_config.get("workspace", {}).get("api", {})
    driver = APIDriver(base_url=cfg.get("base_url", "http://localhost:8000"))
    driver.start()
    driver.login("admin", "admin123")
    yield driver
    driver.close()


@pytest.mark.api
@pytest.mark.security
class TestSecuritySolution:
    def test_injection(self, api):
        assert len(test_injection_resilience(api, "/api/members", "username")) == 0

    def test_headers(self, api):
        resp = api.get("/api/members")
        report = SecurityHeadersReport.from_response("/api/members", resp)
        report.assert_secure(allow_missing=[
            "Strict-Transport-Security", "Content-Security-Policy", "Referrer-Policy",
        ])
