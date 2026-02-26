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

    def __init__(self, app_path, title=None, class_name=None, backend="uia",
                 startup_wait=3, work_dir=None):
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
        """
        self.app_path = app_path
        self.title = title
        self.class_name = class_name
        self.backend = backend
        self.startup_wait = startup_wait
        self.app = None
        self.main_window = None
        # Auto-detect work_dir from app_path if not specified
        if work_dir:
            self.work_dir = work_dir
        elif app_path and os.path.isabs(app_path):
            self.work_dir = os.path.dirname(app_path)
        else:
            self.work_dir = None

    def start(self):
        """Launch the application and connect to its main window."""
        from pywinauto import Application

        logger.info(f"Starting application: {self.app_path} (backend={self.backend}, work_dir={self.work_dir})")

        try:
            self.app = Application(backend=self.backend).start(
                self.app_path, timeout=30, work_dir=self.work_dir
            )
        except Exception:
            # Fallback: try launching via subprocess then connecting
            logger.warning("Direct start failed, trying subprocess + connect...")
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
        """Locate the main window of the application."""
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

    def refresh_window(self):
        """
        Re-detect the main window. Call this after actions that change
        the window (e.g. dialog dismissed, new form loaded).
        Updates self.main_window to the current active window.
        """
        old_handle = self.main_window.handle if self.main_window else None
        self._find_main_window()
        new_handle = self.main_window.handle
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

        logger.info(f"Clicking button: {name or auto_id}")
        btn = self.main_window.child_window(**criteria)
        btn.wait("visible", timeout=10)
        btn.click_input()
        time.sleep(0.3)

    def click_element(self, **kwargs):
        """Click any UI element by flexible criteria."""
        logger.info(f"Clicking element: {kwargs}")
        elem = self.main_window.child_window(**kwargs)
        elem.wait("visible", timeout=10)
        elem.click_input()
        time.sleep(0.3)

    def type_text(self, text, auto_id=None, name=None, control_type="Edit"):
        """Type text into an input field."""
        criteria = {"control_type": control_type}
        if auto_id:
            criteria["auto_id"] = auto_id
        if name:
            criteria["title"] = name

        logger.info(f"Typing into {auto_id or name}: '{text}'")
        field = self.main_window.child_window(**criteria)
        field.wait("visible", timeout=10)
        field.set_text(text)

    def get_text(self, auto_id=None, name=None, control_type=None):
        """Get text content from a UI element."""
        criteria = {}
        if auto_id:
            criteria["auto_id"] = auto_id
        if name:
            criteria["title"] = name
        if control_type:
            criteria["control_type"] = control_type

        elem = self.main_window.child_window(**criteria)
        return elem.window_text()

    def select_menu(self, *menu_path):
        """Navigate menu items. e.g., select_menu('File', 'Open')."""
        logger.info(f"Selecting menu: {' > '.join(menu_path)}")
        self.main_window.menu_select(" -> ".join(menu_path))

    def select_tab(self, tab_name):
        """Select a tab by name."""
        logger.info(f"Selecting tab: {tab_name}")
        tab = self.main_window.child_window(title=tab_name, control_type="TabItem")
        tab.click_input()
        time.sleep(0.3)

    def select_combobox(self, name=None, auto_id=None, value=None):
        """Select a value from a combobox/dropdown."""
        criteria = {"control_type": "ComboBox"}
        if auto_id:
            criteria["auto_id"] = auto_id
        if name:
            criteria["title"] = name

        logger.info(f"Selecting combobox {name or auto_id} -> {value}")
        combo = self.main_window.child_window(**criteria)
        combo.select(value)

    def wait_for_element(self, timeout=10, **kwargs):
        """Wait until an element becomes visible."""
        elem = self.main_window.child_window(**kwargs)
        elem.wait("visible", timeout=timeout)
        return elem

    def element_exists(self, **kwargs):
        """Check if an element exists (without waiting)."""
        try:
            elem = self.main_window.child_window(**kwargs)
            return elem.exists(timeout=1)
        except Exception:
            return False

    def check_popup(self):
        """
        Check if an unexpected popup/dialog appeared on top of main window.
        Returns the popup window wrapper if found, None otherwise.
        """
        try:
            top = self.app.top_window()
            # Kalau top_window berbeda dari main_window → ada popup
            if top.handle != self.main_window.handle:
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
            # Default: coba cari OK, Yes, atau Close
            for fallback in ["OK", "Yes", "Close"]:
                try:
                    btn = popup.child_window(title=fallback, control_type="Button")
                    if btn.exists(timeout=1):
                        btn.click_input()
                        logger.info(f"Popup dismissed with '{fallback}' button")
                        time.sleep(0.3)
                        return True
                except Exception:
                    continue
            logger.warning("Popup found but no dismiss button matched")
            return False

        try:
            btn = popup.child_window(**criteria)
            btn.click_input()
            logger.info(f"Popup dismissed with {button_name or auto_id}")
            time.sleep(0.3)
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
        """Close the application gracefully."""
        if self.app:
            logger.info("Closing application...")
            try:
                self.main_window.close()
                time.sleep(1)
                if self.app.is_process_running():
                    self.app.kill()
            except Exception as e:
                logger.warning(f"Error closing app: {e}")
                try:
                    self.app.kill()
                except Exception:
                    pass

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
