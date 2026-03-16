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
