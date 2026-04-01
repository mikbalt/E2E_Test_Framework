"""
[E2E][e-admin][Customer Key Ceremony] Import — Flow-based version

Precondition: CKC Generate & Export must be completed first (KCPs exist).

Scenario:
    Given  eAdmin launched and connected to HSM (post CKC Generate & Export)
    When   user starts Customer Key Ceremony
    And    accepts Terms & Conditions
    And    Admin logs in with password
    And    declines to recreate KCPs (reuse existing)
    And    selects IMPORT mode
    And    KCP1 logs in (combobox), imports component, selects key attributes
    And    KCP2 logs in, imports component
    And    KCP3 logs in, imports final component with key configuration
    Then   CKC Import completes successfully

Run:
    pytest tests/ui/e_admin/test_TC-XXXXX_Flow_CustomerKeyCeremonyImport.py -v -s
"""

import logging

import allure
import pytest

from sphere_e2e_test_framework.flows.base import FlowContext
from sphere_e2e_test_framework.flows.e_admin.customer_key_ceremony import (
    customer_key_ceremony_import_flow,
)
from tests.test_data import CustomerKeyCeremonyImportData

logger = logging.getLogger(__name__)


@allure.epic("Sphere HSM Idemia - E2E Tests - E-Admin")
@allure.feature("Customer Key Ceremony")
@allure.suite("eAdmin-Tier1 Journeys")
@allure.tag("e-admin", "windows", "ui", "customer-key-ceremony", "import", "flow")
@pytest.mark.e_admin
@pytest.mark.flow
class TestCustomerKeyCeremonyImportFlow:

    @pytest.fixture(autouse=True)
    def setup(self, e_admin_driver, evidence):
        self.driver = e_admin_driver
        self.evidence = evidence
        self.td = CustomerKeyCeremonyImportData.from_env()
        yield

    @allure.story("User performs Customer Key Ceremony Import via E-Admin")
    @allure.title("[E2E][e-admin][CKC] Customer Key Ceremony — Import (Flow)")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical
    @pytest.mark.order(3)
    def test_customer_key_ceremony_import(self):
        """Full CKC Import: connect, reuse KCPs, import components per KCP, finalize."""
        ctx = FlowContext(self.driver, self.evidence, self.td)
        customer_key_ceremony_import_flow.run(ctx)
