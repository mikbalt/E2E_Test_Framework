"""Member management step factories for workspace flows."""

from ankole.flows.base import Step


def create_member(
    username: str,
    email: str,
    password: str,
    role: str = "member",
    base_url: str = "",
) -> Step:
    """Step: create a new member."""

    def _action(ctx):
        from ankole.pages.web.member_management_page import MemberManagementPage

        page = MemberManagementPage(ctx.driver, ctx.evidence, base_url)
        page.goto()
        page.create_member(username, email, password, role)
        ctx.set("member_page", page)

    return Step(f"Create member: {username}", _action)


def delete_member(username: str, base_url: str = "") -> Step:
    """Step: delete a member."""

    def _action(ctx):
        from ankole.pages.web.member_management_page import MemberManagementPage

        page = ctx.get("member_page") or MemberManagementPage(
            ctx.driver, ctx.evidence, base_url
        )
        page.goto()
        page.delete_member(username)

    return Step(f"Delete member: {username}", _action)


def suspend_member(username: str, base_url: str = "") -> Step:
    """Step: suspend a member."""

    def _action(ctx):
        from ankole.pages.web.member_management_page import MemberManagementPage

        page = ctx.get("member_page") or MemberManagementPage(
            ctx.driver, ctx.evidence, base_url
        )
        page.goto()
        page.suspend_member(username)

    return Step(f"Suspend member: {username}", _action)


def reactivate_member(username: str, base_url: str = "") -> Step:
    """Step: reactivate a suspended member."""

    def _action(ctx):
        from ankole.pages.web.member_management_page import MemberManagementPage

        page = ctx.get("member_page") or MemberManagementPage(
            ctx.driver, ctx.evidence, base_url
        )
        page.goto()
        page.reactivate_member(username)

    return Step(f"Reactivate member: {username}", _action)


def verify_member_exists(username: str, base_url: str = "") -> Step:
    """Step: verify a member appears in the table."""

    def _action(ctx):
        from ankole.pages.web.member_management_page import MemberManagementPage

        page = ctx.get("member_page") or MemberManagementPage(
            ctx.driver, ctx.evidence, base_url
        )
        page.goto()
        assert page.is_member_in_table(username), (
            f"Member '{username}' not found in table"
        )

    return Step(f"Verify member exists: {username}", _action)


def verify_member_status(
    username: str, expected_status: str, base_url: str = ""
) -> Step:
    """Step: verify a member's status badge."""

    def _action(ctx):
        from ankole.pages.web.member_management_page import MemberManagementPage

        page = ctx.get("member_page") or MemberManagementPage(
            ctx.driver, ctx.evidence, base_url
        )
        page.goto()
        actual = page.get_member_status(username)
        assert expected_status.lower() in actual.lower(), (
            f"Expected status '{expected_status}' for {username}, got '{actual}'"
        )

    return Step(
        f"Verify {username} status: {expected_status}", _action
    )
