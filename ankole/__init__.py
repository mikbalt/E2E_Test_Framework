"""
Ankole Framework - Multi-driver E2E test framework.

Supports Playwright (web), pywinauto (desktop), httpx (API), and subprocess (CLI)
with full observability: Grafana, Prometheus, Loki, Allure, Kiwi TCMS.

Install:
    pip install ankole-framework[all]

Usage:
    from ankole import WebDriver, APIDriver, UIDriver, ConsoleRunner, Evidence
"""

import importlib

__version__ = "2.0.0"

# Eagerly import cross-platform modules only
from ankole.driver.evidence import Evidence, StepTracker, tracked_step
from ankole.driver.console_runner import ConsoleRunner, CommandResult, resolve_platform_config
from ankole.driver.log_collector import LogCollector, LogMonitor
from ankole.driver.kiwi_tcms import KiwiReporter
from ankole.driver.grafana_push import MetricsPusher
from ankole.driver.health_check import HealthChecker, HealthCheckResult, HealthCheckReport
from ankole.driver.smoke_gate import SmokeGate

# Lazy import for platform-specific / optional-dep modules
_LAZY_IMPORTS = {
    # Desktop (pywinauto)
    "UIDriver": "ankole.driver.ui_driver",
    "WindowMonitor": "ankole.driver.window_monitor",
    "UIAppManager": "ankole.driver.appmanager",
    # Web (Playwright)
    "WebDriver": "ankole.driver.web_driver",
    # API (httpx)
    "APIDriver": "ankole.driver.api_driver",
    # Infrastructure
    "RemoteTrigger": "ankole.driver.remote_trigger",
    "RemoteResult": "ankole.driver.remote_trigger",
    "RemoteAgentPool": "ankole.driver.remote_trigger",
    "LokiLogCollector": "ankole.driver.loki_collector",
    "DriverProtocol": "ankole.driver.base",
    "WebDriverProtocol": "ankole.driver.base",
    "APIDriverProtocol": "ankole.driver.base",
    "CLIDriver": "ankole.driver.cli_driver",
    "ConfigValidator": "ankole.driver.config_validator",
    "ConfigValidationError": "ankole.driver.config_validator",
    "BasePage": "ankole.pages.base_page",
}


def __getattr__(name):
    if name in _LAZY_IMPORTS:
        module = importlib.import_module(_LAZY_IMPORTS[name])
        return getattr(module, name)
    raise AttributeError(f"module 'ankole' has no attribute {name!r}")


__all__ = [
    # Core driver infrastructure
    "UIDriver",
    "WebDriver",
    "APIDriver",
    "DriverProtocol",
    "WebDriverProtocol",
    "APIDriverProtocol",
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
