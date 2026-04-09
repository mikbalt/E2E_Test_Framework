"""Web UI tests for member suspend/reactivate using flow orchestration."""

import pytest

from ankole.flows.base import FlowContext
from ankole.flows.workspace.member_management import (
    suspend_member_flow,
    reactivate_member_flow,
    add_member_flow,
)
from tests.test_data import SuspendReactivateData


@pytest.mark.web
@pytest.mark.flow
class TestMemberSuspendReactivate:
    """Test suspend/reactivate member flows."""

    @pytest.fixture(autouse=True)
    def setup(self, web_driver, base_url, evidence):
        self.driver = web_driver
        self.base_url = base_url
        self.evidence = evidence
        self.td = SuspendReactivateData.from_env()

    def _ensure_member_exists(self):
        """Prerequisite: ensure the test member exists."""
        ctx = FlowContext(self.driver, self.evidence, self.td)
        flow = add_member_flow(
            self.td.admin_username,
            self.td.admin_password,
            self.td.member_username,
            self.td.member_email,
            self.td.member_password,
            base_url=self.base_url,
        )
        flow.run(ctx)

    @pytest.mark.critical
    def test_suspend_member(self):
        """Flow: suspend a member and verify status changes."""
        self._ensure_member_exists()

        ctx = FlowContext(self.driver, self.evidence, self.td)
        flow = suspend_member_flow(
            self.td.admin_username,
            self.td.admin_password,
            self.td.member_username,
            base_url=self.base_url,
        )
        flow.run(ctx)

    @pytest.mark.critical
    def test_reactivate_member(self):
        """Flow: reactivate a suspended member."""
        self._ensure_member_exists()

        # First suspend
        ctx = FlowContext(self.driver, self.evidence, self.td)
        suspend_flow = suspend_member_flow(
            self.td.admin_username,
            self.td.admin_password,
            self.td.member_username,
            base_url=self.base_url,
        )
        suspend_flow.run(ctx)

        # Then reactivate
        ctx2 = FlowContext(self.driver, self.evidence, self.td)
        react_flow = reactivate_member_flow(
            self.td.admin_username,
            self.td.admin_password,
            self.td.member_username,
            base_url=self.base_url,
        )
        react_flow.run(ctx2)
