"""
Log Collector - Collect and attach external log files as test evidence.

Many test tools (Java, C++, Go, GTest) write their own log files.
This module monitors those log paths and attaches them to Allure reports.

Usage:
    collector = LogCollector(evidence)

    # Collect a single log file after test execution
    collector.collect("C:/logs/pkcs11.log", name="pkcs11_keygen")

    # Collect all logs from a directory
    collector.collect_dir("/var/log/pkcs11/", pattern="*.log")

    # Monitor a log file during test execution (capture new lines only)
    with collector.monitor("/var/log/pkcs11/test.log") as mon:
        console.run("pkcs11-tool", ["--keygen"])
    # mon.captured contains only lines written during the 'with' block

    # Collect GTest XML report and convert to readable evidence
    collector.collect_gtest_xml("test_results.xml")

    # Collect multiple tool-specific logs from settings.yaml
    collector.collect_from_config(config["console_tools"]["pkcs11_java"])

    # Collect latest log execution
    collector.collect_latest("C:/logs/", pattern="*.log", name="pkcs11_keygen")
"""

import time
import glob
import logging
import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

logger = logging.getLogger(__name__)


class LogMonitor:
    """
    Context manager that captures lines appended to a log file during execution.

    Usage:
        with LogMonitor("/path/to/app.log") as mon:
            # run your test command here
            pass
        print(mon.captured)  # only lines written during the block
    """

    def __init__(self, log_path, encoding="utf-8"):
        self.log_path = log_path
        self.encoding = encoding
        self.captured = ""
        self._start_pos = 0

    def __enter__(self):
        if os.path.exists(self.log_path):
            self._start_pos = os.path.getsize(self.log_path)
        else:
            self._start_pos = 0
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, "rb") as f:
                    f.seek(self._start_pos)
                    raw = f.read()
                self.captured = raw.decode(self.encoding, errors="replace")
            except Exception as e:
                logger.warning(f"Could not read log file {self.log_path}: {e}")
                self.captured = f"[Error reading log: {e}]"
        else:
            self.captured = "[Log file not found after execution]"
        return False  # don't suppress exceptions


class LogCollector:
    """
    Collect external log files and attach them as Allure evidence.

    Works with the Evidence class to ensure all logs are stored in the
    test's evidence directory AND attached to the Allure report.
    """

    def __init__(self, evidence=None, evidence_dir=None):
        """
        Args:
            evidence: Evidence instance (preferred — auto-attaches to Allure).
            evidence_dir: Manual evidence directory (if no Evidence instance).
        """
        self.evidence = evidence
        if evidence:
            self.evidence_dir = evidence.evidence_dir
        elif evidence_dir:
            self.evidence_dir = evidence_dir
            os.makedirs(evidence_dir, exist_ok=True)
        else:
            self.evidence_dir = "evidence"
            os.makedirs(self.evidence_dir, exist_ok=True)

        self.collected_files = []

    def collect(self, log_path, name=None, max_size_mb=10):
        """
        Collect a single log file and attach to evidence.

        Args:
            log_path: Absolute or relative path to the log file.
            name: Display name in Allure report (default: filename).
            max_size_mb: Skip files larger than this (default: 10MB).

        Returns:
            Path to the collected copy, or None if file not found.
        """
        if not os.path.exists(log_path):
            logger.warning(f"Log file not found: {log_path}")
            self._attach_text(f"[Log file not found: {log_path}]", name or "missing_log")
            return None

        file_size = os.path.getsize(log_path) / (1024 * 1024)
        if file_size > max_size_mb:
            logger.warning(f"Log file too large ({file_size:.1f}MB > {max_size_mb}MB): {log_path}")
            # Collect only the last portion
            return self._collect_tail(log_path, name, lines=500)

        basename = name or os.path.basename(log_path)
        # Ensure unique filename
        ext = os.path.splitext(log_path)[1] or ".log"
        safe_name = _safe_filename(basename)
        if not safe_name.endswith(ext):
            safe_name += ext

        dest = os.path.join(self.evidence_dir, safe_name)
        shutil.copy2(log_path, dest)
        self.collected_files.append(dest)

        logger.info(f"Collected log: {log_path} -> {dest}")

        # Attach to Allure
        self._attach_file(dest, basename)

        # Also log to Evidence instance
        if self.evidence:
            self.evidence.log(f"Collected log: {log_path} ({file_size:.2f}MB)")

        return dest

    def collect_latest(self, log_dir, pattern=None, name=None, max_size_mb=10, wait_timeout=10):
        """
        Collect the latest file from a directory (supports files without extension).

        Args:
            log_dir (str): Directory containing logs
            pattern (str, optional): Pattern filter (e.g. '*.log'). If None → all files
            name (str, optional): Display name in Allure
            max_size_mb (int): Max size before tail collection
            wait_timeout (int): Seconds to wait for files to appear

        Returns:
            str or None
        """

        log_path = Path(log_dir)
        if not log_path.exists():
            logger.warning(f"Directory not found: {log_dir}")
            self._attach_text(f"[Directory not found: {log_dir}]", name or "missing_dir")
            return None

        # 🔥 Wait for file to appear (important for CLI-generated reports)
        files = []
        start_time = time.time()

        while time.time() - start_time < wait_timeout:
            if pattern:
                files = list(log_path.rglob(pattern))
            else:
                # ✅ Get ALL files (including no extension)
                files = [f for f in log_path.rglob("*") if f.is_file()]

            if files:
                break

            time.sleep(1)

        if not files:
            logger.warning(f"No files found in {log_dir} after {wait_timeout}s")
            self._attach_text(f"[No files found in {log_dir}]", name or "missing_file")
            return None

        # 🔥 Filter only fully written files (avoid 0-byte or temp files)
        files = [f for f in files if f.stat().st_size > 0]
        if not files:
            logger.warning("Files found but all are empty (possibly still writing)")
            return None

        # 🔥 Get latest modified file
        latest_file = max(files, key=lambda f: f.stat().st_mtime)
        logger.info(f"Latest file detected: {latest_file}")

        return self.collect(str(latest_file), name=name, max_size_mb=max_size_mb)

    def collect_text(self, text_content, name="output"):
        """
        Collect raw text content (e.g., captured stdout) as evidence.

        Args:
            text_content: String content to save.
            name: Display name.

        Returns:
            Path to the saved file.
        """
        if not text_content:
            return None

        safe_name = _safe_filename(name)
        if not safe_name.endswith(".txt") and not safe_name.endswith(".log"):
            safe_name += ".log"

        dest = os.path.join(self.evidence_dir, safe_name)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(text_content)

        self.collected_files.append(dest)
        self._attach_text(text_content, name)

        return dest

    def collect_dir(self, dir_path, pattern="*.log", name_prefix="", max_files=20):
        """
        Collect all matching log files from a directory.

        Args:
            dir_path: Directory to scan.
            pattern: Glob pattern to match files (default: *.log).
            name_prefix: Prefix for collected file names.
            max_files: Maximum number of files to collect.

        Returns:
            List of collected file paths.
        """
        if not os.path.isdir(dir_path):
            logger.warning(f"Log directory not found: {dir_path}")
            return []

        search = os.path.join(dir_path, pattern)
        files = sorted(glob.glob(search), key=os.path.getmtime, reverse=True)

        if len(files) > max_files:
            logger.info(f"Found {len(files)} files, collecting newest {max_files}")
            files = files[:max_files]

        collected = []
        for filepath in files:
            basename = os.path.basename(filepath)
            name = f"{name_prefix}{basename}" if name_prefix else basename
            result = self.collect(filepath, name=name)
            if result:
                collected.append(result)

        return collected

    def collect_gtest_xml(self, xml_path, name=None):
        """
        Collect and parse Google Test XML report.

        Parses the XML to extract test results and attaches both the raw XML
        and a human-readable summary to the evidence.

        Args:
            xml_path: Path to GTest XML report.
            name: Display name (default: gtest_report).

        Returns:
            Dict with parsed results, or None if file not found.
        """
        if not os.path.exists(xml_path):
            logger.warning(f"GTest XML not found: {xml_path}")
            return None

        # Collect the raw XML
        self.collect(xml_path, name=name or "gtest_report")

        # Parse and create summary
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            results = {
                "total": int(root.attrib.get("tests", 0)),
                "failures": int(root.attrib.get("failures", 0)),
                "errors": int(root.attrib.get("errors", 0)),
                "time": float(root.attrib.get("time", 0)),
                "test_suites": [],
            }

            summary_lines = []
            summary_lines.append("=" * 60)
            summary_lines.append("GOOGLE TEST RESULTS SUMMARY")
            summary_lines.append("=" * 60)
            summary_lines.append(f"Total : {results['total']}")
            summary_lines.append(f"Passed: {results['total'] - results['failures'] - results['errors']}")
            summary_lines.append(f"Failed: {results['failures']}")
            summary_lines.append(f"Errors: {results['errors']}")
            summary_lines.append(f"Time  : {results['time']:.3f}s")
            summary_lines.append("")

            for testsuite in root.findall(".//testsuite"):
                suite_name = testsuite.attrib.get("name", "unknown")
                suite_tests = int(testsuite.attrib.get("tests", 0))
                suite_failures = int(testsuite.attrib.get("failures", 0))
                suite_time = float(testsuite.attrib.get("time", 0))

                summary_lines.append(f"--- {suite_name} ({suite_tests} tests, {suite_time:.3f}s) ---")

                suite_data = {
                    "name": suite_name,
                    "tests": suite_tests,
                    "failures": suite_failures,
                    "time": suite_time,
                    "cases": [],
                }

                for testcase in testsuite.findall("testcase"):
                    tc_name = testcase.attrib.get("name", "unknown")
                    tc_time = float(testcase.attrib.get("time", 0))
                    failure = testcase.find("failure")
                    status = "FAIL" if failure is not None else "PASS"

                    summary_lines.append(f"  [{status}] {tc_name} ({tc_time:.3f}s)")
                    if failure is not None:
                        fail_msg = failure.attrib.get("message", "")[:200]
                        summary_lines.append(f"         Reason: {fail_msg}")

                    suite_data["cases"].append({
                        "name": tc_name,
                        "status": status,
                        "time": tc_time,
                        "failure": failure.attrib.get("message", "") if failure is not None else None,
                    })

                results["test_suites"].append(suite_data)

            summary_lines.append("")
            summary_lines.append("=" * 60)

            summary_text = "\n".join(summary_lines)
            self.collect_text(summary_text, name=f"{name or 'gtest'}_summary")

            logger.info(
                f"GTest results: {results['total']} total, "
                f"{results['failures']} failures, {results['time']:.3f}s"
            )

            return results

        except ET.ParseError as e:
            logger.error(f"Failed to parse GTest XML: {e}")
            return None

    def collect_from_config(self, tool_config):
        """
        Collect logs based on tool config from settings.yaml.

        Expects config like:
            pkcs11_java:
                log_path_windows: "C:\\logs\\pkcs11.log"
                log_path_linux: "/var/log/pkcs11.log"
                log_dir_windows: "C:\\logs\\pkcs11\\"
                log_dir_linux: "/var/log/pkcs11/"

        Args:
            tool_config: Dict from settings.yaml for a specific tool.

        Returns:
            List of collected file paths.
        """
        import platform
        suffix = "windows" if platform.system() == "Windows" else "linux"
        collected = []

        # Single log file
        log_path = tool_config.get(f"log_path_{suffix}") or tool_config.get("log_path")
        if log_path and os.path.exists(log_path):
            result = self.collect(log_path)
            if result:
                collected.append(result)

        # Log directory
        log_dir = tool_config.get(f"log_dir_{suffix}") or tool_config.get("log_dir")
        log_pattern = tool_config.get("log_pattern", "*.log")
        if log_dir and os.path.isdir(log_dir):
            collected.extend(self.collect_dir(log_dir, pattern=log_pattern))

        # GTest XML report
        gtest_xml = tool_config.get(f"gtest_xml_{suffix}") or tool_config.get("gtest_xml")
        if gtest_xml and os.path.exists(gtest_xml):
            self.collect_gtest_xml(gtest_xml)

        return collected

    def monitor(self, log_path, encoding="utf-8"):
        """
        Return a LogMonitor context manager for real-time log capture.

        Usage:
            with collector.monitor("/path/to/app.log") as mon:
                console.run("some-command")
            evidence.attach_text(mon.captured, "runtime_log")

        Args:
            log_path: Path to the log file to monitor.
            encoding: File encoding (default: utf-8).

        Returns:
            LogMonitor context manager.
        """
        return LogMonitor(log_path, encoding=encoding)

    def summary(self):
        """Return a summary of all collected files."""
        lines = [f"Collected {len(self.collected_files)} log files:"]
        for f in self.collected_files:
            size = os.path.getsize(f) if os.path.exists(f) else 0
            lines.append(f"  - {os.path.basename(f)} ({size:,} bytes)")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _collect_tail(self, log_path, name, lines=500):
        """Collect the last N lines of a large log file."""
        from collections import deque

        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                tail = deque(f, maxlen=lines)

            content = f"[... truncated, showing last {lines} lines ...]\n"
            content += "".join(tail)

            basename = name or os.path.basename(log_path)
            return self.collect_text(content, name=f"{basename}_tail")

        except Exception as e:
            logger.error(f"Failed to tail log file {log_path}: {e}")
            return None

    def _attach_file(self, filepath, name):
        """Attach file to Allure report."""
        try:
            import allure
            ext = os.path.splitext(filepath)[1].lower()
            att_map = {
                ".xml": allure.attachment_type.XML,
                ".json": allure.attachment_type.JSON,
                ".html": allure.attachment_type.HTML,
                ".csv": allure.attachment_type.CSV,
                ".png": allure.attachment_type.PNG,
            }
            att_type = att_map.get(ext, allure.attachment_type.TEXT)

            with open(filepath, "rb") as f:
                allure.attach(f.read(), name=name, attachment_type=att_type)
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Failed to attach {filepath} to Allure: {e}")

    def _attach_text(self, content, name):
        """Attach text content to Allure report."""
        try:
            import allure
            allure.attach(content, name=name, attachment_type=allure.attachment_type.TEXT)
        except ImportError:
            pass


def _safe_filename(name):
    """Convert a name to a safe filename."""
    safe = name.replace(" ", "_").replace("/", "_").replace("\\", "_")
    safe = "".join(c for c in safe if c.isalnum() or c in ("_", "-", "."))
    return safe[:100]  # limit length
