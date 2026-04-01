"""
UI Driver - pywinauto wrapper for Windows desktop app automation.

Supports WPF (uia backend) and WinForms/Win32 (win32 backend).
Auto-detects if not specified.

Usage:
    driver = UIDriver("calc.exe", title="Calculator")
    driver.start()
    driver.click_button("Seven")
    driver.take_screenshot("after_click")
    driver.close()
"""

import logging
import os
import subprocess
import time

logger = logging.getLogger(__name__)


class UIDriver:
    """Wrapper around pywinauto for simplified Windows UI automation."""

    # Configurable timing defaults (seconds).
    # Override via set_timing() or pass timing_config dict to __init__.
    TIMING_AFTER_CLICK = 0.3       # Pause after click_button / click_radio / click_element
    TIMING_AFTER_POPUP_DISMISS = 0.5  # Pause after dismissing a popup
    TIMING_AFTER_COMBO_EXPAND = 0.5   # Pause after expanding a combobox dropdown
    TIMING_AFTER_CLOSE = 1.0       # Pause after requesting window close before kill
    TIMING_POLL_INTERVAL = 0.5     # Polling interval for find_element_in_any_window

    def __init__(self, app_path, title=None, class_name=None, backend="uia",
                 startup_wait=3, work_dir=None, popup_dismiss_buttons=None,
                 popup_dismiss_auto_ids=None, timing_config=None):
        """
        Args:
            app_path: Path to executable or just the exe name if in PATH.
            title: Window title pattern (supports regex).
            class_name: Window class name pattern (regex). Useful for apps
                        with empty titles, e.g. 'WindowsForms10\\.Window.*'
            backend: 'uia' for WPF/modern apps, 'win32' for classic WinForms.
            startup_wait: Seconds to wait after launching the app.
            work_dir: Working directory for the app. If None, auto-detected
                      from app_path parent directory.
            popup_dismiss_buttons: Button titles to try when auto-dismissing
                popups (e.g. ["OK", "Yes", "Close"]).
            popup_dismiss_auto_ids: Button automation IDs to try when
                auto-dismissing popups (e.g. ["2", "btnOKE"]).
        """
        self.app_path = app_path
        self.title = title
        self.class_name = class_name
        self.backend = backend
        self.startup_wait = startup_wait
        self.app = None
        self.main_window = None
        self._main_handle = None
        self._window_monitor = None
        self._retry_config = {}
        self._popup_dismiss_buttons = popup_dismiss_buttons or [
            "OK", "Yes", "Close",
        ]
        self._popup_dismiss_auto_ids = popup_dismiss_auto_ids or [
            "2", "btnOKE",
        ]
        # Auto-detect work_dir from app_path if not specified
        if work_dir:
            self.work_dir = work_dir
        elif app_path and os.path.isabs(app_path):
            self.work_dir = os.path.dirname(app_path)
        else:
            self.work_dir = None

        # Apply custom timing overrides
        if timing_config:
            self.set_timing(timing_config)

    def start(self):
        """Launch the application and connect to its main window."""
        from pywinauto import Application
        from pywinauto.application import AppNotConnected, ProcessNotFoundError
        from pywinauto.timings import TimeoutError as PywinautoTimeout

        logger.info(f"Starting application: {self.app_path} (backend={self.backend}, work_dir={self.work_dir})")

        try:
            self.app = Application(backend=self.backend).start(
                self.app_path, timeout=30, work_dir=self.work_dir
            )
        except (AppNotConnected, ProcessNotFoundError, PywinautoTimeout) as e:
            # Fallback: try launching via subprocess then connecting
            logger.warning(f"Direct start failed ({type(e).__name__}), trying subprocess + connect...")
            subprocess.Popen(self.app_path, shell=True, cwd=self.work_dir)
            time.sleep(self.startup_wait)
            connect_kwargs = {}
            if self.title:
                connect_kwargs["title_re"] = f".*{self.title}.*"
            if self.class_name:
                connect_kwargs["class_name_re"] = self.class_name
            self.app = Application(backend=self.backend).connect(
                **connect_kwargs,
                timeout=30,
            )

        time.sleep(self.startup_wait)
        self._find_main_window()
        logger.info(f"Connected to window: {self.main_window.window_text()}")
        return self

    def connect(self, pid=None, title=None):
        """Connect to an already running application."""
        from pywinauto import Application

        connect_args = {"backend": self.backend}
        if pid:
            connect_args["process"] = pid
        elif title:
            connect_args["title_re"] = f".*{title}.*"
        elif self.title:
            connect_args["title_re"] = f".*{self.title}.*"

        logger.info(f"Connecting to running app: {connect_args}")
        self.app = Application(**{k: v for k, v in connect_args.items()
                                  if k == "backend"}).connect(
            **{k: v for k, v in connect_args.items() if k != "backend"}
        )
        self._find_main_window()
        return self

    def _find_main_window(self):
        """Locate the main window of the application.

        Resolves by window handle (int) to avoid ElementAmbiguousError
        when multiple WinForms windows exist with the same class_name.
        Falls back to lazy WindowSpecification if handle enumeration fails.

        If the initial search times out, attempts to dismiss any blocking
        popup (e.g. 'Log File Signature Verification') and retries once.
        """
        from pywinauto.timings import TimeoutError as PywinautoTimeout

        try:
            self._resolve_main_window()
        except PywinautoTimeout:
            logger.warning("Main window not found (timeout), checking for blocking popups...")
            if self._dismiss_blocking_popup():
                logger.info("Blocking popup dismissed, retrying main window search")
                self._resolve_main_window()
            else:
                raise

    def _resolve_main_window(self):
        """Internal: locate and wait for the main window."""
        from pywinauto import findwindows

        find_kwargs = {"process": self.app.process, "backend": self.backend}
        if self.title:
            find_kwargs["title_re"] = f".*{self.title}.*"
        if self.class_name:
            find_kwargs["class_name_re"] = self.class_name

        handles = findwindows.find_windows(**find_kwargs)
        if handles:
            # Prefer the current handle if still valid — prevents
            # accidentally switching to a sibling window when the
            # Win32 enumeration order changes (e.g. after popup dismiss)
            if self._main_handle and self._main_handle in handles:
                target = self._main_handle
            else:
                target = handles[0]
            self.main_window = self.app.window(handle=target)
            self.main_window.wait("visible", timeout=15)
            self._main_handle = target
        else:
            # Fallback: original lazy spec behavior
            criteria = {}
            if self.title:
                criteria["title_re"] = f".*{self.title}.*"
            if self.class_name:
                criteria["class_name_re"] = self.class_name

            if criteria:
                self.main_window = self.app.window(**criteria)
            else:
                self.main_window = self.app.top_window()

            self.main_window.wait("visible", timeout=15)
            self._main_handle = self.main_window.handle

    def _dismiss_blocking_popup(self):
        """Dismiss a popup blocking the main window during startup.

        Uses Desktop search (same as dismiss_startup_popups) but does NOT
        call _find_main_window() afterward, to avoid recursion.
        """
        from pywinauto import Desktop

        desktop = Desktop(backend="uia")

        app_pid = None
        try:
            app_pid = self.app.process
        except Exception:
            return False

        for win in desktop.windows():
            try:
                if app_pid and win.process_id() != app_pid:
                    continue

                title = win.window_text()
                if not title:
                    continue

                for btn_title in self._popup_dismiss_buttons:
                    try:
                        btn = win.child_window(
                            title=btn_title, control_type="Button",
                        )
                        if btn.exists(timeout=0):
                            logger.warning(
                                f"Blocking popup dismissed: '{title}' "
                                f"with '{btn_title}'"
                            )
                            btn.click_input()
                            time.sleep(self.TIMING_AFTER_POPUP_DISMISS)
                            return True
                    except Exception:
                        continue

                for aid in self._popup_dismiss_auto_ids:
                    try:
                        btn = win.child_window(
                            auto_id=aid, control_type="Button",
                        )
                        if btn.exists(timeout=0):
                            logger.warning(
                                f"Blocking popup dismissed: '{title}' "
                                f"with auto_id='{aid}'"
                            )
                            btn.click_input()
                            time.sleep(self.TIMING_AFTER_POPUP_DISMISS)
                            return True
                    except Exception:
                        continue
            except Exception:
                continue

        return False

    def set_window_monitor(self, monitor):
        """Attach a WindowMonitor instance for pre-interaction guard checks."""
        self._window_monitor = monitor

    def _guard_check(self):
        """Check for unexpected windows before UI interaction."""
        unexpected = self._window_monitor.check_once()
        if unexpected:
            for hwnd, title, pid in unexpected:
                logger.warning(f"Unexpected window detected before interaction: '{title}' (PID={pid})")

    def _active_window(self):
        """Return the topmost active window (popup-aware).

        If a popup/dialog sits on top of main_window, return that instead.
        This allows click_button(), type_text(), wait_for_element(), etc.
        to work transparently on popups without callers needing to know.
        """
        if self._window_monitor:
            self._guard_check()
        try:
            top = self.app.top_window()
            if top.handle != self._main_handle:
                return top
        except Exception:
            pass
        return self.main_window

    def dismiss_startup_popups(self):
        """Dismiss popups that appear during app startup.

        Directly connects to popup windows by title using Desktop search.
        Does NOT rely on main_window handle comparison (which fails when
        _find_main_window() incorrectly resolves to the popup itself).

        After a successful dismiss it re-resolves main_window.
        """
        from pywinauto import Desktop

        desktop = Desktop(backend="uia")

        app_pid = None
        try:
            app_pid = self.app.process
        except Exception:
            pass

        for win in desktop.windows():
            try:
                # Only target windows from our app's process
                if app_pid and win.process_id() != app_pid:
                    continue

                title = win.window_text()
                if not title:
                    continue

                # Try each dismiss button
                for btn_title in self._popup_dismiss_buttons:
                    try:
                        btn = win.child_window(
                            title=btn_title, control_type="Button",
                        )
                        if btn.exists(timeout=0):
                            logger.warning(
                                f"Startup popup dismissed: '{title}' "
                                f"with '{btn_title}'"
                            )
                            btn.click_input()
                            time.sleep(self.TIMING_AFTER_POPUP_DISMISS)
                            self._find_main_window()
                            return True
                    except Exception:
                        continue

                for aid in self._popup_dismiss_auto_ids:
                    try:
                        btn = win.child_window(
                            auto_id=aid, control_type="Button",
                        )
                        if btn.exists(timeout=0):
                            logger.warning(
                                f"Startup popup dismissed: '{title}' "
                                f"with auto_id='{aid}'"
                            )
                            btn.click_input()
                            time.sleep(self.TIMING_AFTER_POPUP_DISMISS)
                            self._find_main_window()
                            return True
                    except Exception:
                        continue
            except Exception:
                continue

        return False

    def _auto_dismiss_popup(self):
        """Try to dismiss an unexpected popup. Returns True if dismissed."""
        popup = self.check_popup()
        if popup is None:
            return False

        title = popup.window_text() or "(no title)"
        logger.warning(f"Auto-dismissing popup: '{title}'")

        # Try by button title
        for btn_title in self._popup_dismiss_buttons:
            try:
                btn = popup.child_window(title=btn_title, control_type="Button")
                if btn.exists(timeout=1):
                    btn.click_input()
                    logger.info(f"Popup auto-dismissed with '{btn_title}'")
                    time.sleep(self.TIMING_AFTER_POPUP_DISMISS)
                    return True
            except Exception:
                continue

        # Try by automation ID
        for aid in self._popup_dismiss_auto_ids:
            try:
                btn = popup.child_window(auto_id=aid, control_type="Button")
                if btn.exists(timeout=1):
                    btn.click_input()
                    logger.info(f"Popup auto-dismissed with auto_id='{aid}'")
                    time.sleep(self.TIMING_AFTER_POPUP_DISMISS)
                    return True
            except Exception:
                continue

        logger.error(f"Failed to auto-dismiss popup: '{title}'")
        return False

    def _with_popup_retry(self, action, description=""):
        """Execute action; on element-not-found, dismiss popup and retry.

        Also retries on transient COM errors (UIA tree staleness) which
        are common in WinForms apps after UI transitions.

        Retry behavior is configurable via set_retry_config().
        Default: 2 attempts total (1 retry), 0.5s delay between retries.
        """
        max_attempts = self._retry_config.get("max_attempts", 2)
        delay = self._retry_config.get("delay", 0.5)

        for attempt in range(max_attempts):
            try:
                return action()
            except Exception as e:
                if attempt >= max_attempts - 1:
                    raise
                if self._auto_dismiss_popup():
                    logger.info(
                        f"Retrying after popup dismiss "
                        f"(attempt {attempt + 2}/{max_attempts}): "
                        f"{description}"
                    )
                elif type(e).__name__ == "COMError":
                    logger.info(
                        f"Retrying after COM error "
                        f"(attempt {attempt + 2}/{max_attempts}): "
                        f"{description}"
                    )
                    # Re-wrap window handle to get fresh UIA reference
                    self.main_window = self.app.window(
                        handle=self._main_handle,
                    )
                else:
                    raise
                time.sleep(delay)

    def set_retry_config(self, config):
        """Configure popup retry behavior.

        Args:
            config: dict with optional keys:
                - max_attempts (int): Total attempts including first try. Default 2.
                - delay (float): Seconds between retries. Default 0.5.
        """
        self._retry_config = config
        logger.info(f"Retry config updated: {config}")

    def set_timing(self, config):
        """Override timing defaults from a config dict.

        Args:
            config: dict with optional keys matching TIMING_* class attributes
                (lowercase, without TIMING_ prefix). Example::

                    {"after_click": 0.2, "after_popup_dismiss": 0.3}
        """
        mapping = {
            "after_click": "TIMING_AFTER_CLICK",
            "after_popup_dismiss": "TIMING_AFTER_POPUP_DISMISS",
            "after_combo_expand": "TIMING_AFTER_COMBO_EXPAND",
            "after_close": "TIMING_AFTER_CLOSE",
            "poll_interval": "TIMING_POLL_INTERVAL",
        }
        for key, attr in mapping.items():
            if key in config:
                setattr(self, attr, float(config[key]))
        logger.info(f"Timing config updated: {config}")

    def refresh_window(self):
        """
        Re-detect the main window. Call this after actions that change
        the window (e.g. dialog dismissed, new form loaded).
        Updates self.main_window to the current active window.
        """
        old_handle = self._main_handle
        self._find_main_window()
        new_handle = self._main_handle
        title = self.main_window.window_text() or "(no title)"
        if old_handle != new_handle:
            logger.info(f"Window changed: handle {old_handle} → {new_handle} ('{title}')")
        else:
            logger.info(f"Window refreshed: same handle {new_handle} ('{title}')")
        return self.main_window

    def click_button(self, name=None, auto_id=None, found_index=0):
        """
        Click a button by name or automation ID.

        Args:
            name: Button text/name.
            auto_id: Automation ID (more reliable for locating).
            found_index: Index if multiple matches (0-based).
        """
        criteria = {}
        if auto_id:
            criteria["auto_id"] = auto_id
        if name:
            criteria["title"] = name
        criteria["control_type"] = "Button"
        criteria["found_index"] = found_index

        def _do():
            logger.info(f"Clicking button: {name or auto_id}")
            btn = self._active_window().child_window(**criteria)
            btn.wait("visible", timeout=10)
            btn.click_input()
            time.sleep(self.TIMING_AFTER_CLICK)

        self._with_popup_retry(_do, f"click_button({name or auto_id})")

    def click_radio(self, auto_id=None, name=None, found_index=0):
        """Click a RadioButton by name or automation ID.

        Args:
            auto_id: Automation ID of the radio button.
            name: Text/name of the radio button.
            found_index: Index if multiple matches (0-based).
        """
        criteria = {"control_type": "RadioButton"}
        if auto_id:
            criteria["auto_id"] = auto_id
        if name:
            criteria["title"] = name
        criteria["found_index"] = found_index

        def _do():
            logger.info(f"Clicking radio button: {name or auto_id}")
            btn = self._active_window().child_window(**criteria)
            btn.wait("visible", timeout=10)
            btn.click_input()
            time.sleep(self.TIMING_AFTER_CLICK)

        self._with_popup_retry(_do, f"click_radio({name or auto_id})")

    def click_element(self, **kwargs):
        """Click any UI element by flexible criteria."""
        def _do():
            logger.info(f"Clicking element: {kwargs}")
            elem = self._active_window().child_window(**kwargs)
            elem.wait("visible", timeout=10)
            elem.click_input()
            time.sleep(self.TIMING_AFTER_CLICK)

        self._with_popup_retry(_do, f"click_element({kwargs})")

    def type_text(self, text, auto_id=None, name=None, control_type="Edit",
                  sensitive=False):
        """Type text into an input field.

        Args:
            text: Text to type.
            auto_id: Automation ID of the input field.
            name: Name/title of the input field.
            control_type: UI control type (default: "Edit").
            sensitive: If True, logs '****' instead of the actual text.
        """
        criteria = {"control_type": control_type}
        if auto_id:
            criteria["auto_id"] = auto_id
        if name:
            criteria["title"] = name

        def _do():
            display = "****" if sensitive else f"'{text}'"
            logger.info(f"Typing into {auto_id or name}: {display}")
            field = self._active_window().child_window(**criteria)
            field.wait("visible", timeout=10)
            field.set_text(text)

        self._with_popup_retry(_do, f"type_text({auto_id or name})")

    def type_keys_to_field(self, text, auto_id=None, name=None,
                           control_type="Edit", sensitive=False):
        """Type text into an input field using keyboard simulation.

        Unlike type_text (which uses set_text), this simulates real keystrokes
        so that the application's auto-formatting (e.g. auto-dash) is triggered.

        Args:
            text: Text to type.
            auto_id: Automation ID of the input field.
            name: Name/title of the input field.
            control_type: UI control type (default: "Edit").
            sensitive: If True, logs '****' instead of the actual text.
        """
        criteria = {"control_type": control_type}
        if auto_id:
            criteria["auto_id"] = auto_id
        if name:
            criteria["title"] = name

        def _do():
            display = "****" if sensitive else f"'{text}'"
            logger.info(f"Typing keys into {auto_id or name}: {display}")
            field = self._active_window().child_window(**criteria)
            field.wait("visible", timeout=10)
            field.click_input()
            field.type_keys(text, with_spaces=True, pause=0.02)

        self._with_popup_retry(_do, f"type_keys_to_field({auto_id or name})")

    def get_text(self, auto_id=None, name=None, control_type=None):
        """Get text content from a UI element."""
        criteria = {}
        if auto_id:
            criteria["auto_id"] = auto_id
        if name:
            criteria["title"] = name
        if control_type:
            criteria["control_type"] = control_type

        elem = self._active_window().child_window(**criteria)
        return elem.window_text()

    def select_menu(self, *menu_path):
        """Navigate menu items. e.g., select_menu('File', 'Open')."""
        logger.info(f"Selecting menu: {' > '.join(menu_path)}")
        self._active_window().menu_select(" -> ".join(menu_path))

    def select_tab(self, tab_name):
        """Select a tab by name."""
        logger.info(f"Selecting tab: {tab_name}")
        tab = self._active_window().child_window(title=tab_name, control_type="TabItem")
        tab.click_input()
        time.sleep(self.TIMING_AFTER_CLICK)

    def select_combobox(self, name=None, auto_id=None, value=None):
        """Select a value from a combobox/dropdown."""
        criteria = {"control_type": "ComboBox"}
        if auto_id:
            criteria["auto_id"] = auto_id
        if name:
            criteria["title"] = name

        logger.info(f"Selecting combobox {name or auto_id} -> {value}")
        combo = self._active_window().child_window(**criteria)
        combo.select(value)

    def click_combobox_item(self, auto_id=None, name=None, value=None):
        """Select a combobox item by expanding and clicking directly.

        More reliable than combo.select() for WinForms comboboxes where
        select() silently fails. Mimics human interaction: open dropdown,
        find item, click it.

        Args:
            auto_id: Automation ID of the combobox.
            name: Name/title of the combobox.
            value: Text (or partial text) of the item to click.

        Returns:
            list[str]: All available item texts found in the dropdown.
        """
        criteria = {"control_type": "ComboBox"}
        if auto_id:
            criteria["auto_id"] = auto_id
        if name:
            criteria["title"] = name

        combo = self._active_window().child_window(**criteria)
        combo.wait("visible", timeout=10)

        # Expand the dropdown
        combo.expand()
        time.sleep(self.TIMING_AFTER_COMBO_EXPAND)

        # Find ListItems — try combo descendants first, then Desktop popup
        list_items = []
        try:
            list_items = combo.descendants(control_type="ListItem")
        except Exception:
            pass

        if not list_items:
            try:
                child_list = combo.child_window(control_type="List")
                if child_list.exists(timeout=1):
                    list_items = child_list.children(control_type="ListItem")
            except Exception:
                pass

        if not list_items:
            try:
                from pywinauto import Desktop
                desktop = Desktop(backend=self.backend)
                for win in desktop.windows():
                    try:
                        if win.element_info.control_type == "List":
                            list_items = win.children(control_type="ListItem")
                            if list_items:
                                break
                    except Exception:
                        continue
            except Exception:
                pass

        # Log all available items
        all_texts = [li.window_text() for li in list_items if li.window_text()]
        logger.info(
            f"Combobox '{auto_id or name}' dropdown items ({len(all_texts)}): "
            f"{all_texts}"
        )

        # Find and click the matching item
        target = None
        for li in list_items:
            text = li.window_text()
            if text and value and value.lower() in text.lower():
                target = li
                break

        if target:
            target_text = target.window_text()
            logger.info(
                f"Clicking combobox item: '{target_text}' "
                f"(matched '{value}')"
            )
            target.click_input()
            time.sleep(self.TIMING_AFTER_CLICK)
        else:
            # Collapse if no match found
            try:
                combo.collapse()
            except Exception:
                pass
            raise ValueError(
                f"Item '{value}' not found in combobox '{auto_id or name}'. "
                f"Available: {all_texts}"
            )

        return all_texts

    def get_list_items(self, auto_id=None, name=None):
        """Get all items from a List or ListView control.

        Returns:
            list[str]: Text of each item in the list.
        """
        criteria = {}
        if auto_id:
            criteria["auto_id"] = auto_id
        if name:
            criteria["title"] = name

        # Try List first, then DataGrid (ListView)
        for ctrl_type in ("List", "DataGrid"):
            try:
                criteria["control_type"] = ctrl_type
                container = self._active_window().child_window(**criteria)
                if container.exists(timeout=2):
                    items = container.children(control_type="ListItem")
                    texts = [item.window_text() for item in items]
                    logger.info(f"List '{auto_id or name}' ({ctrl_type}): {len(texts)} items")
                    return texts
            except Exception:
                continue
            finally:
                criteria.pop("control_type", None)

        logger.warning(f"List '{auto_id or name}' not found")
        return []

    def select_list_item(self, item_text, auto_id=None, name=None):
        """Select an item in a List or ListView by its text.

        Args:
            item_text: Text of the item to select.
            auto_id: Automation ID of the list control.
            name: Name/title of the list control.
        """
        criteria = {}
        if auto_id:
            criteria["auto_id"] = auto_id
        if name:
            criteria["title"] = name

        def _do():
            for ctrl_type in ("List", "DataGrid"):
                try:
                    criteria["control_type"] = ctrl_type
                    container = self._active_window().child_window(**criteria)
                    if container.exists(timeout=2):
                        item = container.child_window(title=item_text, control_type="ListItem")
                        item.wait("visible", timeout=10)
                        item.click_input()
                        logger.info(f"Selected '{item_text}' in {ctrl_type} '{auto_id or name}'")
                        return
                except Exception:
                    continue
                finally:
                    criteria.pop("control_type", None)
            raise RuntimeError(f"Item '{item_text}' not found in list '{auto_id or name}'")

        self._with_popup_retry(_do, f"select_list_item({auto_id or name}, {item_text})")

    def get_combobox_items(self, auto_id=None, name=None):
        """Get all available options from a ComboBox/dropdown.

        Returns:
            list[str]: Text of each option.
        """
        criteria = {"control_type": "ComboBox"}
        if auto_id:
            criteria["auto_id"] = auto_id
        if name:
            criteria["title"] = name

        combo = self._active_window().child_window(**criteria)
        combo.wait("visible", timeout=10)

        items = []

        # Strategy 1: expand → search for ListItems
        try:
            combo.expand()
            time.sleep(self.TIMING_AFTER_COMBO_EXPAND)

            # 1a: descendants ListItem
            try:
                list_items = combo.descendants(control_type="ListItem")
                items = [li.window_text() for li in list_items if li.window_text()]
            except Exception:
                pass

            # 1b: child List → ListItem children
            if not items:
                try:
                    child_list = combo.child_window(control_type="List")
                    if child_list.exists(timeout=1):
                        list_items = child_list.children(control_type="ListItem")
                        items = [li.window_text() for li in list_items if li.window_text()]
                except Exception:
                    pass

            # 1c: Desktop popup List (WinForms dropdown = top-level window)
            if not items:
                try:
                    from pywinauto import Desktop
                    desktop = Desktop(backend=self.backend)
                    for win in desktop.windows():
                        try:
                            if win.element_info.control_type == "List":
                                list_items = win.children(control_type="ListItem")
                                if list_items:
                                    items = [li.window_text() for li in list_items if li.window_text()]
                                    break
                        except Exception:
                            continue
                except Exception:
                    pass

            try:
                combo.collapse()
            except Exception:
                pass
        except Exception:
            try:
                combo.collapse()
            except Exception:
                pass

        # Strategy 2: item_texts()
        if not items:
            try:
                items = list(combo.item_texts())
            except Exception:
                pass

        # Strategy 3: texts() fallback
        if not items:
            try:
                raw = combo.texts()
                items = [t for t in raw if t and t.strip()]
            except Exception:
                pass

        logger.info(f"ComboBox '{auto_id or name}': {len(items)} options — {items}")
        return items

    def get_table_data(self, auto_id=None, name=None):
        """Read data from a DataGrid/Table control.

        Returns:
            dict with 'headers' (list[str]) and 'rows' (list[list[str]]).
        """
        import re as _re

        criteria = {}
        if auto_id:
            criteria["auto_id"] = auto_id
        if name:
            criteria["title"] = name

        for ctrl_type in ("DataGrid", "Table", "List"):
            try:
                criteria["control_type"] = ctrl_type
                grid = self._active_window().child_window(**criteria)
                if not grid.exists(timeout=2):
                    continue

                # --- Headers ---
                headers = []
                try:
                    header_items = grid.children(control_type="HeaderItem")
                    if not header_items:
                        header_row = grid.child_window(control_type="Header")
                        header_items = header_row.children(control_type="HeaderItem")
                    headers = [h.window_text() for h in header_items]
                except Exception:
                    pass

                # --- Rows ---
                rows = []

                # Strategy 1: DataItem/ListItem children
                try:
                    data_items = grid.children(control_type="DataItem")
                    if not data_items:
                        data_items = grid.children(control_type="ListItem")
                    for row_elem in data_items:
                        cells = row_elem.children()
                        row = [cell.window_text() for cell in cells]
                        if not row:
                            row = [row_elem.window_text()]
                        rows.append(row)
                except Exception:
                    pass

                # Strategy 2: Custom children (WinForms DataGridView)
                if not rows:
                    try:
                        custom_rows = grid.children(control_type="Custom")
                        for row_elem in custom_rows:
                            cells = row_elem.children()
                            row = []
                            for c in cells:
                                val = ""
                                try:
                                    val = c.iface_value.CurrentValue
                                except Exception:
                                    try:
                                        val = c.legacy_properties().get("Value", "")
                                    except Exception:
                                        val = c.window_text() or ""
                                if val:
                                    row.append(val)
                            if not row:
                                row = [row_elem.window_text()]
                            rows.append(row)
                    except Exception:
                        pass

                # Strategy 3: Parse Edit descendants by "Column Row N" pattern
                if not rows:
                    try:
                        edits = grid.descendants(control_type="Edit")
                        row_map = {}
                        col_order = []
                        for e in edits:
                            edit_name = e.window_text() or ""
                            match = _re.match(r"(.+?) Row (\d+)", edit_name)
                            if match:
                                col_name = match.group(1)
                                row_num = int(match.group(2))
                                if col_name not in col_order:
                                    col_order.append(col_name)
                                if row_num not in row_map:
                                    row_map[row_num] = {}
                                cell_val = ""
                                try:
                                    cell_val = e.iface_value.CurrentValue
                                except Exception:
                                    try:
                                        cell_val = e.legacy_properties().get("Value", "")
                                    except Exception:
                                        pass
                                row_map[row_num][col_name] = cell_val

                        if row_map:
                            if not headers:
                                headers = col_order
                            for row_num in sorted(row_map.keys()):
                                row = [row_map[row_num].get(col, "") for col in headers]
                                rows.append(row)
                    except Exception:
                        pass

                logger.info(f"Table '{auto_id or name}' ({ctrl_type}): {len(headers)} cols, {len(rows)} rows")
                return {"headers": headers, "rows": rows}
            except Exception:
                continue
            finally:
                criteria.pop("control_type", None)

        logger.warning(f"Table '{auto_id or name}' not found")
        return {"headers": [], "rows": []}

    def wait_for_element(self, timeout=10, **kwargs):
        """Wait until an element becomes visible."""
        def _do():
            elem = self._active_window().child_window(**kwargs)
            elem.wait("visible", timeout=timeout)
            return elem

        return self._with_popup_retry(_do, f"wait_for_element({kwargs})")

    def element_exists(self, **kwargs):
        """Check if an element exists (without waiting)."""
        try:
            elem = self._active_window().child_window(**kwargs)
            return elem.exists(timeout=1)
        except Exception:
            return False

    def find_element_in_any_window(self, auto_id=None, control_type="Button",
                                     timeout=10, **kwargs):
        """Find an element across all windows of the application.

        Iterates over all windows belonging to the app process and returns
        the first matching element. Useful when the target element may be
        in a popup or secondary window.

        Args:
            auto_id: Automation ID of the element.
            control_type: UI control type (default: "Button").
            timeout: Max seconds to search.
            **kwargs: Additional child_window criteria (e.g. title).

        Returns:
            The element wrapper if found.

        Raises:
            TimeoutError: If element not found within timeout.
        """
        from pywinauto import findwindows

        criteria = {"control_type": control_type}
        if auto_id:
            criteria["auto_id"] = auto_id
        criteria.update(kwargs)

        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                handles = findwindows.find_windows(
                    process=self.app.process, backend=self.backend,
                )
                for hwnd in handles:
                    try:
                        win = self.app.window(handle=hwnd)
                        elem = win.child_window(**criteria)
                        if elem.exists(timeout=0):
                            logger.info(
                                f"Found element {auto_id or criteria} "
                                f"in window handle={hwnd}"
                            )
                            return elem
                    except Exception:
                        continue
            except Exception:
                pass
            time.sleep(self.TIMING_POLL_INTERVAL)

        raise TimeoutError(
            f"Element {auto_id or criteria} not found in any window "
            f"after {timeout}s"
        )

    def check_popup(self):
        """
        Check if an unexpected popup/dialog appeared on top of main window.
        Returns the popup window wrapper if found, None otherwise.
        """
        try:
            top = self.app.top_window()
            # If top_window differs from main_window → popup detected
            if top.handle != self._main_handle:
                title = top.window_text() or "(no title)"
                logger.warning(f"Popup detected: '{title}' (handle={top.handle})")
                return top
        except Exception as e:
            logger.debug(f"check_popup error: {e}")
        return None

    def dismiss_popup(self, button_name=None, auto_id=None):
        """
        Detect and dismiss a popup by clicking a button on it.

        Args:
            button_name: Text of button to click (e.g. "OK", "Yes", "Cancel").
            auto_id: Automation ID of button to click.

        Returns:
            True if popup was found and dismissed, False otherwise.
        """
        popup = self.check_popup()
        if popup is None:
            logger.info("No popup detected")
            return False

        criteria = {"control_type": "Button"}
        if auto_id:
            criteria["auto_id"] = auto_id
        elif button_name:
            criteria["title"] = button_name
        else:
            # Default: try OK, Yes, or Close
            for fallback in ["OK", "Yes", "Close"]:
                try:
                    btn = popup.child_window(title=fallback, control_type="Button")
                    if btn.exists(timeout=1):
                        btn.click_input()
                        logger.info(f"Popup dismissed with '{fallback}' button")
                        time.sleep(self.TIMING_AFTER_POPUP_DISMISS)
                        return True
                except Exception:
                    continue
            logger.warning("Popup found but no dismiss button matched")
            return False

        try:
            btn = popup.child_window(**criteria)
            btn.click_input()
            logger.info(f"Popup dismissed with {button_name or auto_id}")
            time.sleep(self.TIMING_AFTER_POPUP_DISMISS)
            return True
        except Exception as e:
            logger.error(f"Failed to dismiss popup: {e}")
            return False

    def print_control_tree(self, depth=3):
        """Print the UI control tree for debugging/element discovery."""
        logger.info("=== Control Tree ===")
        self.main_window.print_control_identifiers(depth=depth)

    def take_screenshot(self, name="screenshot"):
        """
        Capture screenshot of the application window.
        Returns the PIL Image object.
        """
        from PIL import Image
        import mss

        rect = self.main_window.rectangle()
        with mss.mss() as sct:
            monitor = {
                "left": rect.left,
                "top": rect.top,
                "width": rect.width(),
                "height": rect.height(),
            }
            screenshot = sct.grab(monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

        logger.info(f"Screenshot captured: {name}")
        return img

    def close(self):
        """Close the application gracefully, verifying process termination."""
        if self.app:
            logger.info("Closing application...")
            try:
                self.main_window.close()
                time.sleep(self.TIMING_AFTER_CLOSE)
                if self.app.is_process_running():
                    self.app.kill()
            except Exception as e:
                logger.warning(f"Error closing app: {e}")
                try:
                    self.app.kill()
                except Exception:
                    pass

            # Verify process is actually dead
            for _ in range(5):
                try:
                    if not self.app.is_process_running():
                        return
                except Exception:
                    return  # Process object invalid = process dead
                time.sleep(1)

            logger.error(
                f"Process still running after close+kill (pid={getattr(self.app, 'process', '?')}). "
                "Orphaned process may accumulate in CI."
            )

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
