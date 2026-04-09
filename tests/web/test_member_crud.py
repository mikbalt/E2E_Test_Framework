"""Web UI tests for member CRUD operations."""

import pytest

from ankole.pages.web.login_page import LoginPage
from ankole.pages.web.member_management_page import MemberManagementPage
from tests.test_data import MemberManagementData


@pytest.mark.web
class TestMemberCRUD:
    """Test member create, read, delete operations."""

    @pytest.fixture(autouse=True)
    def setup(self, web_driver, base_url):
        self.driver = web_driver
        self.td = MemberManagementData.from_env()
        login = LoginPage(self.driver, base_url=base_url)
        login.goto()
        login.login(self.td.admin_username, self.td.admin_password)
        self.page = MemberManagementPage(self.driver, base_url=base_url)

    def test_create_member(self):
        """Should create a new member and show in table."""
        self.page.goto()
        self.page.create_member(
            self.td.member_username,
            self.td.member_email,
            self.td.member_password,
            self.td.member_role,
        )
        assert self.page.is_member_in_table(self.td.member_username)

    def test_members_table_displays(self):
        """Members table should render with data."""
        self.page.goto()
        data = self.page.get_members_table()
        assert len(data) > 0, "Members table should have at least one row"

    @pytest.mark.depends_on("test_create_member")
    def test_delete_member(self):
        """Should delete a member from the table."""
        self.page.goto()
        # Create first, then delete
        self.page.create_member(
            "delete_me_e2e",
            "delete_me@example.com",
            "pass123",
        )
        self.page.goto()
        self.page.delete_member("delete_me_e2e")
        self.page.goto()
        assert not self.page.is_member_in_table("delete_me_e2e")
