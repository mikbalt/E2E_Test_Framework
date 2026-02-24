"""
PKCS#11 Go Tests — Python wrappers for Go compiled binaries.

The Go source code is compiled by build.sh (go build) before tests run.
Python wraps the resulting binary, captures output, and validates.

Test types:
- pkcs11_go_slot : Slot management tool (built from Go source)

Usage:
    pytest tests/console/test_pkcs11_go.py -v
    pytest -m go_test -v
"""

import os

import allure
import pytest

from hsm_test_framework import ConsoleRunner, LogCollector, resolve_platform_config


@allure.epic("PKCS#11")
@allure.feature("Go Tests")
@pytest.mark.console
@pytest.mark.pkcs11
@pytest.mark.go_test
@pytest.mark.needs_build
class TestPKCS11GoSlot:
    """
    PKCS#11 Slot Management — Go binary (built from source).

    Wraps: bin/pkcs11-slot.exe (Windows) / bin/pkcs11-slot (Linux)
    Source: src/go/slot/ (built via 'go build' by build.sh)
    Logs: logs/go_slot.log
    """

    def _tool(self, config):
        return resolve_platform_config(config["console_tools"]["pkcs11_go_slot"])

    @allure.story("List Slots")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.smoke
    def test_list_slots(self, config, console, evidence, log_collector):
        """Test listing PKCS#11 slots via Go tool."""
        tool = self._tool(config)

        if not os.path.exists(tool["command"]):
            pytest.skip(f"Binary not found: {tool['command']} (run build.sh first)")

        with log_collector.monitor(tool.get("log_path", "")) as log_mon:
            evidence.step("Run Go PKCS#11 list slots")
            result = console.run_go(
                binary_path=tool["command"],
                args=["list-slots"],
                timeout=tool.get("timeout", 60),
            )

        evidence.attach_text(result.output, "go_list_slots_stdout")
        if log_mon.captured:
            log_collector.collect_text(log_mon.captured, "go_slot_runtime_log")
        log_collector.collect_from_config(tool)

        evidence.step("Validate Go slot listing")
        result.assert_success()
        result.assert_output_contains("slot", case_sensitive=False)

    @allure.story("Slot Info")
    @allure.severity(allure.severity_level.NORMAL)
    def test_slot_info(self, config, console, evidence, log_collector):
        """Test getting detailed slot information via Go tool."""
        tool = self._tool(config)

        if not os.path.exists(tool["command"]):
            pytest.skip(f"Binary not found: {tool['command']}")

        evidence.step("Run Go PKCS#11 slot info")
        result = console.run_go(
            binary_path=tool["command"],
            args=["slot-info", "--slot", "0"],
            timeout=tool.get("timeout", 60),
        )

        evidence.attach_text(result.output, "go_slot_info_stdout")
        log_collector.collect_from_config(tool)

        evidence.step("Validate slot info output")
        result.assert_success()

    @allure.story("Mechanism List")
    @allure.severity(allure.severity_level.NORMAL)
    def test_mechanism_list(self, config, console, evidence, log_collector):
        """Test listing supported mechanisms via Go tool."""
        tool = self._tool(config)

        if not os.path.exists(tool["command"]):
            pytest.skip(f"Binary not found: {tool['command']}")

        evidence.step("Run Go PKCS#11 mechanism list")
        result = console.run_go(
            binary_path=tool["command"],
            args=["mechanisms", "--slot", "0"],
            timeout=tool.get("timeout", 60),
        )

        evidence.attach_text(result.output, "go_mechanisms_stdout")
        log_collector.collect_from_config(tool)

        evidence.step("Validate mechanism listing")
        result.assert_success()

    @allure.story("Health Check")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_health_check(self, config, console, evidence, log_collector):
        """Test PKCS#11 library health check via Go tool."""
        tool = self._tool(config)

        if not os.path.exists(tool["command"]):
            pytest.skip(f"Binary not found: {tool['command']}")

        evidence.step("Run Go PKCS#11 health check")
        result = console.run_go(
            binary_path=tool["command"],
            args=["health"],
            timeout=tool.get("timeout", 60),
        )

        evidence.attach_text(result.output, "go_health_stdout")
        log_collector.collect_from_config(tool)

        evidence.step("Validate health check result")
        result.assert_success()
        result.assert_output_not_contains("error", case_sensitive=False)
