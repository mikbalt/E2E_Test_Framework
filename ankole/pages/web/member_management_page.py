"""Member management page object for the Workspace web application."""

import logging

from ankole.pages.web.base_web_page import BaseWebPage

logger = logging.getLogger(__name__)


class MemberManagementPage(BaseWebPage):
    """Page object for member CRUD + suspend/reactivate."""

    MEMBERS_TABLE = "#members-table"
    ADD_MEMBER_BTN = "#add-member-btn"
    USERNAME_INPUT = "#username"
    EMAIL_INPUT = "#email"
    PASSWORD_INPUT = "#password"
    ROLE_SELECT = "#role"
    SUBMIT_BTN = "#submit-btn"
    CONFIRM_DELETE_BTN = "#confirm-delete-btn"
    SEARCH_INPUT = "#search-input"

    def goto(self) -> "MemberManagementPage":
        """Navigate to member management page."""
        self.navigate_to("/members")
        return self

    def get_members_table(self) -> list[dict[str, str]]:
        """Extract member data from the table."""
        return self.driver.get_table_data(self.MEMBERS_TABLE)

    def click_add_member(self) -> None:
        """Click the Add Member button."""
        self.driver.click(self.ADD_MEMBER_BTN)

    def fill_member_form(
        self,
        username: str,
        email: str,
        password: str,
        role: str = "member",
    ) -> None:
        """Fill the member creation/edit form."""
        with self._web_step(f"Fill member form: {username}"):
            self.driver.fill(self.USERNAME_INPUT, username)
            self.driver.fill(self.EMAIL_INPUT, email)
            if self.driver.is_visible(self.PASSWORD_INPUT):
                self.driver.fill(self.PASSWORD_INPUT, password)
            self.driver.select_option(self.ROLE_SELECT, role)

    def submit_form(self) -> None:
        """Submit the member form."""
        self.driver.click(self.SUBMIT_BTN)

    def create_member(
        self,
        username: str,
        email: str,
        password: str,
        role: str = "member",
    ) -> None:
        """Full create member flow."""
        with self._web_step(f"Create member: {username}"):
            self.click_add_member()
            self.fill_member_form(username, email, password, role)
            self.submit_form()
        logger.info(f"Member created: {username}")

    def delete_member(self, username: str) -> None:
        """Delete a member by clicking their delete button."""
        with self._web_step(f"Delete member: {username}"):
            row = self.driver.page.locator(
                f"{self.MEMBERS_TABLE} tr:has-text('{username}')"
            )
            row.locator(".delete-btn").click()
            if self.driver.is_visible(self.CONFIRM_DELETE_BTN):
                self.driver.click(self.CONFIRM_DELETE_BTN)
        logger.info(f"Member deleted: {username}")

    def suspend_member(self, username: str) -> None:
        """Suspend a member by clicking their suspend button."""
        with self._web_step(f"Suspend member: {username}"):
            row = self.driver.page.locator(
                f"{self.MEMBERS_TABLE} tr:has-text('{username}')"
            )
            row.locator(".suspend-btn").click()
        logger.info(f"Member suspended: {username}")

    def reactivate_member(self, username: str) -> None:
        """Reactivate a suspended member."""
        with self._web_step(f"Reactivate member: {username}"):
            row = self.driver.page.locator(
                f"{self.MEMBERS_TABLE} tr:has-text('{username}')"
            )
            row.locator(".reactivate-btn").click()
        logger.info(f"Member reactivated: {username}")

    def is_member_in_table(self, username: str) -> bool:
        """Check if a member is visible in the table."""
        return self.driver.page.locator(
            f"{self.MEMBERS_TABLE} tr:has-text('{username}')"
        ).count() > 0

    def get_member_status(self, username: str) -> str:
        """Get the status badge text for a member."""
        row = self.driver.page.locator(
            f"{self.MEMBERS_TABLE} tr:has-text('{username}')"
        )
        return row.locator(".badge").text_content() or ""
