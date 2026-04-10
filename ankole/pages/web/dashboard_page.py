"""Dashboard page object for the Workspace web application."""

import logging

from ankole.pages.web.base_web_page import BaseWebPage

logger = logging.getLogger(__name__)


class DashboardPage(BaseWebPage):
    """Page object for the dashboard page."""

    STATS_MEMBERS = "#stat-members"
    STATS_PROJECTS = "#stat-projects"
    STATS_APPROVALS = "#stat-approvals"

    def goto(self) -> "DashboardPage":
        """Navigate to the dashboard."""
        self.navigate_to("/dashboard")
        return self

    def get_stats(self) -> dict[str, str]:
        """Get dashboard statistics."""
        stats = {}
        for key, selector in [
            ("members", self.STATS_MEMBERS),
            ("projects", self.STATS_PROJECTS),
            ("approvals", self.STATS_APPROVALS),
        ]:
            if self.driver.is_visible(selector):
                stats[key] = self.driver.get_text(selector).strip()
        return stats

    def navigate_to_members(self) -> None:
        """Click sidebar link to Members page."""
        self.click_sidebar_link("Members")

    def navigate_to_projects(self) -> None:
        """Click sidebar link to Projects page."""
        self.click_sidebar_link("Projects")

    def navigate_to_roles(self) -> None:
        """Click sidebar link to Roles page."""
        self.click_sidebar_link("Roles")
