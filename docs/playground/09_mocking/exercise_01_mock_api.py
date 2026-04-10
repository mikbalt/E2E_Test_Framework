"""Exercise: API Mocking.

TODO: Use APIMocker to mock HTTP responses.
"""

import pytest
import httpx

from ankole.driver.api_mock import APIMocker


@pytest.mark.api
class TestAPIMocking:
    """API mocking exercises."""

    def test_mock_members_list(self):
        """TODO: Mock GET /api/members to return a custom list."""
        mocker = APIMocker()
        mocker.start()
        try:
            mock_data = [{"id": 1, "username": "mock_user"}]
            with mocker.mock_response("GET", "/api/members", json=mock_data):
                client = httpx.Client(base_url="http://testserver")
                resp = client.get("/api/members")
                assert resp.status_code == 200
                assert resp.json() == mock_data
        finally:
            mocker.stop()

    def test_mock_network_error(self):
        """TODO: Simulate a network error on POST."""
        mocker = APIMocker()
        mocker.start()
        try:
            with mocker.simulate_network_error("POST", "/api/members"):
                client = httpx.Client(base_url="http://testserver")
                with pytest.raises(ConnectionError):
                    client.post("/api/members", json={})
        finally:
            mocker.stop()

    def test_mock_custom_status(self):
        """TODO: Mock a 404 response."""
        mocker = APIMocker()
        mocker.start()
        try:
            with mocker.mock_response("GET", "/api/missing", status_code=404, json={"error": "not found"}):
                client = httpx.Client(base_url="http://testserver")
                resp = client.get("/api/missing")
                assert resp.status_code == 404
        finally:
            mocker.stop()
