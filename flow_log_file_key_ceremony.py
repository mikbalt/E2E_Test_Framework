# Auto-generated from UI Recorder
# App: Log File Signature Verification | Date: 2026-03-03 16:26:30
# Flow: flow_log_file_signature_verification_20260303_162630.yaml

from hsm_test_framework import tracked_step


def test_recorded_flow(self):
    driver = self.driver
    evidence = self.evidence

    with tracked_step(evidence, driver, "Step 1: Click 'OK' button"):
        driver.click_button(auto_id="2")

    with tracked_step(evidence, driver, "Step 2: Click 'Connect' button"):
        driver.click_button(auto_id="btnUpdate")

    with tracked_step(evidence, driver, "Step 3: Click 'OK' button"):
        driver.click_button(auto_id="btnOKE")

    with tracked_step(evidence, driver, "Step 4: Click 'Start HSM Initialization' button"):
        driver.click_button(auto_id="btnHSMInit")

    with tracked_step(evidence, driver, "Step 5: Click 'Agree' radiobutton"):
        driver.click_button(auto_id="rbAgree")

    with tracked_step(evidence, driver, "Step 6: Click '   Next  >>>' button"):
        driver.click_button(auto_id="btnNext")

    with tracked_step(evidence, driver, "Step 7: Click 'Agree' radiobutton"):
        driver.click_button(auto_id="rbAgree")

    with tracked_step(evidence, driver, "Step 8: Click '   Next  >>>' button"):
        driver.click_button(auto_id="btnNext")

    with tracked_step(evidence, driver, "Step 9: Type into 'Edit'"):
        driver.type_text("p@ssw0rd", auto_id="txtOldPass")

    with tracked_step(evidence, driver, "Step 10: Type into 'Edit'"):
        driver.type_text("p@ssw0rd", auto_id="txtOldPass")

    with tracked_step(evidence, driver, "Step 11: Type into 'Edit'"):
        driver.type_text("11111111", auto_id="txtNewPass")

    with tracked_step(evidence, driver, "Step 12: Type into 'Edit'"):
        driver.type_text("11111111", auto_id="txtRepeatNewPass")

    with tracked_step(evidence, driver, "Step 13: Click 'Confirm' button"):
        driver.click_button(auto_id="btnChangePass")

    with tracked_step(evidence, driver, "Step 14: Click 'OK' button"):
        driver.click_button(auto_id="2")

    with tracked_step(evidence, driver, "Step 15: Click 'Agree' radiobutton"):
        driver.click_button(auto_id="rbAgree")

    with tracked_step(evidence, driver, "Step 16: Click '   Next  >>>' button"):
        driver.click_button(auto_id="btnNext")

    with tracked_step(evidence, driver, "Step 17: Click 'OK' button"):
        driver.click_button(auto_id="2")

    with tracked_step(evidence, driver, "Step 18: Type into 'Edit'"):
        driver.type_text("11111111", auto_id="txtPassword")

    with tracked_step(evidence, driver, "Step 19: Click 'Confirm' button"):
        driver.click_button(auto_id="btnAuth")

    with tracked_step(evidence, driver, "Step 20: Type into 'Edit'"):
        driver.type_text("admin", auto_id="txtUsername")

    with tracked_step(evidence, driver, "Step 21: Click 'Password' radiobutton"):
        driver.click_button(auto_id="rbPass")

    with tracked_step(evidence, driver, "Step 22: Type into 'Password:'"):
        driver.type_text("11111111", auto_id="txtPass")

    with tracked_step(evidence, driver, "Step 23: Type into 'Edit'"):
        driver.type_text("11111111", auto_id="txtPassRepeat")

    with tracked_step(evidence, driver, "Step 24: Click 'Create' button"):
        driver.click_button(auto_id="btnCreate")

    with tracked_step(evidence, driver, "Step 25: Click 'OK' button"):
        driver.click_button(auto_id="2")

    with tracked_step(evidence, driver, "Step 26: Click 'OK' button"):
        driver.click_button(auto_id="2")

    with tracked_step(evidence, driver, "Step 27: Click 'Agree' radiobutton"):
        driver.click_button(auto_id="rbAgree")

    with tracked_step(evidence, driver, "Step 28: Click '   Next  >>>' button"):
        driver.click_button(auto_id="btnNext")

    with tracked_step(evidence, driver, "Step 29: Click 'Password' radiobutton"):
        driver.click_button(auto_id="rbPassword")

    with tracked_step(evidence, driver, "Step 30: Type into 'Password:'"):
        driver.type_text("admin", auto_id="1001")

    with tracked_step(evidence, driver, "Step 31: Type into 'Edit'"):
        driver.type_text("11111111", auto_id="txtPassword")

    with tracked_step(evidence, driver, "Step 32: Click 'Button' button"):
        driver.click_button(auto_id="btnLogin")

    with tracked_step(evidence, driver, "Step 33: Click 'Understand' radiobutton"):
        driver.click_button(auto_id="rbAgree")

    with tracked_step(evidence, driver, "Step 34: Click 'OK' button"):
        driver.click_button(auto_id="2")

    with tracked_step(evidence, driver, "Step 35: Click 'Step 3.0 - Key Ceremony - Create Key Custodians' button"):
        driver.click_button(auto_id="btnAdd1")

    with tracked_step(evidence, driver, "Step 36: Type into 'Edit'"):
        driver.type_text("kc1", auto_id="txtUsername")

    with tracked_step(evidence, driver, "Step 37: Click 'Password' radiobutton"):
        driver.click_button(auto_id="rbPass")

    with tracked_step(evidence, driver, "Step 38: Type into 'Password:'"):
        driver.type_text("11111111", auto_id="txtPass")

    with tracked_step(evidence, driver, "Step 39: Type into 'Edit'"):
        driver.type_text("11111111", auto_id="txtPassRepeat")

    with tracked_step(evidence, driver, "Step 40: Click 'Create' button"):
        driver.click_button(auto_id="btnCreate")

    with tracked_step(evidence, driver, "Step 41: Click 'OK' button"):
        driver.click_button(auto_id="2")

    with tracked_step(evidence, driver, "Step 42: Click 'Button' button"):
        driver.click_button(auto_id="btnAdd2")

    with tracked_step(evidence, driver, "Step 43: Type into 'Edit'"):
        driver.type_text("kc2", auto_id="txtUsername")

    with tracked_step(evidence, driver, "Step 44: Click 'Password' radiobutton"):
        driver.click_button(auto_id="rbPass")

    with tracked_step(evidence, driver, "Step 45: Type into 'Password:'"):
        driver.type_text("11111111", auto_id="txtPass")

    with tracked_step(evidence, driver, "Step 46: Type into 'Edit'"):
        driver.type_text("11111111", auto_id="txtPassRepeat")

    with tracked_step(evidence, driver, "Step 47: Click 'Create' button"):
        driver.click_button(auto_id="btnCreate")

    with tracked_step(evidence, driver, "Step 48: Click 'OK' button"):
        driver.click_button(auto_id="2")

    with tracked_step(evidence, driver, "Step 49: Click 'Button' button"):
        driver.click_button(auto_id="btnAdd3")

    with tracked_step(evidence, driver, "Step 50: Type into 'Edit'"):
        driver.type_text("kc3", auto_id="txtUsername")

    with tracked_step(evidence, driver, "Step 51: Click 'Password' radiobutton"):
        driver.click_button(auto_id="rbPass")

    with tracked_step(evidence, driver, "Step 52: Type into 'Password:'"):
        driver.type_text("11111111", auto_id="txtPass")

    with tracked_step(evidence, driver, "Step 53: Type into 'Edit'"):
        driver.type_text("11111111", auto_id="txtPassRepeat")

    with tracked_step(evidence, driver, "Step 54: Click 'Create' button"):
        driver.click_button(auto_id="btnCreate")

    with tracked_step(evidence, driver, "Step 55: Click 'OK' button"):
        driver.click_button(auto_id="2")

    with tracked_step(evidence, driver, "Step 56: Click 'Button' button"):
        driver.click_button(auto_id="btnAuditorCreate")

    with tracked_step(evidence, driver, "Step 57: Type into 'Edit'"):
        driver.type_text("auditor", auto_id="txtUsername")

    with tracked_step(evidence, driver, "Step 58: Click 'Password' radiobutton"):
        driver.click_button(auto_id="rbPass")

    with tracked_step(evidence, driver, "Step 59: Type into 'Password:'"):
        driver.type_text("11111111", auto_id="txtPass")

    with tracked_step(evidence, driver, "Step 60: Type into 'Edit'"):
        driver.type_text("11111111", auto_id="txtPassRepeat")

    with tracked_step(evidence, driver, "Step 61: Click 'Create' button"):
        driver.click_button(auto_id="btnCreate")

    with tracked_step(evidence, driver, "Step 62: Click 'OK' button"):
        driver.click_button(auto_id="2")

    with tracked_step(evidence, driver, "Step 63: Click 'Understand' radiobutton"):
        driver.click_button(auto_id="rbAgree")

    with tracked_step(evidence, driver, "Step 64: Click '   Next  >>>' button"):
        driver.click_button(auto_id="btnNext")

    with tracked_step(evidence, driver, "Step 65: Click 'Import CCMK' radiobutton"):
        driver.click_button(auto_id="rbAgree")

    with tracked_step(evidence, driver, "Step 66: Click '   Next  >>>' button"):
        driver.click_button(auto_id="btnNext")

    with tracked_step(evidence, driver, "Step 67: Click 'Understand' radiobutton"):
        driver.click_button(auto_id="rbAgree")

    with tracked_step(evidence, driver, "Step 68: Click '   Next  >>>' button"):
        driver.click_button(auto_id="btnNext")

    with tracked_step(evidence, driver, "Step 69: Click 'Password' radiobutton"):
        driver.click_button(auto_id="rbPassword")

    with tracked_step(evidence, driver, "Step 70: Type into 'Password:'"):
        driver.type_text("kc1", auto_id="1001")

    with tracked_step(evidence, driver, "Step 71: Type into 'Edit'"):
        driver.type_text("11111111", auto_id="txtPassword")

    with tracked_step(evidence, driver, "Step 72: Type into 'Edit'"):
        driver.type_text("447722550033DDAADDAA221122550033FEEFBAABDCCDFEEFBAABDCCDFEEFBAAB", auto_id="mtxtSecret")

    with tracked_step(evidence, driver, "Step 73: Type into 'Edit'"):
        driver.type_text("1C19A21F", auto_id="txtKCV")

    with tracked_step(evidence, driver, "Step 74: Click 'Continue' button"):
        driver.click_button(auto_id="btnProcess")

    with tracked_step(evidence, driver, "Step 75: Click 'OK' button"):
        driver.click_button(auto_id="2")

    with tracked_step(evidence, driver, "Step 76: Click '   Next  >>>' button"):
        driver.click_button(auto_id="btnNext")

    with tracked_step(evidence, driver, "Step 77: Click 'Password' radiobutton"):
        driver.click_button(auto_id="rbPassword")

    with tracked_step(evidence, driver, "Step 78: Type into 'Password:'"):
        driver.type_text("kc2", auto_id="1001")

    with tracked_step(evidence, driver, "Step 79: Type into 'Edit'"):
        driver.type_text("11111111", auto_id="txtPassword")

    with tracked_step(evidence, driver, "Step 80: Click 'Button' button"):
        driver.click_button(auto_id="btnLogin")

    with tracked_step(evidence, driver, "Step 81: Type into 'Edit'"):
        driver.type_text("FFEEDDBBEE99009988003366443322669E8FDACBBCAD9E8FDACBBCAD9E8FDACB", auto_id="mtxtSecret")

    with tracked_step(evidence, driver, "Step 82: Type into 'Edit'"):
        driver.type_text("0FBA39B4", auto_id="txtKCV")

    with tracked_step(evidence, driver, "Step 83: Click 'Continue' button"):
        driver.click_button(auto_id="btnProcess")

    with tracked_step(evidence, driver, "Step 84: Click 'OK' button"):
        driver.click_button(auto_id="2")

    with tracked_step(evidence, driver, "Step 85: Click '   Next  >>>' button"):
        driver.click_button(auto_id="btnNext")

    with tracked_step(evidence, driver, "Step 86: Click 'Password' radiobutton"):
        driver.click_button(auto_id="rbPassword")

    with tracked_step(evidence, driver, "Step 87: Type into 'Password:'"):
        driver.type_text("kc3", auto_id="1001")

    with tracked_step(evidence, driver, "Step 88: Type into 'Edit'"):
        driver.type_text("11111111", auto_id="txtPassword")

    with tracked_step(evidence, driver, "Step 89: Click 'Button' button"):
        driver.click_button(auto_id="btnLogin")

    with tracked_step(evidence, driver, "Step 90: Type into 'Edit'"):
        driver.type_text("11223333005577889977FF88CCDDEE888E9FCADBACBD8E9FCADBACBD8E9FCADB", auto_id="mtxtSecret")

    with tracked_step(evidence, driver, "Step 91: Type into 'Edit'"):
        driver.type_text("D7F62A5A", auto_id="txtKCV")

    with tracked_step(evidence, driver, "Step 92: Type into 'Edit'"):
        driver.type_text("EF0ABCDE", auto_id="txtCCMKKCV")

    with tracked_step(evidence, driver, "Step 93: Click 'Continue' button"):
        driver.click_button(auto_id="btnProcess")

    with tracked_step(evidence, driver, "Step 94: Click 'OK' button"):
        driver.click_button(auto_id="2")

    with tracked_step(evidence, driver, "Step 95: Click 'FIPS' radiobutton"):
        driver.click_button(auto_id="rbDisagree")

    with tracked_step(evidence, driver, "Step 96: Click 'Finalize' button"):
        driver.click_button(auto_id="btnNext")

    with tracked_step(evidence, driver, "Step 97: Click 'OK' button"):
        driver.click_button(auto_id="2")

    with tracked_step(evidence, driver, "Step 98: Click 'OK' button"):
        driver.click_button(auto_id="2")
