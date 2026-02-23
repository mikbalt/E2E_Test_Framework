# conftest.py
#
# No code needed here! The hsm_test_framework.plugin is auto-registered
# via the pytest11 entry point when you install the package.
#
# You automatically get these fixtures:
#   - config     (loads config/settings.yaml)
#   - evidence   (per-test evidence collector)
#   - console    (ConsoleRunner instance)
#   - ui_app     (UIDriver with auto-skip on Linux)
#
# And these hooks:
#   - Auto-skip @pytest.mark.ui on non-Windows
#   - Screenshot on failure
#   - Kiwi TCMS reporting (if enabled in settings.yaml)
#   - Grafana metrics push (if enabled in settings.yaml)
#
# Add repo-specific fixtures below if needed:
