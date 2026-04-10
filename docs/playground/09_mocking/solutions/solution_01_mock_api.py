"""Solution: API Mocking."""

import pytest
import httpx
from ankole.driver.api_mock import APIMocker


@pytest.mark.api
class TestAPIMockingSolution:
    def test_mock_members(self):
        mocker = APIMocker()
        mocker.start()
        try:
            with mocker.mock_response("GET", "/api/members", json=[{"id": 1}]):
                resp = httpx.Client(base_url="http://testserver").get("/api/members")
                assert resp.json() == [{"id": 1}]
        finally:
            mocker.stop()

    def test_network_error(self):
        mocker = APIMocker()
        mocker.start()
        try:
            with mocker.simulate_network_error("POST", "/api/members"):
                with pytest.raises(ConnectionError):
                    httpx.Client(base_url="http://testserver").post("/api/members")
        finally:
            mocker.stop()
