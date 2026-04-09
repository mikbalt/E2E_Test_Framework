# Auto-generated from UI Recorder
# App:  | Date: 2026-04-02 10:31:01
# Flow: nonfips.yaml

from sphere_e2e_test_framework import tracked_step


def test_recorded_flow(self):
    driver = self.driver
    evidence = self.evidence

    with tracked_step(evidence, driver, "Step 1: Click 'Connect' button"):
        driver.click_button(auto_id="btnUpdate")

    with tracked_step(evidence, driver, "Step 2: Click 'OK' button"):
        driver.click_button(auto_id="btnOKE")

    with tracked_step(evidence, driver, "Step 3: Click 'Start HSM Initialization' button"):
        driver.click_button(auto_id="btnHSMInit")

    with tracked_step(evidence, driver, "Step 4: Click 'Agree' radiobutton"):
        driver.click_button(auto_id="rbAgree")

    with tracked_step(evidence, driver, "Step 5: Click '   Next  >>>' button"):
        driver.click_button(auto_id="btnNext")

    with tracked_step(evidence, driver, "Step 6: Click 'OK' button"):
        driver.click_button(auto_id="2")

    with tracked_step(evidence, driver, "Step 7: Type into 'Edit'"):
        driver.type_text("11111111", auto_id="txtPassword")

    with tracked_step(evidence, driver, "Step 8: Click 'Confirm' button"):
        driver.click_button(auto_id="btnAuth")

    with tracked_step(evidence, driver, "Step 9: Type into 'Edit'"):
        driver.type_text("admin", auto_id="txtUsername")

    with tracked_step(evidence, driver, "Step 10: Click 'Password' radiobutton"):
        driver.click_button(auto_id="rbPass")

    with tracked_step(evidence, driver, "Step 11: Type into 'Password:'"):
        driver.type_text("11111111", auto_id="txtPass")

    with tracked_step(evidence, driver, "Step 12: Type into 'Edit'"):
        driver.type_text("11111111", auto_id="txtPassRepeat")

    with tracked_step(evidence, driver, "Step 13: Click 'Create' button"):
        driver.click_button(auto_id="btnCreate")

    with tracked_step(evidence, driver, "Step 14: Click 'OK' button"):
        driver.click_button(auto_id="2")

    with tracked_step(evidence, driver, "Step 15: Click 'OK' button"):
        driver.click_button(auto_id="2")

    with tracked_step(evidence, driver, "Step 16: Click 'Agree' radiobutton"):
        driver.click_button(auto_id="rbAgree")

    with tracked_step(evidence, driver, "Step 17: Click '   Next  >>>' button"):
        driver.click_button(auto_id="btnNext")
