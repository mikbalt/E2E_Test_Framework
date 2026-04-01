"""
Shared test data classes for E2E tests.

Provides dataclasses with sensible defaults that can be overridden via:
  1. Subclassing:     class MyData(KeyCeremonyData): admin_password = "custom"
  2. from_env():      data = KeyCeremonyData.from_env()
  3. Fixture override: @pytest.fixture def key_ceremony_data(): return MyData()
  4. Direct init:     data = KeyCeremonyData(admin_password="custom")

Usage in tests:
    from tests.test_data import KeyCeremonyData

    class TestKeyCeremony:
        @pytest.fixture(autouse=True)
        def setup(self):
            self.td = KeyCeremonyData.from_env()

        def test_something(self):
            driver.type_text(self.td.admin_password, ...)
"""

import os
from dataclasses import dataclass, field


@dataclass
class KeyCustodian:
    """A single Key Custodian's credentials and CCMK component."""
    username: str
    password: str
    add_button: str
    ccmk_secret: str
    ccmk_kcv: str
    ccmk_combined_kcv: str = ""


@dataclass
class KeyCeremonyData:
    """Test data for a full key ceremony flow.

    Defaults are safe for a local/staging HSM test environment.
    Override per-environment via from_env() or subclass.
    """
    default_super_user_pass: str = "p@ssw0rd"
    new_super_user_pass: str = "11111111"

    admin_username: str = "admin"
    admin_password: str = "11111111"

    auditor_username: str = "auditor"
    auditor_password: str = "11111111"

    key_custodians: list = field(default_factory=lambda: [
        KeyCustodian(
            username="kc1",
            password="11111111",
            add_button="btnAdd1",
            ccmk_secret="447722550033DDAADDAA221122550033FEEFBAABDCCDFEEFBAABDCCDFEEFBAAB",
            ccmk_kcv="1C19A21F",
        ),
        KeyCustodian(
            username="kc2",
            password="11111111",
            add_button="btnAdd2",
            ccmk_secret="FFEEDDBBEE99009988003366443322669E8FDACBBCAD9E8FDACBBCAD9E8FDACB",
            ccmk_kcv="0FBA39B4",
        ),
        KeyCustodian(
            username="kc3",
            password="11111111",
            add_button="btnAdd3",
            ccmk_secret="11223333005577889977FF88CCDDEE888E9FCADBACBD8E9FCADBACBD8E9FCADB",
            ccmk_kcv="D7F62A5A",
            ccmk_combined_kcv="EF0ABCDE",
        ),
    ])

    @classmethod
    def from_env(cls, **overrides):
        """Create instance with environment variable overrides.

        Env vars (all optional — falls back to class defaults):
            KC_DEFAULT_SUPER_USER_PASS
            KC_NEW_SUPER_USER_PASS
            KC_ADMIN_PASSWORD
            KC_AUDITOR_PASSWORD
            KC_KC1_PASSWORD, KC_CCMK_SECRET_1, KC_CCMK_KCV_1
            KC_KC2_PASSWORD, KC_CCMK_SECRET_2, KC_CCMK_KCV_2
            KC_KC3_PASSWORD, KC_CCMK_SECRET_3, KC_CCMK_KCV_3
            KC_CCMK_COMBINED_KCV
        """
        defaults = cls()

        kwargs = {
            "default_super_user_pass": os.environ.get("KC_DEFAULT_SUPER_USER_PASS", defaults.default_super_user_pass),
            "new_super_user_pass": os.environ.get("KC_NEW_SUPER_USER_PASS", defaults.new_super_user_pass),
            "admin_username": defaults.admin_username,
            "admin_password": os.environ.get("KC_ADMIN_PASSWORD", defaults.admin_password),
            "auditor_username": defaults.auditor_username,
            "auditor_password": os.environ.get("KC_AUDITOR_PASSWORD", defaults.auditor_password),
        }

        # Build key custodians with env overrides
        kc_list = []
        for i, default_kc in enumerate(defaults.key_custodians, start=1):
            kc_list.append(KeyCustodian(
                username=default_kc.username,
                password=os.environ.get(f"KC_KC{i}_PASSWORD", default_kc.password),
                add_button=default_kc.add_button,
                ccmk_secret=os.environ.get(f"KC_CCMK_SECRET_{i}", default_kc.ccmk_secret),
                ccmk_kcv=os.environ.get(f"KC_CCMK_KCV_{i}", default_kc.ccmk_kcv),
                ccmk_combined_kcv=os.environ.get("KC_CCMK_COMBINED_KCV", default_kc.ccmk_combined_kcv),
            ))
        kwargs["key_custodians"] = kc_list

        kwargs.update(overrides)
        return cls(**kwargs)


@dataclass
class AddOperationUserData:
    """Test data for the Add Operation User flow.

    Covers: admin login, profile creation, user creation, user login.
    Override per-environment via from_env() or subclass.

    Env vars (all optional — falls back to class defaults):
        OP_ADMIN_USERNAME, OP_ADMIN_PASSWORD, OP_ADMIN_SESSION
        OP_PROFILE_NAME
        OP_USER_USERNAME, OP_USER_PASSWORD, OP_USER_SESSION
    """
    # Admin credentials
    admin_username: str = "admin"
    admin_password: str = "11111111"
    admin_session: str = "Admin_Session"

    # Profile
    profile_name: str = "PROFILE_USER_OPERATION"
    select_all_acl: bool = True

    # Operation user
    user_username: str = "user_op_1"
    user_password: str = "1122334455667788"
    user_session: str = "User_Session"

    @classmethod
    def from_env(cls, **overrides):
        """Create instance with environment variable overrides."""
        defaults = cls()

        kwargs = {
            "admin_username": os.environ.get("OP_ADMIN_USERNAME", defaults.admin_username),
            "admin_password": os.environ.get("OP_ADMIN_PASSWORD", defaults.admin_password),
            "admin_session": os.environ.get("OP_ADMIN_SESSION", defaults.admin_session),
            "profile_name": os.environ.get("OP_PROFILE_NAME", defaults.profile_name),
            "user_username": os.environ.get("OP_USER_USERNAME", defaults.user_username),
            "user_password": os.environ.get("OP_USER_PASSWORD", defaults.user_password),
            "user_session": os.environ.get("OP_USER_SESSION", defaults.user_session),
        }

        kwargs.update(overrides)
        return cls(**kwargs)


@dataclass
class DeleteOperationUserData:
    """Test data for the Delete Operation User flow.

    Covers: admin login, user creation (prerequisite), user deletion,
    verify deleted user fails to login.
    Override per-environment via from_env() or subclass.

    Env vars (all optional — falls back to class defaults):
        DEL_ADMIN_USERNAME, DEL_ADMIN_PASSWORD, DEL_ADMIN_SESSION
        DEL_PROFILE_NAME
        DEL_USER_USERNAME, DEL_USER_PASSWORD, DEL_USER_SESSION
    """
    # Admin credentials
    admin_username: str = "admin"
    admin_password: str = "11111111"
    admin_session: str = "Admin_Session"

    # Profile
    profile_name: str = "PROFILE_USER_OPERATION"
    select_all_acl: bool = True

    # Operation user to delete
    user_username: str = "user_op_delete"
    user_password: str = "1122334455667788"
    user_session: str = "User_Session"

    @classmethod
    def from_env(cls, **overrides):
        """Create instance with environment variable overrides."""
        defaults = cls()

        kwargs = {
            "admin_username": os.environ.get("DEL_ADMIN_USERNAME", defaults.admin_username),
            "admin_password": os.environ.get("DEL_ADMIN_PASSWORD", defaults.admin_password),
            "admin_session": os.environ.get("DEL_ADMIN_SESSION", defaults.admin_session),
            "profile_name": os.environ.get("DEL_PROFILE_NAME", defaults.profile_name),
            "user_username": os.environ.get("DEL_USER_USERNAME", defaults.user_username),
            "user_password": os.environ.get("DEL_USER_PASSWORD", defaults.user_password),
            "user_session": os.environ.get("DEL_USER_SESSION", defaults.user_session),
        }

        kwargs.update(overrides)
        return cls(**kwargs)


@dataclass
class BlockUserData:
    """Test data for the Block User flow.

    Covers: admin login, ensure user exists (prerequisite), block user,
    verify blocked user fails to login.
    Override per-environment via from_env() or subclass.

    Env vars (all optional — falls back to class defaults):
        BLK_ADMIN_USERNAME, BLK_ADMIN_PASSWORD, BLK_ADMIN_SESSION
        BLK_PROFILE_NAME
        BLK_USER_USERNAME, BLK_USER_PASSWORD, BLK_USER_SESSION
    """
    # Admin credentials
    admin_username: str = "admin"
    admin_password: str = "11111111"
    admin_session: str = "Admin_Session"

    # Profile
    profile_name: str = "PROFILE_USER_OPERATION"
    select_all_acl: bool = True

    # User to block
    user_username: str = "user_op_block"
    user_password: str = "1122334455667788"
    user_session: str = "User_Session"

    # Wrong password for brute-force lock
    wrong_password: str = "WRONGPASSWORD123"
    max_attempts: int = 5

    @classmethod
    def from_env(cls, **overrides):
        """Create instance with environment variable overrides."""
        defaults = cls()

        kwargs = {
            "admin_username": os.environ.get("BLK_ADMIN_USERNAME", defaults.admin_username),
            "admin_password": os.environ.get("BLK_ADMIN_PASSWORD", defaults.admin_password),
            "admin_session": os.environ.get("BLK_ADMIN_SESSION", defaults.admin_session),
            "profile_name": os.environ.get("BLK_PROFILE_NAME", defaults.profile_name),
            "user_username": os.environ.get("BLK_USER_USERNAME", defaults.user_username),
            "user_password": os.environ.get("BLK_USER_PASSWORD", defaults.user_password),
            "user_session": os.environ.get("BLK_USER_SESSION", defaults.user_session),
            "wrong_password": os.environ.get("BLK_WRONG_PASSWORD", defaults.wrong_password),
            "max_attempts": int(os.environ.get("BLK_MAX_ATTEMPTS", defaults.max_attempts)),
        }

        kwargs.update(overrides)
        return cls(**kwargs)


@dataclass
class UnblockUserData:
    """Test data for the Unblock User flow.

    Covers: admin login, ensure user exists (prerequisite), block user
    (prerequisite for standalone), unblock user, verify unblocked user
    can login.
    Override per-environment via from_env() or subclass.

    Env vars (all optional — falls back to class defaults):
        UBLK_ADMIN_USERNAME, UBLK_ADMIN_PASSWORD, UBLK_ADMIN_SESSION
        UBLK_PROFILE_NAME
        UBLK_USER_USERNAME, UBLK_USER_PASSWORD, UBLK_USER_SESSION
    """
    # Admin credentials
    admin_username: str = "admin"
    admin_password: str = "11111111"
    admin_session: str = "Admin_Session"

    # Profile
    profile_name: str = "PROFILE_USER_OPERATION"
    select_all_acl: bool = True

    # User to unblock (same user as block test)
    user_username: str = "user_op_block"
    user_password: str = "1122334455667788"
    user_session: str = "User_Session"

    # Wrong password for brute-force lock (standalone prerequisite)
    wrong_password: str = "WRONGPASSWORD123"
    max_attempts: int = 5

    @classmethod
    def from_env(cls, **overrides):
        """Create instance with environment variable overrides."""
        defaults = cls()

        kwargs = {
            "admin_username": os.environ.get("UBLK_ADMIN_USERNAME", defaults.admin_username),
            "admin_password": os.environ.get("UBLK_ADMIN_PASSWORD", defaults.admin_password),
            "admin_session": os.environ.get("UBLK_ADMIN_SESSION", defaults.admin_session),
            "profile_name": os.environ.get("UBLK_PROFILE_NAME", defaults.profile_name),
            "user_username": os.environ.get("UBLK_USER_USERNAME", defaults.user_username),
            "user_password": os.environ.get("UBLK_USER_PASSWORD", defaults.user_password),
            "user_session": os.environ.get("UBLK_USER_SESSION", defaults.user_session),
            "wrong_password": os.environ.get("UBLK_WRONG_PASSWORD", defaults.wrong_password),
            "max_attempts": int(os.environ.get("UBLK_MAX_ATTEMPTS", defaults.max_attempts)),
        }

        kwargs.update(overrides)
        return cls(**kwargs)


@dataclass
class HSMResetData:
    """Test data for the HSM Reset by Super User flow.

    Covers: SUPER_USER login, export audit log (auditor), initiate reset,
    ADMIN authorization.
    Override per-environment via from_env() or subclass.

    Env vars (all optional — falls back to class defaults):
        RESET_SUPER_USER_USERNAME, RESET_SUPER_USER_PASSWORD, RESET_SUPER_USER_SESSION
        RESET_AUDITOR_USERNAME, RESET_AUDITOR_PASSWORD
        RESET_ADMIN_USERNAME, RESET_ADMIN_PASSWORD
    """
    # Super User credentials
    super_user_username: str = "SUPER_USER"
    super_user_password: str = "11111111"
    super_user_session: str = "Admin_Session"

    # Auditor credentials (for export log authorization)
    auditor_username: str = "auditor"
    auditor_password: str = "11111111"

    # Admin credentials (for reset authorization)
    admin_username: str = "admin"
    admin_password: str = "11111111"

    @classmethod
    def from_env(cls, **overrides):
        """Create instance with environment variable overrides."""
        defaults = cls()

        kwargs = {
            "super_user_username": os.environ.get("RESET_SUPER_USER_USERNAME", defaults.super_user_username),
            "super_user_password": os.environ.get("RESET_SUPER_USER_PASSWORD", defaults.super_user_password),
            "super_user_session": os.environ.get("RESET_SUPER_USER_SESSION", defaults.super_user_session),
            "auditor_username": os.environ.get("RESET_AUDITOR_USERNAME", defaults.auditor_username),
            "auditor_password": os.environ.get("RESET_AUDITOR_PASSWORD", defaults.auditor_password),
            "admin_username": os.environ.get("RESET_ADMIN_USERNAME", defaults.admin_username),
            "admin_password": os.environ.get("RESET_ADMIN_PASSWORD", defaults.admin_password),
        }

        kwargs.update(overrides)
        return cls(**kwargs)


@dataclass
class CKCKeyCustodianParty:
    """A single Key Custodian Party for Customer Key Ceremony."""
    username: str
    password: str
    add_button: str


@dataclass
class CustomerKeyCeremonyData:
    """Test data for the Customer Key Ceremony (CKC) flow.

    Precondition: FIPS Key Ceremony must be completed first.
    Override per-environment via from_env() or subclass.

    Env vars (all optional — falls back to class defaults):
        CKC_ADMIN_USERNAME, CKC_ADMIN_PASSWORD
        CKC_KCP1_USERNAME, CKC_KCP1_PASSWORD
        CKC_KCP2_USERNAME, CKC_KCP2_PASSWORD
        CKC_KCP3_USERNAME, CKC_KCP3_PASSWORD
        CKC_KEY_LABEL, CKC_KEY_ALGO, CKC_KEY_LENGTH
        CKC_KEY_USAGE, CKC_CPS_KEY_TYPE
    """
    # Admin credentials (post-ceremony admin)
    admin_username: str = "admin"
    admin_password: str = "11111111"

    # Key configuration
    key_label: str = "CKC_E2E_1"
    key_algo: str = "AES"
    key_length: str = "256 bits"
    key_usage: str = "3F"
    cps_key_type: str = "ZCMK_EXP"

    # Key Custodian Parties
    custodian_parties: list = field(default_factory=lambda: [
        CKCKeyCustodianParty(
            username="kcp1",
            password="11111111",
            add_button="btnAdd1",
        ),
        CKCKeyCustodianParty(
            username="kcp2",
            password="11111111",
            add_button="btnAdd2",
        ),
        CKCKeyCustodianParty(
            username="kcp3",
            password="11111111",
            add_button="btnAdd3",
        ),
    ])

    @classmethod
    def from_env(cls, **overrides):
        """Create instance with environment variable overrides."""
        defaults = cls()

        kwargs = {
            "admin_username": os.environ.get("CKC_ADMIN_USERNAME", defaults.admin_username),
            "admin_password": os.environ.get("CKC_ADMIN_PASSWORD", defaults.admin_password),
            "key_label": os.environ.get("CKC_KEY_LABEL", defaults.key_label),
            "key_algo": os.environ.get("CKC_KEY_ALGO", defaults.key_algo),
            "key_length": os.environ.get("CKC_KEY_LENGTH", defaults.key_length),
            "key_usage": os.environ.get("CKC_KEY_USAGE", defaults.key_usage),
            "cps_key_type": os.environ.get("CKC_CPS_KEY_TYPE", defaults.cps_key_type),
        }

        # Build custodian parties with env overrides
        kcp_list = []
        for i, default_kcp in enumerate(defaults.custodian_parties, start=1):
            kcp_list.append(CKCKeyCustodianParty(
                username=os.environ.get(f"CKC_KCP{i}_USERNAME", default_kcp.username),
                password=os.environ.get(f"CKC_KCP{i}_PASSWORD", default_kcp.password),
                add_button=default_kcp.add_button,
            ))
        kwargs["custodian_parties"] = kcp_list

        kwargs.update(overrides)
        return cls(**kwargs)


@dataclass
class CKCImportKeyCustodianParty:
    """A single Key Custodian Party's import data for CKC Import."""
    username: str
    password: str
    secret: str
    kcv: str
    key_attributes: dict = field(default_factory=dict)


@dataclass
class CustomerKeyCeremonyImportData:
    """Test data for the Customer Key Ceremony Import flow.

    Precondition: CKC Generate & Export must be completed first.
    The secrets and KCVs come from the export phase.
    Override per-environment via from_env() or subclass.

    Env vars (all optional — falls back to class defaults):
        CKCI_ADMIN_USERNAME, CKCI_ADMIN_PASSWORD
        CKCI_KCP1_SECRET, CKCI_KCP1_KCV
        CKCI_KCP2_SECRET, CKCI_KCP2_KCV
        CKCI_KCP3_SECRET, CKCI_KCP3_KCV
        CKCI_CUSTOMER_KEY_KCV, CKCI_KEY_LABEL, CKCI_KEY_ALGO
        CKCI_KEY_LENGTH, CKCI_KEY_USAGE, CKCI_CPS_KEY_TYPE, CKCI_KEY_MAC
    """
    # Admin credentials
    admin_username: str = "admin"
    admin_password: str = "11111111"

    # Key configuration (entered by last KCP)
    key_label: str = "CKC_E2E"
    key_algo: str = "AES"
    key_length: str = "256bits"
    key_usage: str = "3F"
    cps_key_type: str = "ZCMK_EXP"
    key_mac: str = "CC6AB78EFB29351D"

    # Customer key KCV (entered by last KCP)
    customer_key_kcv: str = "CEE42294"

    # Key Custodian Parties with import data
    custodian_parties: list = field(default_factory=lambda: [
        CKCImportKeyCustodianParty(
            username="kcp1",
            password="11111111",
            secret="239DF91F - 49C9A59C - 4E5A32B8 - 1FFA0A7D - 8681B634 - 6B9C5774 - DBD7D9A6 - 78935EF8",
            kcv="9628716E",
            key_attributes={"cbD0": "Standard_Algorithm", "cbD1": "AES"},
        ),
        CKCImportKeyCustodianParty(
            username="kcp2",
            password="11111111",
            secret="D038EE3F - 9BE0B95A - C144B02B - D9775DA0 - EA09E094 - 80EE8BAA - 83185E1C - 69985F60",
            kcv="D968CE34",
        ),
        CKCImportKeyCustodianParty(
            username="kcp3",
            password="11111111",
            secret="A833F6AE - 47A22917 - 3BE2C64D - 02DB00D2 - 73D61D74 - 3AFE73F5 - F76993D0 - 232D37A2",
            kcv="D8D146F6",
        ),
    ])

    @classmethod
    def from_env(cls, **overrides):
        """Create instance with environment variable overrides."""
        defaults = cls()

        kwargs = {
            "admin_username": os.environ.get("CKCI_ADMIN_USERNAME", defaults.admin_username),
            "admin_password": os.environ.get("CKCI_ADMIN_PASSWORD", defaults.admin_password),
            "key_label": os.environ.get("CKCI_KEY_LABEL", defaults.key_label),
            "key_algo": os.environ.get("CKCI_KEY_ALGO", defaults.key_algo),
            "key_length": os.environ.get("CKCI_KEY_LENGTH", defaults.key_length),
            "key_usage": os.environ.get("CKCI_KEY_USAGE", defaults.key_usage),
            "cps_key_type": os.environ.get("CKCI_CPS_KEY_TYPE", defaults.cps_key_type),
            "key_mac": os.environ.get("CKCI_KEY_MAC", defaults.key_mac),
            "customer_key_kcv": os.environ.get("CKCI_CUSTOMER_KEY_KCV", defaults.customer_key_kcv),
        }

        # Build custodian parties with env overrides
        kcp_list = []
        for i, default_kcp in enumerate(defaults.custodian_parties, start=1):
            kcp_list.append(CKCImportKeyCustodianParty(
                username=default_kcp.username,
                password=default_kcp.password,
                secret=os.environ.get(f"CKCI_KCP{i}_SECRET", default_kcp.secret),
                kcv=os.environ.get(f"CKCI_KCP{i}_KCV", default_kcp.kcv),
                key_attributes=default_kcp.key_attributes,
            ))
        kwargs["custodian_parties"] = kcp_list

        kwargs.update(overrides)
        return cls(**kwargs)
