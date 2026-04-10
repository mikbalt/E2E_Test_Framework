"""Desktop test sample: Windows Calculator automation with pywinauto.

Demonstrates the UIDriver with the Windows Calculator app.
Only runs on Windows platforms.
"""

import platform

import pytest


@pytest.mark.desktop
@pytest.mark.skipif(
    platform.system() != "Windows",
    reason="Desktop tests require Windows",
)
class TestCalculatorSample:
    """Sample pywinauto test using Windows Calculator."""

    def test_calculator_opens(self, calculator):
        """Calculator should launch and display main window."""
        assert calculator.main_window is not None
        calculator.take_screenshot("calculator_opened")

    def test_calculator_basic_addition(self, calculator):
        """Calculator should perform basic addition: 7 + 3 = 10."""
        calculator.click_button(name="Seven")
        calculator.click_button(name="Plus")
        calculator.click_button(name="Three")
        calculator.click_button(name="Equals")
        calculator.take_screenshot("addition_result")
