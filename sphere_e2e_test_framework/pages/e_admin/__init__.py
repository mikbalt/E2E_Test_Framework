"""
E-Admin Page Object Model (POM) classes.

Usage::

    from sphere_e2e_test_framework.pages.e_admin import LoginPage, DashboardPage

    login = LoginPage(driver, evidence)
    dashboard = login.connect_to_hsm(step_name="Connect to HSM")
"""

from sphere_e2e_test_framework.pages.e_admin.e_admin_base_page import EAdminBasePage
from sphere_e2e_test_framework.pages.e_admin.login_page import LoginPage
from sphere_e2e_test_framework.pages.e_admin.dashboard_page import DashboardPage
from sphere_e2e_test_framework.pages.e_admin.terms_page import TermsPage
from sphere_e2e_test_framework.pages.e_admin.password_change_page import PasswordChangePage
from sphere_e2e_test_framework.pages.e_admin.user_creation_page import UserCreationPage
from sphere_e2e_test_framework.pages.e_admin.kc_login_page import KCLoginPage
from sphere_e2e_test_framework.pages.e_admin.ccmk_import_page import CCMKImportPage
from sphere_e2e_test_framework.pages.e_admin.key_ceremony_page import KeyCeremonyFlow
from sphere_e2e_test_framework.pages.e_admin.ckc_page import CustomerKeyCeremonyPage
from sphere_e2e_test_framework.pages.e_admin.profile_management_page import ProfileManagementPage
from sphere_e2e_test_framework.pages.e_admin.user_management_page import UserManagementPage

__all__ = [
    "EAdminBasePage",
    "LoginPage",
    "DashboardPage",
    "TermsPage",
    "PasswordChangePage",
    "UserCreationPage",
    "KCLoginPage",
    "CCMKImportPage",
    "KeyCeremonyFlow",
    "CustomerKeyCeremonyPage",
    "ProfileManagementPage",
    "UserManagementPage",
]
