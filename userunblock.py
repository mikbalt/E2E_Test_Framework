# Auto-generated from UI Recorder
# App:  | Date: 2026-03-31 15:55:59
# Flow: userunblock.yaml

from sphere_e2e_test_framework import tracked_step


def test_recorded_flow(self):
    driver = self.driver
    evidence = self.evidence

    with tracked_step(evidence, driver, "Step 1: Click 'Connect' button"):
        driver.click_button(auto_id="btnUpdate")

    with tracked_step(evidence, driver, "Step 2: Click 'OK' button"):
        driver.click_button(auto_id="btnOKE")

    with tracked_step(evidence, driver, "Step 3: Click 'Click to login!' text"):
        driver.click_element(auto_id="lbl_clickLogin", control_type="Text")

    with tracked_step(evidence, driver, "Step 4: Click 'Password' radiobutton"):
        driver.click_button(auto_id="rbPassword")

    with tracked_step(evidence, driver, "Step 5: Type into 'Password:'"):
        driver.type_text("admin", auto_id="1001")

    with tracked_step(evidence, driver, "Step 6: Type into 'Edit'"):
        driver.type_text("11111111", auto_id="txtPassword")

    with tracked_step(evidence, driver, "Step 7: Click 'Button' button"):
        driver.click_button(auto_id="btnLogin")

    with tracked_step(evidence, driver, "Step 8: Click 'User' button"):
        driver.click_button(auto_id="btnUser")

    with tracked_step(evidence, driver, "Step 9: Type into 'Username Row 6, Not sorted.'"):
        driver.type_text("user_op_block", auto_id="4252060794")

    with tracked_step(evidence, driver, "Step 10: Click 'Button' button"):
        driver.click_button(auto_id="btnUnblock")

    with tracked_step(evidence, driver, "Step 11: Click 'Yes' button"):
        driver.click_button(auto_id="6")

    with tracked_step(evidence, driver, "Step 12: Click 'OK' button"):
        driver.click_button(auto_id="2")

    with tracked_step(evidence, driver, "Step 13: Click 'Button' button"):
        driver.click_button(auto_id="btnLogOut")

    with tracked_step(evidence, driver, "Step 14: Click 'OK' button"):
        driver.click_button(auto_id="2")

    with tracked_step(evidence, driver, "Step 15: Click 'Click to login!' text"):
        driver.click_element(auto_id="lbl_clickLogin", control_type="Text")

    with tracked_step(evidence, driver, "Step 16: Select from 'User Login'"):
        driver.select_combobox(auto_id="cbSession", value="User_session")

    with tracked_step(evidence, driver, "Step 17: Click 'Password' radiobutton"):
        driver.click_button(auto_id="rbPassword")

    with tracked_step(evidence, driver, "Step 18: Type into 'Password:'"):
        driver.type_text("user_op_block", auto_id="1001")

    with tracked_step(evidence, driver, "Step 19: Type into 'Edit'"):
        driver.type_text("11223344556677", auto_id="txtPassword")

    with tracked_step(evidence, driver, "Step 20: Click 'Button' button"):
        driver.click_button(auto_id="btnLogin")

    with tracked_step(evidence, driver, "Step 21: Click 'OK' button"):
        driver.click_button(auto_id="2")

    with tracked_step(evidence, driver, "Step 22: Click 'user_op_block' text"):
        driver.click_element(auto_id="lbl_clickLogin", control_type="Text")
