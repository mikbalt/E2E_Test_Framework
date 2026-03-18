"""Verification tests for framework decoupling (cross-project reuse).

Tests:
- DriverProtocol — UIDriver satisfies it structurally
- EAdminBasePage — correct inheritance chain
- env_overrides_list — list traversal with conditions
- Package exports — __all__ only has generic classes
- Metrics — prefix parameterization
"""

import os
from copy import deepcopy
from unittest.mock import patch

import pytest

from sphere_e2e_test_framework.plugin.config import (
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
        from sphere_e2e_test_framework.driver.base import DriverProtocol
        assert hasattr(DriverProtocol, '__protocol_attrs__') or hasattr(DriverProtocol, '_is_protocol')

    def test_uidriver_satisfies_protocol(self):
        """UIDriver should be recognized as implementing DriverProtocol."""
        from sphere_e2e_test_framework.driver.base import DriverProtocol
        from sphere_e2e_test_framework.driver.ui_driver import UIDriver
        # Use isinstance with a dummy instance check — issubclass() does not
        # work with Protocols that have non-method members (properties) in
        # Python < 3.12.  Verify structurally instead.
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
        from sphere_e2e_test_framework import DriverProtocol
        assert DriverProtocol is not None


# ===================================================================
# Phase 2: EAdminBasePage inheritance
# ===================================================================

class TestEAdminBasePage:
    """Verify EAdminBasePage splits E-Admin nav from generic BasePage."""

    def test_eadmin_base_inherits_basepage(self):
        from sphere_e2e_test_framework.pages.base_page import BasePage
        from sphere_e2e_test_framework.pages.e_admin.e_admin_base_page import EAdminBasePage
        assert issubclass(EAdminBasePage, BasePage)

    def test_basepage_has_no_eadmin_methods(self):
        from sphere_e2e_test_framework.pages.base_page import BasePage
        assert not hasattr(BasePage, 'agree_and_next')
        assert not hasattr(BasePage, 'goto_user_management')
        assert not hasattr(BasePage, 'goto_profile_management')
        assert not hasattr(BasePage, 'logout')

    def test_eadmin_base_has_eadmin_methods(self):
        from sphere_e2e_test_framework.pages.e_admin.e_admin_base_page import EAdminBasePage
        assert hasattr(EAdminBasePage, 'agree_and_next')
        assert hasattr(EAdminBasePage, 'goto_user_management')
        assert hasattr(EAdminBasePage, 'goto_profile_management')
        assert hasattr(EAdminBasePage, 'logout')

    def test_basepage_keeps_generic_methods(self):
        from sphere_e2e_test_framework.pages.base_page import BasePage
        assert hasattr(BasePage, '_step')
        assert hasattr(BasePage, 'dismiss_ok')
        assert hasattr(BasePage, 'dismiss_ok_with_message')

    def test_all_eadmin_pages_inherit_eadmin_base(self):
        from sphere_e2e_test_framework.pages.e_admin.e_admin_base_page import EAdminBasePage
        from sphere_e2e_test_framework.pages.e_admin import (
            LoginPage, DashboardPage, TermsPage, PasswordChangePage,
            UserCreationPage, KCLoginPage, CCMKImportPage, KeyCeremonyFlow,
            ProfileManagementPage, UserManagementPage,
        )
        for cls in [LoginPage, DashboardPage, TermsPage, PasswordChangePage,
                    UserCreationPage, KCLoginPage, CCMKImportPage, KeyCeremonyFlow,
                    ProfileManagementPage, UserManagementPage]:
            assert issubclass(cls, EAdminBasePage), f"{cls.__name__} should inherit EAdminBasePage"

    def test_eadmin_base_exported_from_package(self):
        from sphere_e2e_test_framework.pages.e_admin import EAdminBasePage
        assert EAdminBasePage is not None


# ===================================================================
# Phase 3: Package export cleanliness
# ===================================================================

class TestPackageExports:
    """Verify __all__ only exposes generic core, not E-Admin pages."""

    def test_basepage_in_all(self):
        import sphere_e2e_test_framework as fw
        assert "BasePage" in fw.__all__

    def test_driver_protocol_in_all(self):
        import sphere_e2e_test_framework as fw
        assert "DriverProtocol" in fw.__all__

    def test_eadmin_pages_not_in_all(self):
        import sphere_e2e_test_framework as fw
        eadmin_names = [
            "LoginPage", "DashboardPage", "TermsPage",
            "PasswordChangePage", "UserCreationPage", "KCLoginPage",
            "CCMKImportPage", "KeyCeremonyFlow", "ProfileManagementPage",
            "UserManagementPage", "EAdminBasePage",
        ]
        for name in eadmin_names:
            assert name not in fw.__all__, f"{name} should not be in __all__"

    def test_backward_compat_import_still_works(self):
        """E-Admin pages should still be importable from top-level (compat)."""
        from sphere_e2e_test_framework import LoginPage
        assert LoginPage is not None

    def test_pages_init_only_exports_basepage(self):
        from sphere_e2e_test_framework import pages
        assert "BasePage" in pages.__all__
        assert len(pages.__all__) == 1

    def test_pages_lazy_import_compat(self):
        """E-Admin pages should be importable from pages package (compat)."""
        from sphere_e2e_test_framework.pages import LoginPage
        assert LoginPage is not None


# ===================================================================
# Phase 4: Metrics parameterization
# ===================================================================

class TestMetricsPrefix:
    """Verify MetricsPusher supports configurable metric prefix."""

    def test_default_prefix_is_e2e(self):
        """New consumers without config get generic 'e2e' prefix."""
        from sphere_e2e_test_framework.driver.grafana_push import MetricsPusher
        import inspect
        sig = inspect.signature(MetricsPusher.__init__)
        assert sig.parameters["metric_prefix"].default == "e2e"

    def test_default_job_name_is_e2e_tests(self):
        from sphere_e2e_test_framework.driver.grafana_push import MetricsPusher
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
        """All list items should get the override applied."""
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
        """Only items matching condition should get the override."""
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

        # ping item should NOT get port
        assert "port" not in cfg["health_check"]["checks"][0]
        # tcp item should get port as int
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
        """Non-existent list path should not raise."""
        cfg = {
            "env_overrides_list": {
                "nonexistent.path": {"MY_VAR": "field"},
            },
        }
        with patch.dict(os.environ, {"MY_VAR": "value"}):
            _apply_env_overrides(cfg)  # should not raise

    def test_section_consumed(self):
        """env_overrides_list should be popped from config."""
        cfg = {
            "env_overrides_list": {"items": {"X": "f"}},
            "items": [{"f": "old"}],
        }
        with patch.dict(os.environ, {"X": "new"}):
            _apply_env_overrides(cfg)
        assert "env_overrides_list" not in cfg
