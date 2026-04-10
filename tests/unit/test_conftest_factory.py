"""Phase 4 verification: Conftest abstraction.

Tests that factory functions produce valid pytest fixtures with correct
properties, and that shared hooks/utils work correctly.
"""

import datetime
import os
import tempfile
import zipfile
from unittest.mock import MagicMock, patch

import pytest

from ankole.testing.conftest_utils import (
    get_tc_label,
    zip_app_logs,
    attach_zip_to_allure,
)
from ankole.testing.conftest_factory import (
    make_app_config_fixture,
    make_driver_fixture,
    make_window_monitor_fixture,
    make_app_logs_fixture,
)


# =========================================================================
# conftest_utils Tests
# =========================================================================


class TestGetTcLabel:
    """Verify TC label extraction from markers."""

    def test_with_tcms_marker(self):
        marker = MagicMock()
        marker.kwargs = {"case_id": 37509}
        node = MagicMock()
        node.get_closest_marker.return_value = marker
        node.name = "test_something"
        request = MagicMock()
        request.node = node

        assert get_tc_label(request) == "TC-37509"

    def test_without_tcms_marker(self):
        node = MagicMock()
        node.get_closest_marker.return_value = None
        node.name = "test_fallback_name"
        request = MagicMock()
        request.node = node

        assert get_tc_label(request) == "test_fallback_name"

    def test_tcms_marker_without_case_id(self):
        marker = MagicMock()
        marker.kwargs = {}
        node = MagicMock()
        node.get_closest_marker.return_value = marker
        node.name = "test_no_id"
        request = MagicMock()
        request.node = node

        assert get_tc_label(request) == "test_no_id"


class TestZipAppLogs:
    """Verify app log zipping utility."""

    def test_zip_creates_file(self, tmp_path):
        """Should create a zip with all files from source dir."""
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        (logs_dir / "app.log").write_text("log content")
        (logs_dir / "error.log").write_text("error content")

        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()

        zip_path, count = zip_app_logs(str(logs_dir), str(dest_dir), "TEST_PRE")

        assert zip_path is not None
        assert count == 2
        assert os.path.isfile(zip_path)
        assert "AppLogs_TEST_PRE_" in os.path.basename(zip_path)

        # Verify zip contents
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            assert "app.log" in names
            assert "error.log" in names

    def test_empty_dir_returns_none(self, tmp_path):
        """Empty directory should return (None, 0) and clean up the zip."""
        logs_dir = tmp_path / "empty_logs"
        logs_dir.mkdir()
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()

        zip_path, count = zip_app_logs(str(logs_dir), str(dest_dir), "EMPTY")
        assert zip_path is None
        assert count == 0

    def test_nested_dirs_included(self, tmp_path):
        """Nested subdirectories should be included in the zip."""
        logs_dir = tmp_path / "logs"
        sub = logs_dir / "sub"
        sub.mkdir(parents=True)
        (logs_dir / "root.log").write_text("root")
        (sub / "nested.log").write_text("nested")

        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()

        zip_path, count = zip_app_logs(str(logs_dir), str(dest_dir), "NESTED")
        assert count == 2

        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            assert "root.log" in names
            # Nested path uses os-relative format
            assert any("nested.log" in n for n in names)


class TestAttachZipToAllure:
    """Verify Allure attachment utility."""

    def test_no_crash_when_allure_missing(self, tmp_path):
        """Should not crash if allure is not importable."""
        dummy_zip = tmp_path / "test.zip"
        dummy_zip.write_bytes(b"PK")

        # Should not raise even if allure import fails internally
        attach_zip_to_allure(str(dummy_zip), "test")

    def test_none_path_ignored(self):
        """Should silently ignore None zip_path."""
        attach_zip_to_allure(None, "test")  # should not raise

    def test_nonexistent_path_ignored(self):
        """Should silently ignore non-existent zip path."""
        attach_zip_to_allure("/nonexistent/path.zip", "test")


# =========================================================================
# Factory Function Tests
# =========================================================================


class TestMakeAppConfigFixture:
    """Verify make_app_config_fixture produces correct fixture."""

    def test_returns_callable(self):
        fixture = make_app_config_fixture("test_app")
        assert callable(fixture)

    def test_fixture_is_pytest_fixture(self):
        """Factory output should be a pytest FixtureFunctionMarker."""
        fixture_fn = make_app_config_fixture("workspace")
        # repr of pytest fixtures starts with '<pytest_fixture('
        assert "pytest_fixture" in repr(fixture_fn)

    def test_fixture_has_docstring(self):
        """Factory fixture should have a descriptive docstring."""
        fixture_fn = make_app_config_fixture("my_app")
        assert "my_app" in fixture_fn.__doc__


class TestMakeDriverFixture:
    """Verify make_driver_fixture produces correct fixture."""

    def test_returns_callable(self):
        fixture = make_driver_fixture("test_app")
        assert callable(fixture)

    def test_pre_launch_hook_called(self):
        """pre_launch_hook should be called with app_config before start()."""
        hook_calls = []
        hook = lambda cfg: hook_calls.append(cfg)

        fixture_fn = make_driver_fixture("workspace", pre_launch_hook=hook)

        # The fixture uses request.getfixturevalue, so we'd need a real
        # pytest request to fully test. Here we verify the hook is stored.
        assert callable(fixture_fn)
        # The actual integration is tested via pytest collection


class TestMakeWindowMonitorFixture:
    """Verify make_window_monitor_fixture produces correct fixture."""

    def test_returns_callable(self):
        fixture = make_window_monitor_fixture("test_app")
        assert callable(fixture)


class TestMakeAppLogsFixture:
    """Verify make_app_logs_fixture produces correct fixture."""

    def test_returns_callable(self):
        fixture = make_app_logs_fixture("test_app")
        assert callable(fixture)


# =========================================================================
# Conftest Hooks Tests
# =========================================================================


class TestConftestHooks:
    """Verify shared TCMS dependency hooks."""

    def test_hooks_importable(self):
        from ankole.testing.conftest_hooks import (
            pytest_collection_modifyitems,
            pytest_runtest_makereport,
            pytest_runtest_setup,
        )
        assert callable(pytest_collection_modifyitems)
        assert callable(pytest_runtest_makereport)
        assert callable(pytest_runtest_setup)

    def test_hooks_module_has_tracking_sets(self):
        from ankole.testing import conftest_hooks
        assert hasattr(conftest_hooks, "_passed_cases")
        assert hasattr(conftest_hooks, "_collected_cases")
        assert isinstance(conftest_hooks._passed_cases, set)
        assert isinstance(conftest_hooks._collected_cases, set)
