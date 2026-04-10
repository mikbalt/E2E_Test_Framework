"""Web UI tests for dashboard and navigation."""

import pytest

from ankole.pages.web.login_page import LoginPage
from ankole.pages.web.dashboard_page import DashboardPage
from tests.test_data import LoginData


@pytest.mark.web
class TestDashboardNavigation:
    """Test dashboard display and sidebar navigation."""

    @pytest.fixture(autouse=True)
    def setup(self, web_driver, base_url):
        self.driver = web_driver
        self.base_url = base_url
        td = LoginData.from_env()
        login = LoginPage(self.driver, base_url=base_url)
        login.goto()
        login.login(td.valid_username, td.valid_password)
        self.dashboard = DashboardPage(self.driver, base_url=base_url)

    @pytest.mark.smoke
    def test_dashboard_loads(self):
        """Dashboard should display after login."""
        self.dashboard.goto()
        assert "dashboard" in self.driver.url.lower()

    def test_dashboard_stats_visible(self):
        """Dashboard should show statistics."""
        self.dashboard.goto()
        stats = self.dashboard.get_stats()
        assert len(stats) > 0, "Dashboard should display at least one stat"

    def test_navigate_to_members(self):
        """Sidebar link should navigate to members page."""
        self.dashboard.goto()
        self.dashboard.navigate_to_members()
        assert "members" in self.driver.url.lower()

    def test_navigate_to_projects(self):
        """Sidebar link should navigate to projects page."""
        self.dashboard.goto()
        self.dashboard.navigate_to_projects()
        assert "projects" in self.driver.url.lower()
