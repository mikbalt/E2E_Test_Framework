"""Role management page object for the Workspace web application."""

import logging

from ankole.pages.web.base_web_page import BaseWebPage

logger = logging.getLogger(__name__)


class RoleManagementPage(BaseWebPage):
    """Page object for role CRUD."""

    ROLES_TABLE = "#roles-table"
    ADD_ROLE_BTN = "#add-role-btn"
    ROLE_NAME_INPUT = "#role-name"
    ROLE_DESC_INPUT = "#role-description"
    SUBMIT_BTN = "#submit-btn"

    def goto(self) -> "RoleManagementPage":
        """Navigate to role management page."""
        self.navigate_to("/roles")
        return self

    def get_roles_table(self) -> list[dict[str, str]]:
        """Extract role data from the table."""
        return self.driver.get_table_data(self.ROLES_TABLE)

    def create_role(self, name: str, description: str = "") -> None:
        """Create a new role."""
        with self._web_step(f"Create role: {name}"):
            self.driver.click(self.ADD_ROLE_BTN)
            self.driver.fill(self.ROLE_NAME_INPUT, name)
            if description:
                self.driver.fill(self.ROLE_DESC_INPUT, description)
            self.driver.click(self.SUBMIT_BTN)
        logger.info(f"Role created: {name}")

    def delete_role(self, name: str) -> None:
        """Delete a role by name."""
        with self._web_step(f"Delete role: {name}"):
            self.driver.click_in_row(self.ROLES_TABLE, name, ".delete-btn")
        logger.info(f"Role deleted: {name}")
