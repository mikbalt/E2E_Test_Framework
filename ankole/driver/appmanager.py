import datetime
import logging
import os
import time
import zipfile

logger = logging.getLogger(__name__)


class UIAppManager:
    """
    UIAppManager is responsible for managing the lifecycle of a UI application
    used in automated tests.

    Responsibilities:
    - Start UI drivers
    - Setup and stop unexpected window monitoring
    - Collect application logs
    - Collect remote logs from Loki

    This class allows tests to work with multiple applications dynamically
    using the pytest marker:

        @pytest.mark.apps("e_admin", "testhsm")
    """

    def __init__(self, app_name, config):
        """
        Initialize manager for a specific application.

        Args:
            app_name (str):
                Name of the application defined in settings.yaml.

            config (dict):
                Global configuration object injected by pytest fixture.

        Example settings.yaml structure:

            apps:
                e_admin:
                    path: C:/apps/e_admin.exe
                    class_name: EAdminWindow
                    backend: uia
                    startup_wait: 5
        """

        self.app_name = app_name
        self.config = config.get("apps", {}).get(app_name, {})
        self.global_config = config

    # ------------------------------------------------
    # Driver Management
    # ------------------------------------------------

    def create_driver(self):
        """
        Create and start a UIDriver for the configured application.

        Returns:
            UIDriver:
                Initialized driver instance connected to the application.

        Usage (internally used by pytest fixture):

            manager = UIAppManager("e_admin", config)
            driver = manager.create_driver()

        The driver will automatically launch the application defined
        in settings.yaml.
        """

        from ankole.driver.ui_driver import UIDriver

        driver = UIDriver(
            app_path=self.config.get("path"),
            class_name=self.config.get("class_name"),
            backend=self.config.get("backend", "uia"),
            startup_wait=self.config.get("startup_wait", 5),
        )

        driver.start()

        logger.info(f"{self.app_name} started")

        return driver

    # ------------------------------------------------
    # Window Monitoring
    # ------------------------------------------------

    def setup_window_monitor(self, driver, evidence):
        """
        Start monitoring unexpected popup windows during a test.

        This helps detect UI errors such as:
        - crash dialogs
        - warning popups
        - unexpected modal windows

        Args:
            driver (UIDriver):
                Running application driver.

            evidence:
                Evidence manager used for storing screenshots or logs.

        Returns:
            WindowMonitor | None

        Example (internal usage):

            monitor = manager.setup_window_monitor(driver, evidence)
        """

        monitor_cfg = self.config.get("window_monitor", {})

        if not monitor_cfg.get("enabled", True):
            return None

        from ankole.driver.window_monitor import WindowMonitor

        pid = driver.app.process

        monitor = WindowMonitor(app_pid=pid, evidence=evidence)

        monitor.snapshot_baseline()

        monitor.add_whitelist(driver.main_window.handle)

        interval = monitor_cfg.get("interval", 1.0)

        monitor.start(interval=interval)

        driver.set_window_monitor(monitor)

        return monitor

    def stop_window_monitor(self, driver, monitor):
        """
        Stop the running window monitor and report unexpected windows.

        Args:
            driver (UIDriver)
            monitor (WindowMonitor | None)

        This function is automatically called during fixture teardown.
        """

        if monitor is None:
            return

        detected = monitor.stop()

        driver.set_window_monitor(None)

        if detected:
            logger.warning(
                f"{len(detected)} unexpected window(s) detected in {self.app_name}"
            )

    # ------------------------------------------------
    # Application Log Collection
    # ------------------------------------------------

    def collect_app_logs(self, evidence, test_name):
        """
        Collect local application logs and attach them to the test evidence.

        Logs are compressed into a ZIP file and attached to Allure report.

        Args:
            evidence:
                Evidence manager storing artifacts for the test.

            test_name (str):
                Name of the executed test case.

        Example output:

            evidence/
                AppLogs_test_generate_key_20260315_210000.zip
        """

        app_logs_dir = self.config.get("app_logs_dir", "")

        if not app_logs_dir or not os.path.isdir(app_logs_dir):
            logger.debug(f"{self.app_name} log dir not found: {app_logs_dir}")
            return

        try:

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

            zip_name = f"{self.app_name}_AppLogs_{test_name}_{timestamp}.zip"

            zip_path = os.path.join(evidence.evidence_dir, zip_name)

            file_count = 0

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:

                for root, _dirs, files in os.walk(app_logs_dir):

                    for fname in files:

                        full_path = os.path.join(root, fname)

                        arcname = os.path.relpath(full_path, app_logs_dir)

                        zf.write(full_path, arcname)

                        file_count += 1

            if file_count == 0:
                os.remove(zip_path)
                logger.info(f"{self.app_name} log dir empty, skipped zip")
                return

            logger.info(
                f"{self.app_name} collected {file_count} log files -> {zip_path}"
            )

            try:
                import allure

                with open(zip_path, "rb") as f:
                    allure.attach(
                        f.read(),
                        name=zip_name,
                        attachment_type="application/zip",
                        extension="zip",
                    )

            except ImportError:
                pass

        except Exception as e:
            logger.warning(f"{self.app_name} failed collecting logs: {e}")

    # ------------------------------------------------
    # Remote Log Collection
    # ------------------------------------------------

    def collect_remote_logs(self, start_time, end_time, evidence, test_name):
        """
        Query remote logs from Loki for the duration of the test.

        Args:
            start_time (float):
                Start timestamp of the test.

            end_time (float):
                End timestamp of the test.

            evidence:
                Evidence manager to attach logs.

            test_name (str):
                Name of the executed test.

        Configuration example in settings.yaml:

            remote_logs:
                enabled: true
                loki_url: http://loki:3100
                queries:
                    - '{job="hsm"}'
        """

        remote_cfg = self.global_config.get("remote_logs", {})

        if not remote_cfg.get("enabled", False):
            return

        try:

            from ankole.driver.loki_collector import LokiLogCollector

            collector = LokiLogCollector(
                loki_url=remote_cfg.get("loki_url", ""),
                queries=remote_cfg.get("queries", []),
                default_limit=remote_cfg.get("default_limit", 5000),
                timeout=remote_cfg.get("timeout", 30),
            )

            collector.collect(
                start_time=start_time,
                end_time=end_time,
                evidence=evidence,
                test_name=test_name,
            )

        except Exception as e:
            logger.warning(
                f"{self.app_name} failed collecting remote logs: {e}"
            )