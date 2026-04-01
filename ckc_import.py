# Auto-generated from UI Recorder
# App:  | Date: 2026-04-01 15:01:21
# Flow: ckc_import.yaml

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
        driver.type_text("11111111", auto_id="txtPassword")

    with tracked_step(evidence, driver, "Step 9: Click 'Button' button"):
        driver.click_button(auto_id="btnLogin")

    with tracked_step(evidence, driver, "Step 10: Click 'No' button"):
        driver.click_button(auto_id="7")

    with tracked_step(evidence, driver, "Step 11: Click 'IMPORT' radiobutton"):
        driver.click_button(auto_id="rbAgree")

    with tracked_step(evidence, driver, "Step 12: Click '   Next  >>>' button"):
        driver.click_button(auto_id="btnNext")

    with tracked_step(evidence, driver, "Step 13: Click 'Understand' radiobutton"):
        driver.click_button(auto_id="rbAgree")

    with tracked_step(evidence, driver, "Step 14: Click '   Next  >>>' button"):
        driver.click_button(auto_id="btnNext")

    with tracked_step(evidence, driver, "Step 15: Click 'Password' radiobutton"):
        driver.click_button(auto_id="rbPassword")

    with tracked_step(evidence, driver, "Step 16: Select from 'Password:'"):
        driver.select_combobox(auto_id="txtUsername", value="kcp1")

    with tracked_step(evidence, driver, "Step 17: Type into 'Edit'"):
        driver.type_text("11111111", auto_id="txtPassword")

    with tracked_step(evidence, driver, "Step 18: Click 'Button' button"):
        driver.click_button(auto_id="btnLogin")

    with tracked_step(evidence, driver, "Step 19: Type into 'Edit'"):
        driver.type_text("239DF91F - 49C9A59C - 4E5A32B8 - 1FFA0A7D - 8681B634 - 6B9C5774 - DBD7D9A6 - 78935EF8", auto_id="mtxtSecret")

    with tracked_step(evidence, driver, "Step 20: Type into 'Edit'"):
        driver.type_text("", auto_id="txtKCV")

    with tracked_step(evidence, driver, "Step 21: Type into 'Edit'"):
        driver.type_text("9628716E", auto_id="txtKCV")

    with tracked_step(evidence, driver, "Step 22: Select from 'Choose..'"):
        driver.select_combobox(auto_id="cbD0", value="Standard_Algorithm")

    with tracked_step(evidence, driver, "Step 23: Select from 'Choose..'"):
        driver.select_combobox(auto_id="cbD1", value="AES")

    with tracked_step(evidence, driver, "Step 24: Click 'Continue' button"):
        driver.click_button(auto_id="btnProcess")

    with tracked_step(evidence, driver, "Step 25: Click 'OK' button"):
        driver.click_button(auto_id="2")

    with tracked_step(evidence, driver, "Step 26: Click 'Understand' radiobutton"):
        driver.click_button(auto_id="rbAgree")

    with tracked_step(evidence, driver, "Step 27: Click '   Next  >>>' button"):
        driver.click_button(auto_id="btnNext")

    with tracked_step(evidence, driver, "Step 28: Click 'Password' radiobutton"):
        driver.click_button(auto_id="rbPassword")

    with tracked_step(evidence, driver, "Step 29: Type into 'Password:'"):
        driver.type_text("kcp2", auto_id="1001")

    with tracked_step(evidence, driver, "Step 30: Type into 'Edit'"):
        driver.type_text("11111111", auto_id="txtPassword")

    with tracked_step(evidence, driver, "Step 31: Click 'Button' button"):
        driver.click_button(auto_id="btnLogin")

    with tracked_step(evidence, driver, "Step 32: Type into 'Edit'"):
        driver.type_text("D038EE3F - 9BE0B95A - C144B02B - D9775DA0 - EA09E094 - 80EE8BAA - 83185E1C - 69985F60", auto_id="mtxtSecret")

    with tracked_step(evidence, driver, "Step 33: Type into 'Edit'"):
        driver.type_text("", auto_id="txtKCV")

    with tracked_step(evidence, driver, "Step 34: Type into 'Edit'"):
        driver.type_text("D968CE34", auto_id="txtKCV")

    with tracked_step(evidence, driver, "Step 35: Click 'Continue' button"):
        driver.click_button(auto_id="btnProcess")

    with tracked_step(evidence, driver, "Step 36: Click 'OK' button"):
        driver.click_button(auto_id="2")

    with tracked_step(evidence, driver, "Step 37: Click 'Understand' radiobutton"):
        driver.click_button(auto_id="rbAgree")

    with tracked_step(evidence, driver, "Step 38: Click 'Finalize' button"):
        driver.click_button(auto_id="btnNext")

    with tracked_step(evidence, driver, "Step 39: Click 'Password' radiobutton"):
        driver.click_button(auto_id="rbPassword")

    with tracked_step(evidence, driver, "Step 40: Type into 'Password:'"):
        driver.type_text("kcp3", auto_id="1001")

    with tracked_step(evidence, driver, "Step 41: Type into 'Password:'"):
        driver.type_text("kcp3", auto_id="1001")

    with tracked_step(evidence, driver, "Step 42: Type into 'Edit'"):
        driver.type_text("11111111", auto_id="txtPassword")

    with tracked_step(evidence, driver, "Step 43: Click 'Button' button"):
        driver.click_button(auto_id="btnLogin")

    with tracked_step(evidence, driver, "Step 44: Type into 'Edit'"):
        driver.type_text("A833F6AE - 47A22917 - 3BE2C64D - 02DB00D2 - 73D61D74 - 3AFE73F5 - F76993D0 - 232D37A2", auto_id="mtxtSecret")

    with tracked_step(evidence, driver, "Step 45: Type into 'Edit'"):
        driver.type_text("D8D146F6", auto_id="txtKCV")

    with tracked_step(evidence, driver, "Step 46: Type into 'Edit'"):
        driver.type_text("CEE42294", auto_id="txtCustKeyKCV")

    with tracked_step(evidence, driver, "Step 47: Type into 'KCV of Cust Key:'"):
        driver.type_text("CKC_E2E", auto_id="txtKeyLabel")

    with tracked_step(evidence, driver, "Step 48: Select from 'TDES'"):
        driver.select_combobox(auto_id="cbKeyAlgo", value="AES")

    with tracked_step(evidence, driver, "Step 49: Select from '128 bits'"):
        driver.select_combobox(auto_id="cbKeyLength", value="256bits")

    with tracked_step(evidence, driver, "Step 50: Type into 'Edit'"):
        driver.type_text("3F", auto_id="txtKeyUsage")

    with tracked_step(evidence, driver, "Step 51: Select from '0'"):
        driver.select_combobox(auto_id="cbCpsKeyType", value="ZCMK_EXP")

    with tracked_step(evidence, driver, "Step 52: Type into 'Edit'"):
        driver.type_text("CC6AB78EFB29351D", auto_id="txtKeyMac")

    with tracked_step(evidence, driver, "Step 53: Click 'Continue' button"):
        driver.click_button(auto_id="btnProcess")

    with tracked_step(evidence, driver, "Step 54: Click 'OK' button"):
        driver.click_button(auto_id="2")

    with tracked_step(evidence, driver, "Step 55: Click 'OK' button"):
        driver.click_button(auto_id="2")
