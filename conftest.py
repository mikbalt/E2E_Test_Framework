# conftest.py - Root conftest for this repository's own sample tests.
#
# Intentionally minimal: all hooks and fixtures live in
# sphere_e2e_test_framework.plugin, auto-registered via the pytest11 entry point.
# This file exists so IDEs discover the project as a pytest root and to
# prevent "no conftest.py found" warnings.
#
# Consumer repos do NOT need to copy this file. They only need:
#   pip install git+<gitlab-url>/sphere-e2e-test-framework.git
#   + their own config/settings.yaml
#   + their own tests/
