"""Driver modules — infrastructure, evidence, integrations.

Re-exports key classes for convenience::

    from sphere_e2e_test_framework.driver import UIDriver, Evidence, tracked_step
"""

from sphere_e2e_test_framework.driver.evidence import Evidence, StepTracker, tracked_step
from sphere_e2e_test_framework.driver.console_runner import ConsoleRunner, CommandResult, resolve_platform_config
from sphere_e2e_test_framework.driver.log_collector import LogCollector, LogMonitor
from sphere_e2e_test_framework.driver.kiwi_tcms import KiwiReporter
from sphere_e2e_test_framework.driver.grafana_push import MetricsPusher
from sphere_e2e_test_framework.driver.health_check import HealthChecker, HealthCheckResult, HealthCheckReport
from sphere_e2e_test_framework.driver.smoke_gate import SmokeGate
from sphere_e2e_test_framework.driver.appmanager import UIAppManager
from sphere_e2e_test_framework.driver.cli_driver import CLIDriver
from sphere_e2e_test_framework.driver.config_validator import ConfigValidator, ConfigValidationError

__all__ = [
    "Evidence",
    "StepTracker",
    "tracked_step",
    "ConsoleRunner",
    "CommandResult",
    "resolve_platform_config",
    "LogCollector",
    "LogMonitor",
    "KiwiReporter",
    "MetricsPusher",
    "HealthChecker",
    "HealthCheckResult",
    "HealthCheckReport",
    "SmokeGate",
    "UIAppManager",
    "CLIDriver",
    "ConfigValidator",
    "ConfigValidationError",
]
