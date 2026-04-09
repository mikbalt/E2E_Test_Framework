"""Project approval step factories for workspace flows."""

from ankole.flows.base import Step


def create_project(
    name: str,
    description: str = "",
    required_approvals: int = 3,
    base_url: str = "",
) -> Step:
    """Step: create a new project."""

    def _action(ctx):
        from ankole.pages.web.project_approval_page import ProjectApprovalPage

        page = ProjectApprovalPage(ctx.driver, ctx.evidence, base_url)
        page.goto()
        page.create_project(name, description, required_approvals)
        ctx.set("project_page", page)

    return Step(f"Create project: {name}", _action)


def approve_as(
    project_name: str,
    username: str,
    password: str,
    comment: str = "",
    base_url: str = "",
) -> Step:
    """Step: login as approver and approve the current step."""

    def _action(ctx):
        from ankole.pages.web.login_page import LoginPage
        from ankole.pages.web.project_approval_page import ProjectApprovalPage

        login = LoginPage(ctx.driver, ctx.evidence, base_url)
        login.goto()
        login.login(username, password)

        page = ProjectApprovalPage(ctx.driver, ctx.evidence, base_url)
        page.goto()
        page.open_project(project_name)
        page.approve_step(comment or f"Approved by {username}")

    return Step(f"Approve as {username}", _action)


def verify_project_status(
    project_name: str, expected_status: str, base_url: str = ""
) -> Step:
    """Step: verify a project's status."""

    def _action(ctx):
        from ankole.pages.web.project_approval_page import ProjectApprovalPage

        page = ProjectApprovalPage(ctx.driver, ctx.evidence, base_url)
        page.goto()
        actual = page.get_project_status(project_name)
        assert expected_status.lower() in actual.lower(), (
            f"Expected status '{expected_status}' for {project_name}, "
            f"got '{actual}'"
        )

    return Step(
        f"Verify project status: {expected_status}", _action
    )
