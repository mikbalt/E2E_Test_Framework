"""
HSM Test Framework - Reusable base for E2E testing across multiple repositories.

Install in consumer repos:
    pip install git+https://gitlab.yourcompany.com/qa/hsm-test-framework.git

Usage in consumer test files:
    from hsm_test_framework import UIDriver, ConsoleRunner, Evidence, LogCollector
"""

import importlib

__version__ = "1.2.0"

# Eagerly import cross-platform modules only
from hsm_test_framework.evidence import Evidence, StepTracker, tracked_step
from hsm_test_framework.console_runner import ConsoleRunner, CommandResult, resolve_platform_config
from hsm_test_framework.log_collector import LogCollector, LogMonitor
from hsm_test_framework.kiwi_tcms import KiwiReporter
from hsm_test_framework.grafana_push import MetricsPusher
from hsm_test_framework.health_check import HealthChecker, HealthCheckResult, HealthCheckReport
from hsm_test_framework.smoke_gate import SmokeGate

# Lazy import for platform-specific / optional-dep modules
_LAZY_IMPORTS = {
    "UIDriver": "hsm_test_framework.ui_driver",
    "WindowMonitor": "hsm_test_framework.window_monitor",
    "RemoteTrigger": "hsm_test_framework.remote_trigger",
    "RemoteResult": "hsm_test_framework.remote_trigger",
    "RemoteAgentPool": "hsm_test_framework.remote_trigger",
    "LokiLogCollector": "hsm_test_framework.loki_collector",
    # Page Object Model classes
    "BasePage": "hsm_test_framework.pages.base_page",
    "LoginPage": "hsm_test_framework.pages.login_page",
    "DashboardPage": "hsm_test_framework.pages.dashboard_page",
    "TermsPage": "hsm_test_framework.pages.terms_page",
    "PasswordChangePage": "hsm_test_framework.pages.password_change_page",
    "UserCreationPage": "hsm_test_framework.pages.user_creation_page",
    "KCLoginPage": "hsm_test_framework.pages.kc_login_page",
    "CCMKImportPage": "hsm_test_framework.pages.ccmk_import_page",
    "KeyCeremonyFlow": "hsm_test_framework.pages.key_ceremony_page",
    "ProfileManagementPage": "hsm_test_framework.pages.profile_management_page",
    "UserManagementPage": "hsm_test_framework.pages.user_management_page",
}


def __getattr__(name):
    if name in _LAZY_IMPORTS:
        module = importlib.import_module(_LAZY_IMPORTS[name])
        return getattr(module, name)
    raise AttributeError(f"module 'hsm_test_framework' has no attribute {name!r}")


__all__ = [
    "UIDriver",
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
    # Page Object Model
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
