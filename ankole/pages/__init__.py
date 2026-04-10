"""
Page Object Model (POM) classes.

Subpackages:
    web/       — Playwright-based web page objects
    desktop/   — pywinauto-based desktop page objects
"""

from ankole.pages.base_page import BasePage

__all__ = ["BasePage"]
