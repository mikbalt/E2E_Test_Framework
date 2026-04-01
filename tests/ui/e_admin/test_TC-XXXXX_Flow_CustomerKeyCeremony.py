"""
[E2E][e-admin][Customer Key Ceremony] Generate & Export — Flow-based version

Precondition: FIPS Key Ceremony must be completed first.

Scenario:
    Given  eAdmin launched and connected to HSM (post FIPS key ceremony)
    When   user starts Customer Key Ceremony
    And    accepts Terms & Conditions
    And    Admin logs in with password
    And    creates 3 Key Custodian Parties (KCP1, KCP2, KCP3)
    And    selects GENERATE_AND_EXPORT mode
    And    configures key (AES 256-bit, ZCMK_EXP)
    And    generates the key
    And    each KCP logs in, reads export values (secret + KCV)
    Then   key summary is verified and CKC completes

Run:
    pytest tests/ui/e_admin/test_TC-XXXXX_Flow_CustomerKeyCeremony.py -v -s
"""

import logging

import allure
import pytest

from sphere_e2e_test_framework.flows.base import FlowContext
from sphere_e2e_test_framework.flows.e_admin.customer_key_ceremony import (
    customer_key_ceremony_flow,
)
from tests.test_data import CustomerKeyCeremonyData

logger = logging.getLogger(__name__)


@allure.epic("Sphere HSM Idemia - E2E Tests - E-Admin")
@allure.feature("Customer Key Ceremony")
@allure.suite("eAdmin-Tier1 Journeys")
@allure.tag("e-admin", "windows", "ui", "customer-key-ceremony", "flow")
@pytest.mark.e_admin
@pytest.mark.flow
class TestCustomerKeyCeremonyFlow:

    @pytest.fixture(autouse=True)
    def setup(self, e_admin_driver, evidence):
        self.driver = e_admin_driver
        self.evidence = evidence
        self.td = CustomerKeyCeremonyData.from_env()
        yield

    @allure.story("User performs Customer Key Ceremony (Generate & Export) via E-Admin")
    @allure.title("[E2E][e-admin][CKC] Customer Key Ceremony — Generate & Export (Flow)")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical
    @pytest.mark.order(2)
    def test_customer_key_ceremony(self):
        """Full CKC: connect, create KCPs, generate key, export per KCP, verify summary."""
        ctx = FlowContext(self.driver, self.evidence, self.td)
        customer_key_ceremony_flow.run(ctx)

        # Log exported values for traceability
        export_values = ctx.get("ckc_export_values")
        if export_values:
            for ev in export_values:
                logger.info(f"Export — {ev['username']}: secret={ev['secret']}, kcv={ev['secret_kcv']}")
            allure.attach(
                str(export_values),
                name="ckc_export_values",
                attachment_type=allure.attachment_type.TEXT,
            )

        # Log key summary
        key_summary = ctx.get("ckc_key_summary")
        if key_summary:
            logger.info(f"Key summary: {key_summary}")
            allure.attach(
                str(key_summary),
                name="ckc_key_summary",
                attachment_type=allure.attachment_type.TEXT,
            )
