"""Phase 1 verification: Plugin decomposition.

Ensures the plugin/ package re-exports everything correctly and
the pytest11 entry point resolves to the new package structure.
"""

import importlib
import types

import pytest


class TestPluginImports:
    """Verify all public symbols are importable from the plugin package."""

    def test_load_config_from_package(self):
        from ankole.plugin import load_config
        assert callable(load_config)

    def test_load_config_from_config_module(self):
        from ankole.plugin.config import load_config
        assert callable(load_config)

    def test_hooks_importable(self):
        from ankole.plugin import (
            pytest_addoption,
            pytest_configure,
            pytest_collection_modifyitems,
            pytest_sessionstart,
            pytest_runtest_setup,
            pytest_runtest_makereport,
            pytest_sessionfinish,
        )
        # All should be callable functions
        for fn in [
            pytest_addoption, pytest_configure,
            pytest_collection_modifyitems, pytest_sessionstart,
            pytest_runtest_setup, pytest_runtest_makereport,
            pytest_sessionfinish,
        ]:
            assert callable(fn), f"{fn} is not callable"

    def test_fixtures_importable(self):
        from ankole.plugin import (
            config, evidence, console, log_collector, ui_app,
        )
        # pytest fixtures are function objects
        for fix in [config, evidence, console, log_collector, ui_app]:
            assert callable(fix), f"{fix} is not callable"

    def test_plugin_is_package(self):
        """Ensure plugin is a package (directory with __init__.py), not a module."""
        import ankole.plugin as plugin
        assert hasattr(plugin, "__path__"), "plugin should be a package, not a .py file"

    def test_submodules_exist(self):
        """All expected submodules should be importable."""
        submodules = [
            "ankole.plugin.config",
            "ankole.plugin.hooks",
            "ankole.plugin.fixtures",
            "ankole.plugin.kiwi_hooks",
            "ankole.plugin.metrics",
        ]
        for mod_name in submodules:
            mod = importlib.import_module(mod_name)
            assert isinstance(mod, types.ModuleType), f"{mod_name} failed to import"

    def test_pytest11_entry_point_resolves(self):
        """The entry point 'ankole.plugin' should resolve
        to the package __init__.py, not raise ImportError."""
        mod = importlib.import_module("ankole.plugin")
        # Should have the hooks re-exported
        assert hasattr(mod, "pytest_addoption")
        assert hasattr(mod, "load_config")

    def test_wildcard_import_compat(self):
        """Consumer repos use 'from ankole.plugin import *'."""
        mod = importlib.import_module("ankole.plugin")
        # __init__.py uses explicit imports, so dir() should contain all symbols
        public = [name for name in dir(mod) if not name.startswith("_")]
        assert "load_config" in public
        assert "pytest_addoption" in public
        assert "config" in public  # fixture
