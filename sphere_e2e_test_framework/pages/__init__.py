"""
Page Object Model (POM) classes.

Only ``BasePage`` is eagerly imported. E-Admin page objects are available
via lazy import for backward compatibility — prefer importing from
``sphere_e2e_test_framework.pages.e_admin`` directly for new code.
"""

import importlib

from sphere_e2e_test_framework.pages.base_page import BasePage

__all__ = ["BasePage"]

# Backward-compat lazy imports for E-Admin page objects.
_LAZY_IMPORTS = {
    "EAdminBasePage": "sphere_e2e_test_framework.pages.e_admin.e_admin_base_page",
    "LoginPage": "sphere_e2e_test_framework.pages.e_admin.login_page",
    "DashboardPage": "sphere_e2e_test_framework.pages.e_admin.dashboard_page",
    "TermsPage": "sphere_e2e_test_framework.pages.e_admin.terms_page",
    "PasswordChangePage": "sphere_e2e_test_framework.pages.e_admin.password_change_page",
    "UserCreationPage": "sphere_e2e_test_framework.pages.e_admin.user_creation_page",
    "KCLoginPage": "sphere_e2e_test_framework.pages.e_admin.kc_login_page",
    "CCMKImportPage": "sphere_e2e_test_framework.pages.e_admin.ccmk_import_page",
    "KeyCeremonyFlow": "sphere_e2e_test_framework.pages.e_admin.key_ceremony_page",
    "ProfileManagementPage": "sphere_e2e_test_framework.pages.e_admin.profile_management_page",
    "UserManagementPage": "sphere_e2e_test_framework.pages.e_admin.user_management_page",
}


def __getattr__(name):
    if name in _LAZY_IMPORTS:
        module = importlib.import_module(_LAZY_IMPORTS[name])
        return getattr(module, name)
    raise AttributeError(f"module 'sphere_e2e_test_framework.pages' has no attribute {name!r}")
