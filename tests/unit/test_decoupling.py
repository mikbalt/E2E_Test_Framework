"""Verification tests for framework decoupling (cross-project reuse).

Tests:
- DriverProtocol — UIDriver satisfies it structurally
- WebDriverProtocol / APIDriverProtocol — new protocols exist
- Package exports — __all__ only has generic classes
- Metrics — prefix parameterization
- env_overrides_list — list traversal with conditions
"""

import os
from unittest.mock import patch

import pytest

from ankole.plugin.config import (
    _apply_env_overrides,
    _parse_field_spec,
    _check_condition,
)


# ===================================================================
# Phase 1: DriverProtocol
# ===================================================================

class TestDriverProtocol:
    """Verify DriverProtocol is a valid runtime-checkable protocol."""

    def test_protocol_importable(self):
        from ankole.driver.base import DriverProtocol
        assert hasattr(DriverProtocol, '__protocol_attrs__') or hasattr(DriverProtocol, '_is_protocol')

    def test_uidriver_satisfies_protocol(self):
        """UIDriver should be recognized as implementing DriverProtocol."""
        from ankole.driver.base import DriverProtocol
        from ankole.driver.ui_driver import UIDriver
        protocol_methods = [
            "start", "close", "click_button", "type_text", "get_text",
            "wait_for_element", "element_exists", "take_screenshot",
            "set_retry_config", "set_window_monitor", "click_radio",
            "click_element", "type_keys_to_field", "refresh_window",
            "check_popup", "dismiss_popup", "dismiss_startup_popups",
            "select_combobox", "click_combobox_item", "get_combobox_items",
            "get_list_items", "get_table_data", "print_control_tree",
        ]
        for method in protocol_methods:
            assert hasattr(UIDriver, method), f"UIDriver missing protocol method: {method}"

    def test_protocol_available_via_top_level(self):
        """DriverProtocol should be importable from top-level package."""
        from ankole import DriverProtocol
        assert DriverProtocol is not None


# ===================================================================
# Phase 2: New protocols exist
# ===================================================================

class TestNewProtocols:
    """Verify WebDriverProtocol and APIDriverProtocol are importable."""

    def test_web_driver_protocol_importable(self):
        from ankole.driver.base import WebDriverProtocol
        assert WebDriverProtocol is not None

    def test_api_driver_protocol_importable(self):
        from ankole.driver.base import APIDriverProtocol
        assert APIDriverProtocol is not None

    def test_web_driver_importable(self):
        from ankole.driver.web_driver import WebDriver
        assert WebDriver is not None

    def test_api_driver_importable(self):
        from ankole.driver.api_driver import APIDriver
        assert APIDriver is not None


# ===================================================================
# Phase 3: Package export cleanliness
# ===================================================================

class TestPackageExports:
    """Verify __all__ only exposes generic core."""

    def test_basepage_in_all(self):
        import ankole as fw
        assert "BasePage" in fw.__all__

    def test_driver_protocol_in_all(self):
        import ankole as fw
        assert "DriverProtocol" in fw.__all__

    def test_new_drivers_in_all(self):
        import ankole as fw
        assert "WebDriver" in fw.__all__
        assert "APIDriver" in fw.__all__
        assert "WebDriverProtocol" in fw.__all__
        assert "APIDriverProtocol" in fw.__all__

    def test_pages_init_only_exports_basepage(self):
        from ankole import pages
        assert "BasePage" in pages.__all__
        assert len(pages.__all__) == 1


# ===================================================================
# Phase 4: Metrics parameterization
# ===================================================================

class TestMetricsPrefix:
    """Verify MetricsPusher supports configurable metric prefix."""

    def test_default_prefix_is_e2e(self):
        from ankole.driver.grafana_push import MetricsPusher
        import inspect
        sig = inspect.signature(MetricsPusher.__init__)
        assert sig.parameters["metric_prefix"].default == "e2e"

    def test_default_job_name_is_e2e_tests(self):
        from ankole.driver.grafana_push import MetricsPusher
        import inspect
        sig = inspect.signature(MetricsPusher.__init__)
        assert sig.parameters["job_name"].default == "e2e_tests"


# ===================================================================
# Phase 5: Config list overrides
# ===================================================================

class TestParseFieldSpec:
    """Verify _parse_field_spec parsing logic."""

    def test_simple_field(self):
        name, type_hint, condition = _parse_field_spec("host")
        assert name == "host"
        assert type_hint is None
        assert condition is None

    def test_field_with_type(self):
        name, type_hint, condition = _parse_field_spec("port:int")
        assert name == "port"
        assert type_hint == "int"
        assert condition is None

    def test_field_with_type_and_condition(self):
        name, type_hint, condition = _parse_field_spec("port:int?type=tcp")
        assert name == "port"
        assert type_hint == "int"
        assert condition == {"type": "tcp"}

    def test_field_with_multiple_conditions(self):
        name, type_hint, condition = _parse_field_spec("host?type=ping&label=test")
        assert name == "host"
        assert type_hint is None
        assert condition == {"type": "ping", "label": "test"}


class TestCheckCondition:
    """Verify _check_condition matching."""

    def test_match(self):
        assert _check_condition({"type": "tcp", "host": "x"}, {"type": "tcp"})

    def test_no_match(self):
        assert not _check_condition({"type": "ping"}, {"type": "tcp"})

    def test_missing_key(self):
        assert not _check_condition({}, {"type": "tcp"})


class TestEnvOverridesList:
    """Verify env_overrides_list mechanism end-to-end."""

    def test_list_override_unconditional(self):
        cfg = {
            "env_overrides_list": {
                "health_check.checks": {
                    "MY_HOST": "host",
                },
            },
            "health_check": {
                "checks": [
                    {"type": "ping", "host": "old1"},
                    {"type": "tcp", "host": "old2"},
                ],
            },
        }
        with patch.dict(os.environ, {"MY_HOST": "new_host"}):
            _apply_env_overrides(cfg)

        assert cfg["health_check"]["checks"][0]["host"] == "new_host"
        assert cfg["health_check"]["checks"][1]["host"] == "new_host"

    def test_list_override_with_condition(self):
        cfg = {
            "env_overrides_list": {
                "health_check.checks": {
                    "MY_PORT": "port:int?type=tcp",
                },
            },
            "health_check": {
                "checks": [
                    {"type": "ping", "host": "x"},
                    {"type": "tcp", "host": "x", "port": 0},
                ],
            },
        }
        with patch.dict(os.environ, {"MY_PORT": "9999"}):
            _apply_env_overrides(cfg)

        assert "port" not in cfg["health_check"]["checks"][0]
        assert cfg["health_check"]["checks"][1]["port"] == 9999

    def test_empty_env_var_skipped(self):
        cfg = {
            "env_overrides_list": {
                "items": {"UNSET": "field"},
            },
            "items": [{"field": "original"}],
        }
        os.environ.pop("UNSET", None)
        _apply_env_overrides(cfg)
        assert cfg["items"][0]["field"] == "original"

    def test_missing_list_path_ignored(self):
        cfg = {
            "env_overrides_list": {
                "nonexistent.path": {"MY_VAR": "field"},
            },
        }
        with patch.dict(os.environ, {"MY_VAR": "value"}):
            _apply_env_overrides(cfg)

    def test_section_consumed(self):
        cfg = {
            "env_overrides_list": {"items": {"X": "f"}},
            "items": [{"f": "old"}],
        }
        with patch.dict(os.environ, {"X": "new"}):
            _apply_env_overrides(cfg)
        assert "env_overrides_list" not in cfg
