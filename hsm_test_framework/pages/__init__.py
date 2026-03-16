"""
E-Admin Page Object Model (POM) classes.

Usage::

    from hsm_test_framework.pages import LoginPage, DashboardPage

    login = LoginPage(driver, evidence)
    dashboard = login.connect_to_hsm(step_name="Connect to HSM")
"""

from hsm_test_framework.pages.base_page import BasePage
from hsm_test_framework.pages.login_page import LoginPage
from hsm_test_framework.pages.dashboard_page import DashboardPage
from hsm_test_framework.pages.terms_page import TermsPage
from hsm_test_framework.pages.password_change_page import PasswordChangePage
from hsm_test_framework.pages.user_creation_page import UserCreationPage
from hsm_test_framework.pages.kc_login_page import KCLoginPage
from hsm_test_framework.pages.ccmk_import_page import CCMKImportPage
from hsm_test_framework.pages.key_ceremony_page import KeyCeremonyFlow
from hsm_test_framework.pages.profile_management_page import ProfileManagementPage
from hsm_test_framework.pages.user_management_page import UserManagementPage

__all__ = [
    "BasePage",
    "LoginPage",
    "DashboardPage",
    "TermsPage",
    "PasswordChangePage",
    "UserCreationPage",
    "KCLoginPage",
    "CCMKImportPage",
    "KeyCeremonyFlow",
    "ProfileManagementPage",
    "UserManagementPage",
]
