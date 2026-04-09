"""Web UI tests for multi-step project approval workflow."""

import pytest

from ankole.flows.base import FlowContext
from ankole.flows.workspace.project_approval import full_approval_flow
from tests.test_data import ProjectApprovalData


@pytest.mark.web
@pytest.mark.flow
@pytest.mark.critical
class TestProjectApprovalWorkflow:
    """Test the multi-step project approval workflow."""

    @pytest.fixture(autouse=True)
    def setup(self, web_driver, base_url, evidence):
        self.driver = web_driver
        self.base_url = base_url
        self.evidence = evidence
        self.td = ProjectApprovalData.from_env()

    def test_full_approval_workflow(self):
        """Create project and have all approvers approve it.

        This is the critical multi-step workflow test:
        1. Admin creates a project
        2. Approver 1 approves step 1
        3. Approver 2 approves step 2
        4. Approver 3 approves step 3
        5. Project status changes to 'approved'
        """
        approvers = [
            {"username": a.username, "password": a.password}
            for a in self.td.approvers
        ]

        ctx = FlowContext(self.driver, self.evidence, self.td)
        flow = full_approval_flow(
            admin_user=self.td.admin_username,
            admin_pass=self.td.admin_password,
            project_name=self.td.project_name,
            approvers=approvers,
            description=self.td.project_description,
            base_url=self.base_url,
        )
        flow.run(ctx)
