"""Project approval page object for the Workspace web application."""

import logging

from ankole.pages.web.base_web_page import BaseWebPage

logger = logging.getLogger(__name__)


class ProjectApprovalPage(BaseWebPage):
    """Page object for project CRUD and multi-step approval workflow."""

    PROJECTS_TABLE = "#projects-table"
    ADD_PROJECT_BTN = "#add-project-btn"
    PROJECT_NAME_INPUT = "#project-name"
    PROJECT_DESC_INPUT = "#project-description"
    REQUIRED_APPROVALS_INPUT = "#required-approvals"
    SUBMIT_BTN = "#submit-btn"
    APPROVE_BTN = "#approve-btn"
    REJECT_BTN = "#reject-btn"
    APPROVAL_COMMENT = "#approval-comment"
    APPROVAL_STEPS = ".approval-step"

    def goto(self) -> "ProjectApprovalPage":
        """Navigate to projects page."""
        self.navigate_to("/projects")
        return self

    def get_projects_table(self) -> list[dict[str, str]]:
        """Extract project data from the table."""
        return self.driver.get_table_data(self.PROJECTS_TABLE)

    def create_project(
        self,
        name: str,
        description: str = "",
        required_approvals: int = 3,
    ) -> None:
        """Create a new project."""
        with self._web_step(f"Create project: {name}"):
            self.driver.click(self.ADD_PROJECT_BTN)
            self.driver.fill(self.PROJECT_NAME_INPUT, name)
            if description:
                self.driver.fill(self.PROJECT_DESC_INPUT, description)
            self.driver.fill(
                self.REQUIRED_APPROVALS_INPUT, str(required_approvals)
            )
            self.driver.click(self.SUBMIT_BTN)
        logger.info(f"Project created: {name}")

    def open_project(self, name: str) -> None:
        """Click on a project to view its details."""
        self.driver.click(f"{self.PROJECTS_TABLE} tr:has-text('{name}') a")

    def approve_step(self, comment: str = "") -> None:
        """Approve the current pending step."""
        with self._web_step("Approve step"):
            if comment:
                self.driver.fill(self.APPROVAL_COMMENT, comment)
            self.driver.click(self.APPROVE_BTN)
        logger.info("Approval step completed")

    def reject_project(self, comment: str = "") -> None:
        """Reject the project."""
        with self._web_step("Reject project"):
            if comment:
                self.driver.fill(self.APPROVAL_COMMENT, comment)
            self.driver.click(self.REJECT_BTN)
        logger.info("Project rejected")

    def get_approval_steps(self) -> list[dict[str, str]]:
        """Get all approval step statuses."""
        return self.driver.get_elements_data(
            self.APPROVAL_STEPS,
            {
                "step": ".step-number",
                "status": ".step-status",
                "approver": ".step-approver",
            },
        )

    def get_project_status(self, name: str) -> str:
        """Get the status badge for a project."""
        return self.driver.get_text_in_row(self.PROJECTS_TABLE, name, ".badge")

    def full_approval_workflow(
        self,
        project_name: str,
        approvers: list[dict[str, str]],
        login_page,
    ) -> None:
        """Execute full multi-step approval workflow.

        Args:
            project_name: Name of the project to approve.
            approvers: List of dicts with 'username' and 'password'.
            login_page: LoginPage instance for re-authentication.
        """
        for i, approver in enumerate(approvers):
            with self._web_step(
                f"Approval step {i + 1} by {approver['username']}"
            ):
                login_page.goto()
                login_page.login(approver["username"], approver["password"])
                self.goto()
                self.open_project(project_name)
                self.approve_step(
                    comment=f"Approved by {approver['username']}"
                )
            logger.info(
                f"Step {i + 1} approved by {approver['username']}"
            )
