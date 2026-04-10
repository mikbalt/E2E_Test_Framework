"""Project approval workflow flows for workspace application.

Pre-composed flows for the multi-step project approval process:
    create_project_flow     — login, create project
    full_approval_flow      — create project + all approval steps
"""

from ankole.flows.base import Flow
from ankole.steps.workspace.login import full_login, logout
from ankole.steps.workspace.project_approval import (
    create_project,
    approve_as,
    verify_project_status,
)


def create_project_flow(
    admin_user: str,
    admin_pass: str,
    project_name: str,
    description: str = "",
    required_approvals: int = 3,
    base_url: str = "",
) -> Flow:
    """Flow: login as admin, create a project."""
    return Flow(
        f"Create Project: {project_name}",
        steps=[
            full_login(admin_user, admin_pass, base_url),
            create_project(
                project_name, description, required_approvals, base_url,
            ),
            verify_project_status(project_name, "pending", base_url),
        ],
        cleanup_steps=[logout(base_url)],
    )


def full_approval_flow(
    admin_user: str,
    admin_pass: str,
    project_name: str,
    approvers: list[dict[str, str]],
    description: str = "",
    base_url: str = "",
) -> Flow:
    """Flow: create project, then have each approver approve it.

    Args:
        admin_user: Admin username for project creation.
        admin_pass: Admin password.
        project_name: Name of the project.
        approvers: List of dicts with 'username' and 'password' keys.
        description: Project description.
        base_url: Base URL of the web application.
    """
    steps = [
        full_login(admin_user, admin_pass, base_url),
        create_project(
            project_name, description, len(approvers), base_url,
        ),
    ]

    for approver in approvers:
        steps.append(
            approve_as(
                project_name,
                approver["username"],
                approver["password"],
                base_url=base_url,
            )
        )

    steps.append(
        verify_project_status(project_name, "approved", base_url)
    )

    return Flow(
        f"Full Approval: {project_name}",
        steps=steps,
    )
