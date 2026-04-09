"""
Customer Key Ceremony (CKC) page object for E-Admin.

Handles the full CKC flow in both modes:
- Generate & Export: create KCPs, generate key, export per KCP, verify summary
- Import: reuse KCPs, import key components per KCP, configure key, finalize
"""

import logging

from sphere_e2e_test_framework.pages.e_admin.e_admin_base_page import EAdminBasePage, TIMEOUT

logger = logging.getLogger(__name__)


class CustomerKeyCeremonyPage(EAdminBasePage):
    """Customer Key Ceremony flow page object."""

    def start_ckc(self, step_name=None):
        """Click the Customer Key Ceremony button on the dashboard."""
        with self._step(step_name):
            self.driver.click_button(auto_id="btnCustomerKeyCeremony")
            logger.info("Customer Key Ceremony started")
        return self

    def login_admin(self, username, password, step_name=None):
        """Login as admin via password authentication during CKC."""
        with self._step(step_name):
            self.driver.click_radio(auto_id="rbPassword")
            self.driver.type_text(username, auto_id="1001")
            self.driver.type_text(
                password, auto_id="txtPassword", sensitive=True,
            )
            self.driver.click_button(auto_id="btnLogin")
            logger.info(f"Admin '{username}' logged in for CKC")
        return self

    def create_custodian_party(self, username, password, add_button_id,
                               step_name=None):
        """Create a Key Custodian Party account.

        Args:
            username: Custodian party username.
            password: Custodian party password.
            add_button_id: Button to open creation form (e.g. 'btnAdd1').
            step_name: Optional evidence step description.
        """
        with self._step(step_name):
            self.driver.click_button(auto_id=add_button_id)
            self.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="txtUsername",
            )
            self.driver.type_text(username, auto_id="txtUsername")
            self.driver.click_radio(auto_id="rbPass")
            self.driver.type_text(
                password, auto_id="txtPass", sensitive=True,
            )
            self.driver.type_text(
                password, auto_id="txtPassRepeat", sensitive=True,
            )
            self.driver.click_button(auto_id="btnCreate")
            self.dismiss_ok()
            logger.info(f"Custodian Party '{username}' created")
        return self

    def select_generate_and_export(self, step_name=None):
        """Select GENERATE_AND_EXPORT mode and proceed."""
        with self._step(step_name):
            self.driver.click_radio(auto_id="rbDisagree")
            self.driver.click_button(auto_id="btnNext")
            logger.info("GENERATE_AND_EXPORT mode selected")
        return self

    def configure_key(self, key_label, key_algo, key_length, key_usages,
                      cps_key_type, key_type=None, kcv_algo=None,
                      valid_date=None, step_name=None):
        """Configure key parameters for generation.

        Args:
            key_label: Key label text (e.g. 'CKC_E2E_1').
            key_algo: Key algorithm (e.g. 'AES').
            key_length: Key length (e.g. '256 bits').
            key_usages: List of key usage checkbox auto_ids to select,
                e.g. ['cb_TRANSPORT_KEY', 'cbUSAGE_SIGN', ...].
            cps_key_type: CPS key type / KCV Method (e.g. 'ZCMK_EXP').
            key_type: Key type (e.g. 'Permanent (stored in LKD)'). None = skip.
            kcv_algo: KCV algorithm (e.g. 'Standard_Algorithm'). None = skip.
            valid_date: Valid date string for dateTimePicker. None = skip.
            step_name: Optional evidence step description.
        """
        with self._step(step_name):
            self.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="txtKeyLabel",
            )
            self.driver.type_text(key_label, auto_id="txtKeyLabel")
            self.driver.click_combobox_item(auto_id="cbKeyAlgo", value=key_algo)
            self.driver.refresh_window()
            self.driver.click_combobox_item(auto_id="cbKeyLength", value=key_length)
            if key_type is not None:
                self.driver.select_combobox(auto_id="cbKeyType", value=key_type)

            # Key usage: click txtKeyUsage to open popup, check all at once, confirm
            self.driver.click_element(auto_id="txtKeyUsage")
            win = self.driver._active_window()
            for cb_id in key_usages:
                cb = win.child_window(auto_id=cb_id, control_type="CheckBox")
                cb.click_input()
            logger.info(f"Key usage checkboxes checked: {key_usages}")
            self.driver.click_button(auto_id="btnConfirm")

            if kcv_algo is not None:
                self.driver.select_combobox(auto_id="cbD0", value=kcv_algo)
            self.driver.select_combobox(auto_id="cbCpsKeyType", value=cps_key_type)
            if valid_date is not None:
                self.driver.select_combobox(auto_id="dateTimePicker", value=valid_date)
            logger.info(
                f"Key configured: label={key_label}, algo={key_algo}, "
                f"length={key_length}, usages={key_usages}, cps_type={cps_key_type}"
            )
        return self

    def generate_key(self, step_name=None):
        """Click Generate and dismiss confirmation dialog."""
        with self._step(step_name):
            self.driver.click_button(auto_id="btnCreate")
            self.dismiss_ok()
            logger.info("Key generated successfully")
        return self

    def accept_understanding(self, step_name=None):
        """Click 'Understand' radio and Next/Finalize button."""
        with self._step(step_name):
            self.driver.click_radio(auto_id="rbAgree")
            self.driver.click_button(auto_id="btnNext")
            logger.info("Understanding accepted")
        return self

    def login_custodian(self, username, password, step_name=None):
        """Login as Key Custodian Party for export phase.

        Same auth flow as login_admin but during the export phase.
        """
        with self._step(step_name):
            self.driver.click_radio(auto_id="rbPassword")
            self.driver.type_text(username, auto_id="1001")
            self.driver.type_text(
                password, auto_id="txtPassword", sensitive=True,
            )
            self.driver.click_button(auto_id="btnLogin")
            logger.info(f"Custodian '{username}' logged in for export")
        return self

    def read_export_values(self, is_last=False, step_name=None):
        """Read export values from textboxes (secret, KCV, and optionally key KCV).

        Args:
            is_last: If True, also reads the combined key KCV field.
            step_name: Optional evidence step description.

        Returns:
            dict with keys: 'secret', 'secret_kcv', and optionally 'key_kcv'.
        """
        values = {}
        with self._step(step_name):
            self.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="txtExpSecret",
            )
            values["secret"] = self.driver.get_field_value(auto_id="txtExpSecret")
            values["secret_kcv"] = self.driver.get_field_value(auto_id="txtExpSecretKcv")
            logger.info(
                f"Export values read: secret={values['secret']}, "
                f"secret_kcv={values['secret_kcv']}"
            )

            if is_last:
                values["key_kcv"] = self.driver.get_field_value(auto_id="txtExpKeyKcv")
                logger.info(f"Key KCV: {values['key_kcv']}")

        return values

    def continue_export(self, step_name=None):
        """Click Continue button to proceed after export."""
        with self._step(step_name):
            self.driver.click_button(auto_id="btnContinue")
            logger.info("Export continued")
        return self

    def get_key_summary(self, step_name=None):
        """Read all key summary information from the verification screen.

        Returns:
            dict with key info: key_label, key_algo, key_size, key_usage,
            key_type, cps_key_type, valid_date, key_mac.
        """
        summary = {}
        with self._step(step_name):
            summary["key_label"] = self.driver.get_text(auto_id="lblExpKeyLabel")
            summary["key_algo"] = self.driver.get_text(auto_id="lblExpKeyAlgo")
            summary["key_size"] = self.driver.get_text(auto_id="lblExpSize")
            summary["key_usage"] = self.driver.get_text(auto_id="lblExpKeyUsage")
            summary["key_type"] = self.driver.get_text(auto_id="lblExpKeyType")
            summary["cps_key_type"] = self.driver.get_text(auto_id="lblCpsKeyType")
            summary["valid_date"] = self.driver.get_text(auto_id="lblExpValidDate")
            summary["key_mac"] = self.driver.get_text(auto_id="lblExpKeyMac")
            logger.info(f"Key summary: {summary}")
        return summary

    def finish(self, step_name=None):
        """Click Continue to complete the CKC flow."""
        with self._step(step_name):
            self.driver.click_button(auto_id="btnContinue")
            logger.info("Customer Key Ceremony completed")
        return self

    # ------------------------------------------------------------------
    # Import mode methods
    # ------------------------------------------------------------------

    def dismiss_reuse_kcps(self, step_name=None):
        """Click 'No' to reuse existing Key Custodian Parties.

        When KCPs already exist (from a previous CKC Generate), the app
        asks whether to recreate them. Click No to keep existing ones.
        """
        with self._step(step_name):
            self.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="7", control_type="Button",
            )
            self._snap("reuse_kcps_dialog")
            self.driver.click_button(auto_id="7")
            logger.info("Dismissed reuse KCPs dialog — keeping existing KCPs")
        return self

    def select_import_mode(self, step_name=None):
        """Select IMPORT mode and proceed."""
        with self._step(step_name):
            self.driver.click_radio(auto_id="rbAgree")
            self.driver.click_button(auto_id="btnNext")
            logger.info("IMPORT mode selected")
        return self

    def login_custodian_import(self, username, password, use_combobox=False,
                               step_name=None):
        """Login as Key Custodian Party for import phase.

        Args:
            username: Custodian party username.
            password: Custodian party password.
            use_combobox: If True, select username from combobox (txtUsername).
                If False, type username into text field (1001).
            step_name: Optional evidence step description.
        """
        with self._step(step_name):
            self.driver.click_radio(auto_id="rbPassword")
            if use_combobox:
                self.driver.select_combobox(
                    auto_id="txtUsername", value=username,
                )
            else:
                self.driver.type_text(username, auto_id="1001")
            self.driver.type_text(
                password, auto_id="txtPassword", sensitive=True,
            )
            self.driver.click_button(auto_id="btnLogin")
            logger.info(f"Custodian '{username}' logged in for import")
        return self

    def import_component(self, secret, kcv, step_name=None):
        """Type the secret component and KCV for import.

        Args:
            secret: Secret hex string (e.g. '239DF91F - 49C9A59C - ...').
            kcv: KCV hex string (e.g. '9628716E').
            step_name: Optional evidence step description.
        """
        with self._step(step_name):
            self.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="mtxtSecret",
            )
            self.driver.type_keys_to_field(
                secret, auto_id="mtxtSecret", sensitive=True,
            )
            self.driver.type_text("", auto_id="txtKCV")
            self.driver.type_text(kcv, auto_id="txtKCV")
            logger.info(f"Import component entered: kcv={kcv}")
        return self

    def select_key_attributes(self, attributes, step_name=None):
        """Select key attributes from comboboxes during import.

        Args:
            attributes: dict mapping combobox auto_id to value,
                e.g. {'cbD0': 'Standard_Algorithm', 'cbD1': 'AES'}.
            step_name: Optional evidence step description.
        """
        with self._step(step_name):
            for auto_id, value in attributes.items():
                self.driver.select_combobox(auto_id=auto_id, value=value)
                logger.info(f"Key attribute {auto_id}={value}")
        return self

    def import_final_component(self, secret, kcv, customer_key_kcv,
                               key_label, key_algo, key_length, key_usage,
                               cps_key_type, key_mac, step_name=None):
        """Import the final KCP component with full key configuration.

        Only called for the last KCP. Enters secret, KCV, customer key KCV,
        key config parameters, and key MAC.

        Args:
            secret: Secret hex string.
            kcv: KCV hex string.
            customer_key_kcv: Customer key KCV hex.
            key_label: Key label (e.g. 'CKC_E2E').
            key_algo: Key algorithm (e.g. 'AES').
            key_length: Key length (e.g. '256bits').
            key_usage: Key usage hex (e.g. '3F').
            cps_key_type: CPS key type (e.g. 'ZCMK_EXP').
            key_mac: Key MAC hex (e.g. 'CC6AB78EFB29351D').
            step_name: Optional evidence step description.
        """
        with self._step(step_name):
            self.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="mtxtSecret",
            )
            self.driver.type_keys_to_field(
                secret, auto_id="mtxtSecret", sensitive=True,
            )
            self.driver.type_text(kcv, auto_id="txtKCV")
            self.driver.type_text(customer_key_kcv, auto_id="txtCustKeyKCV")
            self.driver.type_text(key_label, auto_id="txtKeyLabel")
            self.driver.select_combobox(auto_id="cbKeyAlgo", value=key_algo)
            self.driver.select_combobox(auto_id="cbKeyLength", value=key_length)
            self.driver.type_text(key_usage, auto_id="txtKeyUsage")
            self.driver.select_combobox(auto_id="cbCpsKeyType", value=cps_key_type)
            self.driver.type_text(key_mac, auto_id="txtKeyMac")
            logger.info(
                f"Final import component entered: label={key_label}, "
                f"algo={key_algo}, length={key_length}, mac={key_mac}"
            )
        return self

    def process_import(self, step_name=None):
        """Click Continue/Process and dismiss confirmation dialog."""
        with self._step(step_name):
            self.driver.click_button(auto_id="btnProcess")
            self.dismiss_ok()
            logger.info("Import component processed")
        return self

    def finalize_import(self, step_name=None):
        """Process the final import and dismiss both confirmation dialogs."""
        with self._step(step_name):
            self.driver.click_button(auto_id="btnProcess")
            self.dismiss_ok()
            self.dismiss_ok()
            logger.info("CKC Import finalized")
        return self
