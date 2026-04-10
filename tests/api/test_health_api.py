"""API tests for health endpoint."""

import pytest


@pytest.mark.api
@pytest.mark.smoke
class TestHealthAPI:
    """Test /api/health endpoint."""

    def test_health_ok(self, api_client):
        """Health endpoint should return status ok without auth."""
        resp = api_client.get("/api/health")
        resp.assert_status(200)
        resp.assert_json_key("status", "ok")

    def test_health_includes_version(self, api_client):
        """Health response should include version info."""
        resp = api_client.get("/api/health")
        resp.assert_status(200)
        resp.assert_json_key("version")
