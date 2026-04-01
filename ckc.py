# Auto-generated from UI Recorder
# App:  | Date: 2026-04-01 14:22:51
# Flow: ckc.yaml

from sphere_e2e_test_framework import tracked_step


def test_recorded_flow(self):
    driver = self.driver
    evidence = self.evidence

    with tracked_step(evidence, driver, "Step 1: Click 'Connect' button"):
        driver.click_button(auto_id="btnUpdate")

    with tracked_step(evidence, driver, "Step 2: Click 'OK' button"):
        driver.click_button(auto_id="btnOKE")

    with tracked_step(evidence, driver, "Step 3: Click 'CKC' button"):
        driver.click_button(auto_id="btnCustomerKeyCeremony")

    with tracked_step(evidence, driver, "Step 4: Click 'Agree' radiobutton"):
        driver.click_button(auto_id="rbAgree")

    with tracked_step(evidence, driver, "Step 5: Click '   Next  >>>' button"):
        driver.click_button(auto_id="btnNext")

    with tracked_step(evidence, driver, "Step 6: Click 'Password' radiobutton"):
        driver.click_button(auto_id="rbPassword")

    with tracked_step(evidence, driver, "Step 7: Type into 'Password:'"):
        driver.type_text("admin", auto_id="1001")

    with tracked_step(evidence, driver, "Step 8: Type into 'Edit'"):
        driver.type_text("	11111111", auto_id="txtPassword")

    with tracked_step(evidence, driver, "Step 9: Click 'Button' button"):
        driver.click_button(auto_id="btnLogin")

    with tracked_step(evidence, driver, "Step 10: Click 'Step 1.0 - Customer Key Ceremony - Create Key Custodians' button"):
        driver.click_button(auto_id="btnAdd1")

    with tracked_step(evidence, driver, "Step 11: Type into 'Edit'"):
        driver.type_text("kcp1", auto_id="txtUsername")

    with tracked_step(evidence, driver, "Step 12: Click 'Password' radiobutton"):
        driver.click_button(auto_id="rbPass")

    with tracked_step(evidence, driver, "Step 13: Type into 'Password:'"):
        driver.type_text("11111111", auto_id="txtPass")

    with tracked_step(evidence, driver, "Step 14: Type into 'Edit'"):
        driver.type_text("11111111", auto_id="txtPassRepeat")

    with tracked_step(evidence, driver, "Step 15: Click 'Create' button"):
        driver.click_button(auto_id="btnCreate")

    with tracked_step(evidence, driver, "Step 16: Click 'OK' button"):
        driver.click_button(auto_id="2")

    with tracked_step(evidence, driver, "Step 17: Click 'Button' button"):
        driver.click_button(auto_id="btnAdd2")

    with tracked_step(evidence, driver, "Step 18: Type into 'Edit'"):
        driver.type_text("kcp2", auto_id="txtUsername")

    with tracked_step(evidence, driver, "Step 19: Click 'Password' radiobutton"):
        driver.click_button(auto_id="rbPass")

    with tracked_step(evidence, driver, "Step 20: Type into 'Password:'"):
        driver.type_text("11111111", auto_id="txtPass")

    with tracked_step(evidence, driver, "Step 21: Type into 'Edit'"):
        driver.type_text("11111111", auto_id="txtPassRepeat")

    with tracked_step(evidence, driver, "Step 22: Click 'Create' button"):
        driver.click_button(auto_id="btnCreate")

    with tracked_step(evidence, driver, "Step 23: Click 'OK' button"):
        driver.click_button(auto_id="2")

    with tracked_step(evidence, driver, "Step 24: Click 'Button' button"):
        driver.click_button(auto_id="btnAdd3")

    with tracked_step(evidence, driver, "Step 25: Type into 'Edit'"):
        driver.type_text("kcp3", auto_id="txtUsername")

    with tracked_step(evidence, driver, "Step 26: Click 'Password' radiobutton"):
        driver.click_button(auto_id="rbPass")

    with tracked_step(evidence, driver, "Step 27: Type into 'Password:'"):
        driver.type_text("11111111", auto_id="txtPass")

    with tracked_step(evidence, driver, "Step 28: Type into 'Edit'"):
        driver.type_text("11111111", auto_id="txtPassRepeat")

    with tracked_step(evidence, driver, "Step 29: Click 'Create' button"):
        driver.click_button(auto_id="btnCreate")

    with tracked_step(evidence, driver, "Step 30: Click 'OK' button"):
        driver.click_button(auto_id="2")

    with tracked_step(evidence, driver, "Step 31: Click '   Next  >>>' button"):
        driver.click_button(auto_id="btnNext")

    with tracked_step(evidence, driver, "Step 32: Click 'GENERATE_AND_EXPORT' radiobutton"):
        driver.click_button(auto_id="rbDisagree")

    with tracked_step(evidence, driver, "Step 33: Click '   Next  >>>' button"):
        driver.click_button(auto_id="btnNext")

    with tracked_step(evidence, driver, "Step 34: Type into 'Edit'"):
        driver.type_text("CKC_E2E_1", auto_id="txtKeyLabel")

    with tracked_step(evidence, driver, "Step 35: Select from 'TDES'"):
        driver.select_combobox(auto_id="cbKeyAlgo", value="AES")

    with tracked_step(evidence, driver, "Step 36: Select from '128 bits'"):
        driver.select_combobox(auto_id="cbKeyLength", value="256 bits")

    with tracked_step(evidence, driver, "Step 37: Type into 'Key Label:'"):
        driver.type_text("3F", auto_id="txtKeyUsage")

    with tracked_step(evidence, driver, "Step 38: Select from 'KCV Method:'"):
        driver.select_combobox(auto_id="cbCpsKeyType", value="ZCMK_EXP")

    with tracked_step(evidence, driver, "Step 39: Click 'Generate' button"):
        driver.click_button(auto_id="btnCreate")

    with tracked_step(evidence, driver, "Step 40: Click 'OK' button"):
        driver.click_button(auto_id="2")

    with tracked_step(evidence, driver, "Step 41: Click 'Understand' radiobutton"):
        driver.click_button(auto_id="rbAgree")

    with tracked_step(evidence, driver, "Step 42: Click '   Next  >>>' button"):
        driver.click_button(auto_id="btnNext")

    with tracked_step(evidence, driver, "Step 43: Click 'Password' radiobutton"):
        driver.click_button(auto_id="rbPassword")

    with tracked_step(evidence, driver, "Step 44: Type into 'Password:'"):
        driver.type_text("kcp1", auto_id="1001")

    with tracked_step(evidence, driver, "Step 45: Type into 'Edit'"):
        driver.type_text("11111111", auto_id="txtPassword")

    with tracked_step(evidence, driver, "Step 46: Click 'Button' button"):
        driver.click_button(auto_id="btnLogin")

    with tracked_step(evidence, driver, "Step 47: Type into 'KCV of KEY :'"):
        driver.type_text("copy text", auto_id="txtExpSecret")

    with tracked_step(evidence, driver, "Step 48: Type into 'Edit'"):
        driver.type_text("copy text", auto_id="txtExpSecretKcv")

    with tracked_step(evidence, driver, "Step 49: Click 'Continue' button"):
        driver.click_button(auto_id="btnContinue")

    with tracked_step(evidence, driver, "Step 50: Click 'Understand' radiobutton"):
        driver.click_button(auto_id="rbAgree")

    with tracked_step(evidence, driver, "Step 51: Click '   Next  >>>' button"):
        driver.click_button(auto_id="btnNext")

    with tracked_step(evidence, driver, "Step 52: Click 'Password' radiobutton"):
        driver.click_button(auto_id="rbPassword")

    with tracked_step(evidence, driver, "Step 53: Type into 'Password:'"):
        driver.type_text("kcp2", auto_id="1001")

    with tracked_step(evidence, driver, "Step 54: Type into 'Edit'"):
        driver.type_text("11111111", auto_id="txtPassword")

    with tracked_step(evidence, driver, "Step 55: Click 'Button' button"):
        driver.click_button(auto_id="btnLogin")

    with tracked_step(evidence, driver, "Step 56: Type into 'KCV of KEY :'"):
        driver.type_text("copy text", auto_id="txtExpSecret")

    with tracked_step(evidence, driver, "Step 57: Type into 'Edit'"):
        driver.type_text("copy text", auto_id="txtExpSecretKcv")

    with tracked_step(evidence, driver, "Step 58: Click 'Continue' button"):
        driver.click_button(auto_id="btnContinue")

    with tracked_step(evidence, driver, "Step 59: Click 'Understand' radiobutton"):
        driver.click_button(auto_id="rbAgree")

    with tracked_step(evidence, driver, "Step 60: Click 'Finalize' button"):
        driver.click_button(auto_id="btnNext")

    with tracked_step(evidence, driver, "Step 61: Click 'Password' radiobutton"):
        driver.click_button(auto_id="rbPassword")

    with tracked_step(evidence, driver, "Step 62: Type into 'Password:'"):
        driver.type_text("kcp3", auto_id="1001")

    with tracked_step(evidence, driver, "Step 63: Type into 'Edit'"):
        driver.type_text("11111111", auto_id="txtPassword")

    with tracked_step(evidence, driver, "Step 64: Click 'Button' button"):
        driver.click_button(auto_id="btnLogin")

    with tracked_step(evidence, driver, "Step 65: Type into 'KCV of KEY :'"):
        driver.type_text("copy", auto_id="txtExpSecret")

    with tracked_step(evidence, driver, "Step 66: Type into 'Edit'"):
        driver.type_text("copy", auto_id="txtExpSecretKcv")

    with tracked_step(evidence, driver, "Step 67: Type into 'Edit'"):
        driver.type_text("copy", auto_id="txtExpKeyKcv")

    with tracked_step(evidence, driver, "Step 68: Click 'Customer Key Info' group"):
        driver.click_element(auto_id="groupInfoExport", control_type="Group")

    with tracked_step(evidence, driver, "Step 69: Click 'CKC_E2E_1' text"):
        driver.click_element(auto_id="lblExpKeyLabel", control_type="Text")

    with tracked_step(evidence, driver, "Step 70: Click 'AES' text"):
        driver.click_element(auto_id="lblExpKeyAlgo", control_type="Text")

    with tracked_step(evidence, driver, "Step 71: Click 'AES_256b' text"):
        driver.click_element(auto_id="lblExpSize", control_type="Text")

    with tracked_step(evidence, driver, "Step 72: Click '003F' text"):
        driver.click_element(auto_id="lblExpKeyUsage", control_type="Text")

    with tracked_step(evidence, driver, "Step 73: Click 'Permanent (stored in LKD)' text"):
        driver.click_element(auto_id="lblExpKeyType", control_type="Text")

    with tracked_step(evidence, driver, "Step 74: Click 'ZCMK_EXP' text"):
        driver.click_element(auto_id="lblCpsKeyType", control_type="Text")

    with tracked_step(evidence, driver, "Step 75: Click '2027 - 4 - 1 ' text"):
        driver.click_element(auto_id="lblExpValidDate", control_type="Text")

    with tracked_step(evidence, driver, "Step 76: Click 'CC 6A B7 8E FB 29 35 1D' text"):
        driver.click_element(auto_id="lblExpKeyMac", control_type="Text")

    with tracked_step(evidence, driver, "Step 77: Click 'Continue' button"):
        driver.click_button(auto_id="btnContinue")
