"""
Window Monitor - Detect unexpected windows during UI automation tests.

Uses win32gui to enumerate all visible top-level windows on the desktop.
Runs a background daemon thread that polls periodically, plus provides
a single-check method for pre-interaction guards.

Usage:
    monitor = WindowMonitor(app_pid=driver.app.process, evidence=evidence)
    monitor.snapshot_baseline()
    monitor.add_whitelist(driver.main_window.handle)
    monitor.start(interval=1.0)
    # ... run tests ...
    detected = monitor.stop()
"""

import ctypes
import logging
import threading
import time

try:
    import win32gui
    import win32process
    _HAS_WIN32 = True
except ImportError:
    _HAS_WIN32 = False

logger = logging.getLogger(__name__)


class WindowMonitor:
    """Detect unexpected windows during UI automation tests."""

    def __init__(self, app_pid, evidence=None, on_detected=None):
        """
        Args:
            app_pid: PID of the app under test (whitelisted automatically).
            evidence: Evidence instance for desktop screenshots.
            on_detected: Optional callback(hwnd, title, pid) called on detection.
        """
        if not _HAS_WIN32:
            raise ImportError(
                "WindowMonitor requires pywin32. Install: pip install pywin32"
            )
        self._app_pid = app_pid
        self._evidence = evidence
        self._on_detected = on_detected

        self._baseline_handles = set()
        self._whitelist_handles = set()
        self._detected = []
        self._detected_handles = set()
        self._lock = threading.Lock()

        self._stop_event = threading.Event()
        self._thread = None

    def snapshot_baseline(self):
        """Record all currently visible window handles as baseline."""
        current = self._enum_visible_windows()
        self._baseline_handles = {hwnd for hwnd, _, _ in current}
        logger.info(f"Window monitor baseline: {len(self._baseline_handles)} windows")

    def add_whitelist(self, *handles):
        """Add handles to the whitelist (e.g. main_window handle)."""
        self._whitelist_handles.update(handles)

    def start(self, interval=1.0):
        """Start daemon thread that polls every `interval` seconds."""
        if self._thread and self._thread.is_alive():
            logger.warning("Window monitor already running")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            name="WindowMonitor",
            daemon=True,
        )
        self._thread.start()
        logger.info(f"Window monitor started (interval={interval}s)")

    def stop(self):
        """Stop monitoring, return list of detected windows."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        self._thread = None

        with self._lock:
            detected = list(self._detected)

        logger.info(f"Window monitor stopped — {len(detected)} unexpected window(s) detected")
        return detected

    def check_once(self):
        """Single check for unexpected windows.

        Called by UIDriver guard before each interaction.

        Returns:
            List of (hwnd, title, pid) for unexpected windows, or empty list.
        """
        return self._check_windows()

    def _monitor_loop(self, interval):
        """Thread target — loop until stop_event is set."""
        while not self._stop_event.is_set():
            try:
                self._check_windows()
            except Exception as e:
                logger.debug(f"Window monitor check error: {e}")
            self._stop_event.wait(interval)

    def _check_windows(self):
        """Enumerate windows, compare vs baseline + whitelist + app_pid.

        Returns:
            List of newly detected (hwnd, title, pid) tuples.
        """
        current = self._enum_visible_windows()
        newly_detected = []

        for hwnd, title, pid in current:
            # Skip baseline windows
            if hwnd in self._baseline_handles:
                continue
            # Skip whitelisted handles
            if hwnd in self._whitelist_handles:
                continue
            # Skip windows belonging to the app under test
            if pid == self._app_pid:
                continue
            # Skip already-detected handles (deduplication)
            if hwnd in self._detected_handles:
                continue

            # New unexpected window found
            proc_name = self._get_process_name(pid)
            logger.warning(
                f"Unexpected window detected: '{title}' "
                f"(PID={pid}, process={proc_name}, hwnd={hwnd})"
            )

            with self._lock:
                self._detected.append((hwnd, title, pid))
                self._detected_handles.add(hwnd)

            newly_detected.append((hwnd, title, pid))

            # Desktop screenshot
            if self._evidence:
                try:
                    self._evidence.desktop_screenshot(
                        name=f"unexpected_window_{hwnd}"
                    )
                except Exception as e:
                    logger.debug(f"Failed to capture desktop screenshot: {e}")

            # Optional callback
            if self._on_detected:
                try:
                    self._on_detected(hwnd, title, pid)
                except Exception as e:
                    logger.debug(f"on_detected callback error: {e}")

        return newly_detected

    @staticmethod
    def _enum_visible_windows():
        """Return set of (hwnd, title, pid) for all visible top-level windows.

        Filters out windows with empty titles and zero-size windows.
        """
        results = []

        def _callback(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return True
            title = win32gui.GetWindowText(hwnd)
            if not title:
                return True
            # Skip zero-size windows (hidden system windows)
            try:
                rect = win32gui.GetWindowRect(hwnd)
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]
                if width <= 0 or height <= 0:
                    return True
            except Exception:
                return True
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            results.append((hwnd, title, pid))
            return True

        try:
            win32gui.EnumWindows(_callback, None)
        except Exception as e:
            logger.debug(f"EnumWindows error: {e}")

        return results

    @staticmethod
    def _get_process_name(pid):
        """Get process name from PID. Returns 'unknown' on failure."""
        try:
            import psutil
            proc = psutil.Process(pid)
            return proc.name()
        except Exception:
            pass
        # Fallback using ctypes
        try:
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, pid
            )
            if handle:
                buf = ctypes.create_unicode_buffer(260)
                size = ctypes.c_uint(260)
                ctypes.windll.kernel32.QueryFullProcessImageNameW(
                    handle, 0, buf, ctypes.byref(size)
                )
                ctypes.windll.kernel32.CloseHandle(handle)
                if buf.value:
                    import os
                    return os.path.basename(buf.value)
        except Exception:
            pass
        return "unknown"
