"""
HSM Test Framework - Reusable base for E2E testing across multiple repositories.

Install in consumer repos:
    pip install git+https://gitlab.yourcompany.com/qa/hsm-test-framework.git

Usage in consumer test files:
    from hsm_test_framework import UIDriver, ConsoleRunner, Evidence, LogCollector
"""

__version__ = "1.1.0"

from hsm_test_framework.ui_driver import UIDriver
from hsm_test_framework.console_runner import ConsoleRunner, CommandResult, resolve_platform_config
from hsm_test_framework.evidence import Evidence, StepTracker
from hsm_test_framework.log_collector import LogCollector, LogMonitor
from hsm_test_framework.kiwi_tcms import KiwiReporter
from hsm_test_framework.grafana_push import MetricsPusher

__all__ = [
    "UIDriver",
    "ConsoleRunner",
    "CommandResult",
    "resolve_platform_config",
    "Evidence",
    "StepTracker",
    "LogCollector",
    "LogMonitor",
    "KiwiReporter",
    "MetricsPusher",
]
