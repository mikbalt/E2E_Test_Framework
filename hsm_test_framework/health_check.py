"""
Health Check - Pre-execution environment verification.

Verifies test environment readiness before test collection begins.
Prevents cryptic failures by aborting early with clear diagnostics.

Supported check types:
    - tcp: Verify a TCP port is open (socket connect)
    - ping: Verify host is reachable (ICMP ping)
    - http: Verify HTTP endpoint responds

Usage (automatic via plugin):
    Runs automatically in pytest_sessionstart unless --skip-health-check.

Manual usage:
    checker = HealthChecker(config["health_check"])
    report = checker.run_all()
    if not report.all_passed:
        sys.exit(1)
"""

import logging
import platform
import socket
import subprocess
import time

logger = logging.getLogger(__name__)


class HealthCheckResult:
    """Result of a single health check."""

    def __init__(self, label, check_type, host, passed, message, duration=0.0):
        self.label = label
        self.check_type = check_type
        self.host = host
        self.passed = passed
        self.message = message
        self.duration = duration

    def __repr__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.label}: {self.message}"


class HealthCheckReport:
    """Aggregated result of all health checks."""

    def __init__(self):
        self.results = []

    def add(self, result):
        self.results.append(result)

    @property
    def all_passed(self):
        return all(r.passed for r in self.results)

    def summary(self):
        lines = ["=" * 60, "Health Check Results", "=" * 60]
        for r in self.results:
            lines.append(str(r))
        lines.append("=" * 60)
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        lines.append(f"Result: {passed}/{total} checks passed")
        if not self.all_passed:
            failed = [r for r in self.results if not r.passed]
            lines.append("")
            lines.append("Failed checks:")
            for r in failed:
                lines.append(f"  - {r.label}: {r.message}")
            lines.append("")
            lines.append("ABORTING: Environment not ready for testing.")
        lines.append("=" * 60)
        return "\n".join(lines)


class HealthChecker:
    """Run pre-execution health checks against the test environment."""

    def __init__(self, health_config):
        """
        Args:
            health_config: Dict from settings.yaml 'health_check' section.
                Expected keys: enabled (bool), checks (list of check dicts).
        """
        self.enabled = health_config.get("enabled", False)
        self.checks = health_config.get("checks", [])

    def run_all(self):
        """Execute all configured checks and return a HealthCheckReport."""
        report = HealthCheckReport()

        if not self.enabled:
            logger.info("Health checks disabled in config")
            return report

        logger.info("Running pre-execution health checks...")

        for check_def in self.checks:
            check_type = check_def.get("type", "tcp")
            label = check_def.get("label", f"{check_type} check")
            host = check_def.get("host", "")
            timeout = check_def.get("timeout", 5)

            logger.info(f"Health check: {label} ({check_type})")

            if check_type == "tcp":
                port = int(check_def.get("port", 0))
                result = self._check_tcp(host, port, timeout, label)
            elif check_type == "ping":
                result = self._check_ping(host, timeout, label)
            elif check_type == "http":
                url = check_def.get("url", f"http://{host}")
                result = self._check_http(url, timeout, label)
            else:
                result = HealthCheckResult(
                    label=label, check_type=check_type, host=host,
                    passed=False, message=f"Unknown check type: {check_type}",
                )

            report.add(result)
            logger.info(str(result))

        return report

    def _check_tcp(self, host, port, timeout, label):
        """Check if a TCP port is open."""
        start = time.time()
        try:
            with socket.create_connection((host, port), timeout=timeout):
                duration = time.time() - start
                return HealthCheckResult(
                    label=label, check_type="tcp", host=f"{host}:{port}",
                    passed=True,
                    message=f"TCP {host}:{port} is open ({duration:.2f}s)",
                    duration=duration,
                )
        except (socket.timeout, socket.error, OSError) as e:
            duration = time.time() - start
            return HealthCheckResult(
                label=label, check_type="tcp", host=f"{host}:{port}",
                passed=False,
                message=f"TCP {host}:{port} unreachable: {e}",
                duration=duration,
            )

    def _check_ping(self, host, timeout, label):
        """Check if a host responds to ICMP ping."""
        is_windows = platform.system() == "Windows"
        if is_windows:
            cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), host]
        else:
            cmd = ["ping", "-c", "1", "-W", str(timeout), host]

        start = time.time()
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout + 5,
            )
            duration = time.time() - start
            if proc.returncode == 0:
                return HealthCheckResult(
                    label=label, check_type="ping", host=host,
                    passed=True,
                    message=f"Ping {host} OK ({duration:.2f}s)",
                    duration=duration,
                )
            else:
                return HealthCheckResult(
                    label=label, check_type="ping", host=host,
                    passed=False,
                    message=f"Ping {host} failed (rc={proc.returncode})",
                    duration=duration,
                )
        except subprocess.TimeoutExpired:
            duration = time.time() - start
            return HealthCheckResult(
                label=label, check_type="ping", host=host,
                passed=False,
                message=f"Ping {host} timed out after {timeout}s",
                duration=duration,
            )

    def _check_http(self, url, timeout, label):
        """Check if an HTTP endpoint responds."""
        import ssl
        from urllib.request import Request, urlopen

        start = time.time()
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = Request(url, method="HEAD")
            resp = urlopen(req, timeout=timeout, context=ctx)
            duration = time.time() - start
            return HealthCheckResult(
                label=label, check_type="http", host=url,
                passed=True,
                message=f"HTTP {url} -> {resp.status} ({duration:.2f}s)",
                duration=duration,
            )
        except Exception as e:
            duration = time.time() - start
            return HealthCheckResult(
                label=label, check_type="http", host=url,
                passed=False,
                message=f"HTTP {url} failed: {e}",
                duration=duration,
            )
