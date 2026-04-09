"""Phase 2 verification: Config flexibility (data-driven env overrides).

Tests the new _set_nested, _apply_env_overrides with env_overrides section,
and type casting logic.
"""

import os
from copy import deepcopy
from unittest.mock import patch

import pytest

from ankole.plugin.config import (
    _set_nested,
    _apply_env_overrides,
    _resolve_placeholders,
    _parse_field_spec,
    _check_condition,
    _TYPE_CASTERS,
)


class TestSetNested:
    """Verify _set_nested creates intermediate dicts correctly."""

    def test_single_level(self):
        cfg = {}
        _set_nested(cfg, "key", "value")
        assert cfg == {"key": "value"}

    def test_two_levels(self):
        cfg = {}
        _set_nested(cfg, "a.b", "value")
        assert cfg == {"a": {"b": "value"}}

    def test_deep_nesting(self):
        cfg = {}
        _set_nested(cfg, "apps.workspace.connection.ip", "10.0.0.1")
        assert cfg["apps"]["workspace"]["connection"]["ip"] == "10.0.0.1"

    def test_preserves_existing_keys(self):
        cfg = {"apps": {"workspace": {"path": "app.exe"}}}
        _set_nested(cfg, "apps.workspace.connection.ip", "10.0.0.1")
        assert cfg["apps"]["workspace"]["path"] == "app.exe"
        assert cfg["apps"]["workspace"]["connection"]["ip"] == "10.0.0.1"

    def test_overwrites_existing_value(self):
        cfg = {"apps": {"workspace": {"connection": {"ip": "old"}}}}
        _set_nested(cfg, "apps.workspace.connection.ip", "new")
        assert cfg["apps"]["workspace"]["connection"]["ip"] == "new"


class TestTypeCasters:
    """Verify type casting helpers."""

    def test_int_caster(self):
        assert _TYPE_CASTERS["int"]("42") == 42
        assert _TYPE_CASTERS["int"]("0") == 0

    def test_bool_caster_true(self):
        for val in ("1", "true", "True", "TRUE", "yes", "Yes", "YES"):
            assert _TYPE_CASTERS["bool"](val) is True, f"Expected True for '{val}'"

    def test_bool_caster_false(self):
        for val in ("0", "false", "no", "nope", ""):
            assert _TYPE_CASTERS["bool"](val) is False, f"Expected False for '{val}'"


class TestApplyEnvOverrides:
    """Verify data-driven env override application."""

    def test_env_overrides_applied(self):
        """env_overrides section should set values at dotted paths."""
        cfg = {
            "env_overrides": {
                "TEST_IP": "apps.workspace.connection.ip",
                "TEST_PORT": "apps.workspace.connection.port",
            },
        }
        with patch.dict(os.environ, {"TEST_IP": "1.2.3.4", "TEST_PORT": "9999"}):
            _apply_env_overrides(cfg)

        assert cfg["apps"]["workspace"]["connection"]["ip"] == "1.2.3.4"
        assert cfg["apps"]["workspace"]["connection"]["port"] == "9999"

    def test_env_overrides_with_int_type(self):
        """Type hint ':int' should cast value to integer."""
        cfg = {
            "env_overrides": {
                "TEST_PLAN_ID": "kiwi_tcms.plan_id:int",
            },
        }
        with patch.dict(os.environ, {"TEST_PLAN_ID": "123"}):
            _apply_env_overrides(cfg)

        assert cfg["kiwi_tcms"]["plan_id"] == 123
        assert isinstance(cfg["kiwi_tcms"]["plan_id"], int)

    def test_env_overrides_with_bool_type(self):
        """Type hint ':bool' should cast value to boolean."""
        cfg = {
            "env_overrides": {
                "TEST_ENABLED": "feature.enabled:bool",
            },
        }
        with patch.dict(os.environ, {"TEST_ENABLED": "true"}):
            _apply_env_overrides(cfg)

        assert cfg["feature"]["enabled"] is True

    def test_empty_env_var_skipped(self):
        """Empty or unset env vars should not create entries."""
        cfg = {
            "env_overrides": {
                "UNSET_VAR": "should.not.exist",
            },
        }
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("UNSET_VAR", None)
            _apply_env_overrides(cfg)

        assert "should" not in cfg

    def test_env_overrides_section_removed(self):
        """env_overrides section should be consumed (popped) from config."""
        cfg = {
            "env_overrides": {"X": "a.b"},
            "other": "kept",
        }
        with patch.dict(os.environ, {"X": "val"}):
            _apply_env_overrides(cfg)

        assert "env_overrides" not in cfg
        assert cfg["other"] == "kept"

    def test_health_check_list_traversal(self):
        """env_overrides_list should apply env vars to list items."""
        cfg = {
            "env_overrides_list": {
                "health_check.checks": {
                    "HSM_IP": "host",
                    "HSM_PORT": "port:int?type=tcp",
                },
            },
            "health_check": {
                "checks": [
                    {"type": "ping", "host": "old", "timeout": 5},
                    {"type": "tcp", "host": "old", "port": 1111, "timeout": 5},
                ],
            },
        }
        with patch.dict(os.environ, {"HSM_IP": "10.0.0.1", "HSM_PORT": "8080"}):
            _apply_env_overrides(cfg)

        assert cfg["health_check"]["checks"][0]["host"] == "10.0.0.1"
        assert cfg["health_check"]["checks"][1]["host"] == "10.0.0.1"
        assert cfg["health_check"]["checks"][1]["port"] == 8080
        # ping check should NOT get port (condition: type=tcp)
        assert "port" not in cfg["health_check"]["checks"][0]

    def test_no_env_overrides_section(self):
        """Config without env_overrides should still work (backward compat)."""
        cfg = {"apps": {"workspace": {"path": "app.exe"}}}
        _apply_env_overrides(cfg)  # should not raise
        assert cfg["apps"]["workspace"]["path"] == "app.exe"


class TestResolvePlaceholders:
    """Verify ${VAR} placeholder resolution."""

    def test_simple_placeholder(self):
        with patch.dict(os.environ, {"MY_VAR": "hello"}):
            result = _resolve_placeholders("${MY_VAR}")
        assert result == "hello"

    def test_unset_placeholder_resolves_empty(self):
        os.environ.pop("NONEXISTENT_VAR_XYZ", None)
        result = _resolve_placeholders("${NONEXISTENT_VAR_XYZ}")
        assert result == ""

    def test_nested_dict_resolution(self):
        with patch.dict(os.environ, {"A": "1", "B": "2"}):
            result = _resolve_placeholders({"x": "${A}", "y": {"z": "${B}"}})
        assert result == {"x": "1", "y": {"z": "2"}}

    def test_list_resolution(self):
        with patch.dict(os.environ, {"V": "val"}):
            result = _resolve_placeholders(["${V}", "literal"])
        assert result == ["val", "literal"]

    def test_non_string_passthrough(self):
        assert _resolve_placeholders(42) == 42
        assert _resolve_placeholders(True) is True
        assert _resolve_placeholders(None) is None
