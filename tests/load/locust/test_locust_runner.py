"""Pytest wrapper for Locust load tests.

Runs locust in headless mode via subprocess and asserts exit code.
"""

import os
import subprocess
import sys

import pytest

pytestmark = [pytest.mark.load]

LOCUST_DIR = os.path.dirname(__file__)


class TestLocustRunner:
    """Run Locust load tests headlessly and verify results."""

    def _run_locust(self, locustfile: str, locust_config: dict, target_url: str) -> int:
        """Run a locustfile in headless mode. Returns process return code."""
        filepath = os.path.join(LOCUST_DIR, locustfile)
        cmd = [
            sys.executable, "-m", "locust",
            "-f", filepath,
            "--headless",
            "--host", target_url,
            "-u", str(locust_config.get("users", 5)),
            "-r", str(locust_config.get("spawn_rate", 2)),
            "-t", locust_config.get("run_time", "10s"),
            "--json",
        ]
        env = os.environ.copy()
        env["TARGET_HOST"] = target_url
        env.setdefault("ADMIN_USER", "admin")
        env.setdefault("ADMIN_PASS", "admin123")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
        if result.returncode != 0:
            print(f"STDOUT:\n{result.stdout[-2000:]}")
            print(f"STDERR:\n{result.stderr[-2000:]}")
        return result.returncode

    def test_auth_load(self, locust_config, target_url):
        """Run auth flow load test."""
        rc = self._run_locust("locustfile_auth.py", locust_config, target_url)
        assert rc == 0, f"Locust auth load test failed with exit code {rc}"

    def test_members_load(self, locust_config, target_url):
        """Run member CRUD load test."""
        rc = self._run_locust("locustfile_members.py", locust_config, target_url)
        assert rc == 0, f"Locust members load test failed with exit code {rc}"

    def test_full_scenario_load(self, locust_config, target_url):
        """Run full scenario load test."""
        rc = self._run_locust("locustfile_full.py", locust_config, target_url)
        assert rc == 0, f"Locust full scenario load test failed with exit code {rc}"
