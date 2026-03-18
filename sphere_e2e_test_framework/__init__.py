"""
Sphere E2E Test Framework - Reusable base for E2E testing across multiple repositories.

Install in consumer repos:
    pip install git+https://gitlab.yourcompany.com/qa/sphere-e2e-test-framework.git

Usage in consumer test files:
    from sphere_e2e_test_framework import UIDriver, ConsoleRunner, Evidence, LogCollector
"""

import importlib

__version__ = "1.2.0"

# Eagerly import cross-platform modules only
from sphere_e2e_test_framework.driver.evidence import Evidence, StepTracker, tracked_step
from sphere_e2e_test_framework.driver.console_runner import ConsoleRunner, CommandResult, resolve_platform_config
from sphere_e2e_test_framework.driver.log_collector import LogCollector, LogMonitor
from sphere_e2e_test_framework.driver.kiwi_tcms import KiwiReporter
from sphere_e2e_test_framework.driver.grafana_push import MetricsPusher
from sphere_e2e_test_framework.driver.health_check import HealthChecker, HealthCheckResult, HealthCheckReport
from sphere_e2e_test_framework.driver.smoke_gate import SmokeGate

# Lazy import for platform-specific / optional-dep modules (generic core)
_LAZY_IMPORTS = {
    "UIDriver": "sphere_e2e_test_framework.driver.ui_driver",
    "WindowMonitor": "sphere_e2e_test_framework.driver.window_monitor",
    "RemoteTrigger": "sphere_e2e_test_framework.driver.remote_trigger",
    "RemoteResult": "sphere_e2e_test_framework.driver.remote_trigger",
    "RemoteAgentPool": "sphere_e2e_test_framework.driver.remote_trigger",
    "LokiLogCollector": "sphere_e2e_test_framework.driver.loki_collector",
    "DriverProtocol": "sphere_e2e_test_framework.driver.base",
    "BasePage": "sphere_e2e_test_framework.pages.base_page",
}

# Backward-compat lazy imports for E-Admin page objects.
# NOT in __all__ — new consumers should import from pages.e_admin directly.
_LAZY_IMPORTS_COMPAT = {
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
    if name in _LAZY_IMPORTS_COMPAT:
        module = importlib.import_module(_LAZY_IMPORTS_COMPAT[name])
        return getattr(module, name)
    raise AttributeError(f"module 'sphere_e2e_test_framework' has no attribute {name!r}")


__all__ = [
    # Core driver infrastructure
    "UIDriver",
    "DriverProtocol",
    "ConsoleRunner",
    "CommandResult",
    "resolve_platform_config",
    "Evidence",
    "StepTracker",
    "tracked_step",
    "LogCollector",
    "LogMonitor",
    "LokiLogCollector",
    "KiwiReporter",
    "MetricsPusher",
    "HealthChecker",
    "HealthCheckResult",
    "HealthCheckReport",
    "SmokeGate",
    "WindowMonitor",
    "RemoteTrigger",
    "RemoteResult",
    "RemoteAgentPool",
    # Generic Page Object base
    "BasePage",
]
