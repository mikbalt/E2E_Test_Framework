"""
Grafana Metrics - Push test metrics to Prometheus Pushgateway for Grafana dashboards.

Tracks:
- Test pass/fail counts
- Test duration
- Test suite execution time
- Historical trends

Requires Prometheus Pushgateway running (usually alongside Grafana).

Usage (via conftest.py - automatic):
    Metrics are automatically pushed after test session completes.

Manual usage:
    metrics = MetricsPusher("http://localhost:9091", job_name="hsm_tests")
    metrics.record_test("test_login", passed=True, duration=3.5)
    metrics.push()
"""

import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class MetricsPusher:
    """Push test metrics to Prometheus Pushgateway for Grafana visualization."""

    def __init__(self, pushgateway_url="http://localhost:9091",
                 job_name="hsm_tests", labels=None, run_id=None):
        self.pushgateway_url = pushgateway_url
        self.job_name = job_name
        self.labels = labels or {}
        self.run_id = run_id or datetime.now().strftime("run_%Y%m%d_%H%M%S")
        self.registry = None
        self._setup_metrics()

    def _setup_metrics(self):
        """Initialize Prometheus metrics."""
        try:
            from prometheus_client import (
                CollectorRegistry,
                Counter,
                Gauge,
                Histogram,
            )

            self.registry = CollectorRegistry()

            self.tests_total = Counter(
                "hsm_tests_total",
                "Total number of tests executed",
                ["suite", "test_name", "status", "run_id", *self.labels.keys()],
                registry=self.registry,
            )

            self.test_duration = Histogram(
                "hsm_test_duration_seconds",
                "Test execution duration in seconds",
                ["suite", "test_name", "run_id"],
                buckets=[1, 5, 10, 30, 60, 120, 300],
                registry=self.registry,
            )

            self.suite_pass_rate = Gauge(
                "hsm_suite_pass_rate",
                "Pass rate of executed tests: passed/(passed+failed)",
                ["suite", "run_id"],
                registry=self.registry,
            )

            self.suite_coverage = Gauge(
                "hsm_suite_coverage",
                "Automation coverage: (passed+failed)/(total including blocked)",
                ["suite", "run_id"],
                registry=self.registry,
            )

            self.suite_duration = Gauge(
                "hsm_suite_duration_seconds",
                "Total suite execution time",
                ["suite", "run_id"],
                registry=self.registry,
            )

            self.last_run_timestamp = Gauge(
                "hsm_last_run_timestamp",
                "Timestamp of last test run",
                ["suite", "run_id"],
                registry=self.registry,
            )

            self.suite_total = Gauge(
                "hsm_suite_total",
                "Total test cases in suite (including blocked)",
                ["suite", "run_id"],
                registry=self.registry,
            )

            self.suite_passed = Gauge(
                "hsm_suite_passed",
                "Number of passed tests",
                ["suite", "run_id"],
                registry=self.registry,
            )

            self.suite_failed = Gauge(
                "hsm_suite_failed",
                "Number of failed tests",
                ["suite", "run_id"],
                registry=self.registry,
            )

            self.suite_blocked = Gauge(
                "hsm_suite_blocked",
                "Number of blocked test cases (no automation)",
                ["suite", "run_id"],
                registry=self.registry,
            )

            logger.info("Prometheus metrics initialized")
        except ImportError:
            logger.warning("prometheus_client not installed, metrics disabled")
            self.registry = None

    def record_test(self, test_name, passed, duration, suite="default"):
        """Record a single test result."""
        if not self.registry:
            return

        status = "passed" if passed else "failed"

        self.tests_total.labels(
            suite=suite, test_name=test_name, status=status,
            run_id=self.run_id, **self.labels
        ).inc()

        self.test_duration.labels(
            suite=suite, test_name=test_name, run_id=self.run_id
        ).observe(duration)

    def record_suite(self, suite, total, passed, duration, blocked=0):
        """Record suite-level metrics."""
        if not self.registry:
            return

        failed = total - passed
        grand_total = total + blocked
        executed = passed + failed
        pass_rate = passed / executed if executed > 0 else 0
        coverage = executed / grand_total if grand_total > 0 else 0

        self.suite_pass_rate.labels(suite=suite, run_id=self.run_id).set(pass_rate)
        self.suite_coverage.labels(suite=suite, run_id=self.run_id).set(coverage)
        self.suite_duration.labels(suite=suite, run_id=self.run_id).set(duration)
        self.last_run_timestamp.labels(suite=suite, run_id=self.run_id).set(time.time())
        self.suite_total.labels(suite=suite, run_id=self.run_id).set(grand_total)
        self.suite_passed.labels(suite=suite, run_id=self.run_id).set(passed)
        self.suite_failed.labels(suite=suite, run_id=self.run_id).set(failed)
        self.suite_blocked.labels(suite=suite, run_id=self.run_id).set(blocked)

    def push(self):
        """Push all metrics to Pushgateway (additive — preserves previous runs)."""
        if not self.registry:
            return

        try:
            from prometheus_client import pushadd_to_gateway

            pushadd_to_gateway(
                self.pushgateway_url,
                job=self.job_name,
                registry=self.registry,
                grouping_key={"run_id": self.run_id},
            )
            logger.info(f"Metrics pushed to {self.pushgateway_url} "
                        f"(run_id={self.run_id})")
        except Exception as e:
            logger.warning(f"Failed to push metrics: {e}")

    def delete_run(self):
        """Delete metrics for this run_id from Pushgateway."""
        try:
            from prometheus_client import delete_from_gateway

            delete_from_gateway(
                self.pushgateway_url,
                job=self.job_name,
                grouping_key={"run_id": self.run_id},
            )
            logger.info(f"Deleted metrics for run_id={self.run_id}")
        except Exception as e:
            logger.warning(f"Failed to delete metrics: {e}")
