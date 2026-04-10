"""Driver modules — infrastructure, evidence, integrations.

Re-exports key classes for convenience::

    from ankole.driver import UIDriver, Evidence, tracked_step
"""

from ankole.driver.evidence import Evidence, StepTracker, tracked_step
from ankole.driver.console_runner import ConsoleRunner, CommandResult, resolve_platform_config
from ankole.driver.log_collector import LogCollector, LogMonitor
from ankole.driver.kiwi_tcms import KiwiReporter
from ankole.driver.grafana_push import MetricsPusher
from ankole.driver.health_check import HealthChecker, HealthCheckResult, HealthCheckReport
from ankole.driver.smoke_gate import SmokeGate
from ankole.driver.appmanager import UIAppManager
from ankole.driver.cli_driver import CLIDriver
from ankole.driver.config_validator import ConfigValidator, ConfigValidationError

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
