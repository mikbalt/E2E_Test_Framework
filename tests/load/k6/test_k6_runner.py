"""Pytest wrapper for k6 load tests.

Runs k6 scripts via subprocess with --summary-export and asserts thresholds.
Auto-skips if k6 is not installed.
"""

import json
import os
import shutil
import subprocess
import tempfile

import pytest

pytestmark = [pytest.mark.load]

K6_SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "scripts")


@pytest.fixture(scope="session", autouse=True)
def check_k6_installed():
    """Skip all k6 tests if k6 binary is not available."""
    if not shutil.which("k6"):
        pytest.skip("k6 is not installed — skipping k6 tests")


class TestK6Runner:
    """Run k6 load test scripts and verify results."""

    def _run_k6(self, script: str, target_url: str, extra_env: dict | None = None) -> dict:
        """Run a k6 script with --summary-export. Returns summary dict."""
        script_path = os.path.join(K6_SCRIPTS_DIR, script)
        summary_file = os.path.join(tempfile.mkdtemp(), "summary.json")

        env = os.environ.copy()
        env["TARGET_URL"] = target_url
        env.setdefault("ADMIN_USER", "admin")
        env.setdefault("ADMIN_PASS", "admin123")
        env.setdefault("K6_VUS", "5")
        env.setdefault("K6_DURATION", "10s")
        if extra_env:
            env.update(extra_env)

        cmd = ["k6", "run", "--summary-export", summary_file, script_path]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )

        summary = {}
        if os.path.exists(summary_file):
            with open(summary_file) as f:
                summary = json.load(f)
            os.unlink(summary_file)

        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "summary": summary,
        }

    def test_auth_k6(self):
        """Run k6 auth load test."""
        target = os.environ.get("WORKSPACE_API_URL", "http://localhost:8000")
        result = self._run_k6("auth.js", target)
        assert result["returncode"] == 0, (
            f"k6 auth test failed:\n{result['stderr'][-2000:]}"
        )

    def test_health_k6(self):
        """Run k6 health endpoint stress test."""
        target = os.environ.get("WORKSPACE_API_URL", "http://localhost:8000")
        result = self._run_k6("health.js", target)
        assert result["returncode"] == 0, (
            f"k6 health test failed:\n{result['stderr'][-2000:]}"
        )

    def test_full_scenario_k6(self):
        """Run k6 full scenario load test."""
        target = os.environ.get("WORKSPACE_API_URL", "http://localhost:8000")
        result = self._run_k6("full_scenario.js", target)
        assert result["returncode"] == 0, (
            f"k6 full scenario test failed:\n{result['stderr'][-2000:]}"
        )
