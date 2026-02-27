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

logger = logging.getLogger(__name__)


class MetricsPusher:
    """Push test metrics to Prometheus Pushgateway for Grafana visualization."""

    def __init__(self, pushgateway_url="http://localhost:9091",
                 job_name="hsm_tests", labels=None):
        self.pushgateway_url = pushgateway_url
        self.job_name = job_name
        self.labels = labels or {}
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
                ["suite", "test_name", "status", *self.labels.keys()],
                registry=self.registry,
            )

            self.test_duration = Histogram(
                "hsm_test_duration_seconds",
                "Test execution duration in seconds",
                ["suite", "test_name"],
                buckets=[1, 5, 10, 30, 60, 120, 300],
                registry=self.registry,
            )

            self.suite_pass_rate = Gauge(
                "hsm_suite_pass_rate",
                "Test suite pass rate (0-1)",
                ["suite"],
                registry=self.registry,
            )

            self.suite_duration = Gauge(
                "hsm_suite_duration_seconds",
                "Total suite execution time",
                ["suite"],
                registry=self.registry,
            )

            self.last_run_timestamp = Gauge(
                "hsm_last_run_timestamp",
                "Timestamp of last test run",
                ["suite"],
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
            suite=suite, test_name=test_name, status=status, **self.labels
        ).inc()

        self.test_duration.labels(suite=suite, test_name=test_name).observe(duration)

    def record_suite(self, suite, total, passed, duration):
        """Record suite-level metrics."""
        if not self.registry:
            return

        pass_rate = passed / total if total > 0 else 0
        self.suite_pass_rate.labels(suite=suite).set(pass_rate)
        self.suite_duration.labels(suite=suite).set(duration)
        self.last_run_timestamp.labels(suite=suite).set(time.time())

    def push(self):
        """Push all metrics to Pushgateway."""
        if not self.registry:
            return

        try:
            from prometheus_client import push_to_gateway

            push_to_gateway(
                self.pushgateway_url,
                job=self.job_name,
                registry=self.registry,
            )
            logger.info(f"Metrics pushed to {self.pushgateway_url}")
        except Exception as e:
            logger.warning(f"Failed to push metrics: {e}")
