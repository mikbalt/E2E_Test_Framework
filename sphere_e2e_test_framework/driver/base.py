"""Driver protocol — defines the interface any UI driver must satisfy.

Consumers can type-hint against ``DriverProtocol`` without depending on
pywinauto or any concrete driver implementation::

    from sphere_e2e_test_framework.driver.base import DriverProtocol

    def my_helper(driver: DriverProtocol) -> None:
        driver.click_button(auto_id="btnOK")
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class DriverProtocol(Protocol):
    """Structural (duck-typed) interface for UI automation drivers.

    ``UIDriver`` already satisfies this protocol without modification.
    Custom drivers (Playwright, mock, etc.) can implement it as well.

    The protocol covers all methods used by page objects and test code.
    Methods are grouped by category for readability.
    """

    # -- Properties -----------------------------------------------------------

    @property
    def main_window(self) -> Any: ...

    @property
    def app(self) -> Any: ...

    # -- Lifecycle ------------------------------------------------------------

    def start(self) -> DriverProtocol: ...

    def close(self) -> None: ...

    def refresh_window(self) -> Any: ...

    def set_retry_config(self, config: dict) -> None: ...

    def set_window_monitor(self, monitor: Any) -> None: ...

    # -- Click actions --------------------------------------------------------

    def click_button(self, name: str | None = None, auto_id: str | None = None,
                     found_index: int = 0) -> None: ...

    def click_radio(self, auto_id: str | None = None, name: str | None = None,
                    found_index: int = 0) -> None: ...

    def click_element(self, **kwargs: Any) -> None: ...

    # -- Text input -----------------------------------------------------------

    def type_text(self, text: str, auto_id: str | None = None,
                  name: str | None = None, **kwargs: Any) -> None: ...

    def type_keys_to_field(self, text: str, auto_id: str | None = None,
                           name: str | None = None, **kwargs: Any) -> None: ...

    # -- Text retrieval -------------------------------------------------------

    def get_text(self, auto_id: str | None = None,
                 name: str | None = None, **kwargs: Any) -> str: ...

    # -- Waits & queries ------------------------------------------------------

    def wait_for_element(self, timeout: int = 10, **kwargs: Any) -> Any: ...

    def element_exists(self, **kwargs: Any) -> bool: ...

    # -- Combobox / List / Table ----------------------------------------------

    def select_combobox(self, name: str | None = None, auto_id: str | None = None,
                        value: str | None = None) -> None: ...

    def click_combobox_item(self, auto_id: str | None = None, name: str | None = None,
                            value: str | None = None) -> list[str]: ...

    def get_combobox_items(self, auto_id: str | None = None,
                           name: str | None = None) -> list[str]: ...

    def get_list_items(self, auto_id: str | None = None,
                       name: str | None = None) -> list[str]: ...

    def get_table_data(self, auto_id: str | None = None,
                       name: str | None = None) -> dict: ...

    # -- Popups ---------------------------------------------------------------

    def check_popup(self) -> Any: ...

    def dismiss_popup(self, button_name: str | None = None,
                      auto_id: str | None = None) -> bool: ...

    def dismiss_startup_popups(self) -> bool: ...

    # -- Screenshots & debugging ----------------------------------------------

    def take_screenshot(self, name: str = "screenshot") -> Any: ...

    def print_control_tree(self, depth: int = 3) -> None: ...
