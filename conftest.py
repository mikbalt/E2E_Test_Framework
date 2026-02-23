# conftest.py - Root conftest for this repository's own sample tests.
#
# The heavy lifting (hooks, fixtures, TCMS, Grafana) is handled by the
# hsm_test_framework.plugin module, which is auto-registered via pytest11.
#
# Consumer repos do NOT need to copy this file. They only need:
#   pip install git+<gitlab-url>/hsm-test-framework.git
#   + their own config/settings.yaml
#   + their own tests/
