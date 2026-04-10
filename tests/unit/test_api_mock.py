"""Unit tests for API Mocking module."""

import pytest


class TestAPIMocker:
    """Tests for APIMocker (respx-based)."""

    def test_mock_response(self):
        import httpx
        from ankole.driver.api_mock import APIMocker

        mocker = APIMocker()
        mocker.start()
        try:
            with mocker.mock_response("GET", "/api/members", json=[{"id": 1}]):
                client = httpx.Client(base_url="http://testserver")
                resp = client.get("/api/members")
                assert resp.status_code == 200
                assert resp.json() == [{"id": 1}]
        finally:
            mocker.stop()

    def test_simulate_network_error(self):
        import httpx
        from ankole.driver.api_mock import APIMocker

        mocker = APIMocker()
        mocker.start()
        try:
            with mocker.simulate_network_error("GET", "/api/fail"):
                client = httpx.Client(base_url="http://testserver")
                with pytest.raises(ConnectionError):
                    client.get("/api/fail")
        finally:
            mocker.stop()


class TestBrowserMocker:
    """Tests for BrowserMocker (Playwright route-based)."""

    def test_intercept_registers_route(self):
        from unittest.mock import MagicMock
        from ankole.driver.api_mock import BrowserMocker

        mock_page = MagicMock()
        mocker = BrowserMocker(mock_page)
        mocker.intercept("GET", "**/api/test", json={"ok": True})

        mock_page.route.assert_called_once()
        assert "**/api/test" in mocker._routes

    def test_clear_all(self):
        from unittest.mock import MagicMock
        from ankole.driver.api_mock import BrowserMocker

        mock_page = MagicMock()
        mocker = BrowserMocker(mock_page)
        mocker.intercept("GET", "**/api/a", json={})
        mocker.intercept("POST", "**/api/b", json={})
        assert len(mocker._routes) == 2

        mocker.clear_all()
        assert len(mocker._routes) == 0
        assert mock_page.unroute.call_count == 2
