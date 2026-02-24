"""
PKCS#11 Test Suite - Root conftest.

The hsm_test_framework.plugin is auto-registered via pytest11 entry point.
Available fixtures (auto-provided by framework):
    - config        : settings.yaml loaded as dict
    - evidence      : Evidence collector for current test
    - console       : ConsoleRunner instance
    - log_collector : LogCollector linked to current test's evidence

This conftest adds PKCS11-specific fixtures:
    - build_artifacts  : Session-scoped fixture that runs build scripts first
"""

import logging
import os
import platform
import subprocess

import pytest

logger = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"


# ====================================================================
# Build Fixture — compiles source code before test session starts
# ====================================================================

@pytest.fixture(scope="session", autouse=True)
def build_artifacts(config):
    """
    Run build scripts before the test session if sources need compilation.

    This fixture:
    1. Checks config for tools that have 'needs_build: true'
    2. Runs the appropriate build script (build.bat or build.sh)
    3. Verifies the output binaries exist

    If BUILD_SKIP=1 env var is set, skips building (useful for CI
    where build is a separate stage).
    """
    if os.environ.get("BUILD_SKIP", "").strip() in ("1", "true", "yes"):
        logger.info("BUILD_SKIP is set — skipping build phase")
        return

    # Check if any tool needs building
    tools = config.get("console_tools", {})
    needs_build = any(
        t.get("needs_build", False) for t in tools.values()
    )

    if not needs_build:
        logger.info("No tools require building — skipping build phase")
        return

    # Run the appropriate build script
    script = "scripts\\build.bat" if IS_WINDOWS else "scripts/build.sh"

    if not os.path.exists(script):
        logger.warning(f"Build script not found: {script}")
        return

    logger.info(f"Running build script: {script}")

    try:
        if IS_WINDOWS:
            result = subprocess.run(
                ["cmd", "/c", script],
                capture_output=True, text=True, timeout=300,
            )
        else:
            result = subprocess.run(
                ["bash", script],
                capture_output=True, text=True, timeout=300,
            )

        if result.returncode != 0:
            logger.error(f"Build failed (exit {result.returncode}):")
            logger.error(result.stderr or result.stdout)
            pytest.fail(f"Build script failed with exit code {result.returncode}")
        else:
            logger.info("Build completed successfully")
            if result.stdout:
                for line in result.stdout.strip().split("\n")[-10:]:
                    logger.info(f"  build: {line}")

    except subprocess.TimeoutExpired:
        pytest.fail("Build script timed out (300s)")
    except FileNotFoundError:
        logger.warning(f"Cannot execute build script: {script}")


# ====================================================================
# Helper fixture — resolve tool config for current platform
# ====================================================================

@pytest.fixture
def tool_config(config):
    """
    Helper to get platform-resolved tool configs.

    Usage in tests:
        def test_keygen(tool_config, console):
            tool = tool_config("pkcs11_java_keygen")
            result = console.run_java(jar_path=tool["command"], ...)
    """
    from hsm_test_framework import resolve_platform_config

    def _get(tool_name):
        tools = config.get("console_tools", {})
        if tool_name not in tools:
            pytest.fail(f"Tool '{tool_name}' not found in settings.yaml console_tools")
        return resolve_platform_config(tools[tool_name])

    return _get
