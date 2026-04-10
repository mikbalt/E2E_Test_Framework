"""
Loki Log Collector - Query Loki for remote VM logs and attach as test evidence.

Multiple VMs (Windows + Linux) generate logs during E2E tests. Loki already
collects all logs via Promtail/agents. After each test, this module queries
the Loki API for logs within the test's time range, saves them as .log files,
zips them, and attaches the archive to the Allure report.

Usage:
    collector = LokiLogCollector(
        loki_url="http://10.88.1.14:3100",
        queries=[
            {"label": "e_admin_app", "query": '{job="e_admin"}'},
            {"label": "hsm_backend", "query": '{job="hsm_backend"}'},
        ],
    )

    # Collect logs for a time range (typically test start → test end)
    collector.collect(
        start_time=test_start,
        end_time=test_end,
        evidence=evidence,
        test_name="test_key_ceremony",
    )
"""

import datetime
import logging
import os
import zipfile

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

logger = logging.getLogger(__name__)


class LokiLogCollector:
    """
    Query Loki HTTP API and collect remote logs as zipped test evidence.

    Each configured query is executed against Loki's query_range endpoint.
    Results are saved as individual .log files, bundled into a zip archive,
    and attached to the Allure report.
    """

    def __init__(self, loki_url, queries=None, default_limit=5000, timeout=30):
        """
        Args:
            loki_url: Base URL of the Loki instance (e.g. "http://10.88.1.14:3100").
            queries: List of dicts with "label" and "query" keys.
                     Each query is a LogQL expression (e.g. '{job="e_admin"}').
            default_limit: Maximum number of log lines per query (default: 5000).
            timeout: HTTP request timeout in seconds (default: 30).
        """
        if not _HAS_REQUESTS:
            raise ImportError(
                "LokiLogCollector requires 'requests'. Install: pip install requests"
            )
        self.loki_url = loki_url.rstrip("/") if loki_url else ""
        self.queries = queries or []
        self.default_limit = default_limit
        self.timeout = timeout

    def collect(self, start_time, end_time, evidence, test_name="test"):
        """
        Query Loki for all configured log streams and save as zipped evidence.

        Args:
            start_time: Start of the time range (datetime or epoch float).
            end_time: End of the time range (datetime or epoch float).
            evidence: Evidence instance for attaching results.
            test_name: Test name used in the zip filename.

        Returns:
            Path to the zip file, or None if no logs were collected.
        """
        if not self.loki_url:
            logger.debug("Loki URL not configured, skipping remote log collection")
            return None

        if not self.queries:
            logger.debug("No Loki queries configured, skipping remote log collection")
            return None

        start_ns = self._to_nanoseconds(start_time)
        end_ns = self._to_nanoseconds(end_time)

        log_files = []
        for q in self.queries:
            label = q.get("label", "unknown")
            query = q.get("query", "")
            limit = q.get("limit", self.default_limit)

            if not query:
                continue

            lines = self._query_loki(query, start_ns, end_ns, limit)
            if lines:
                log_files.append((label, lines))
                logger.info(f"Loki [{label}]: collected {len(lines)} log lines")
            else:
                logger.debug(f"Loki [{label}]: no logs found")

        if not log_files:
            logger.info("No remote logs collected from Loki")
            return None

        return self._save_and_attach(log_files, evidence, test_name)

    def _query_loki(self, query, start_ns, end_ns, limit):
        """
        Query Loki with automatic pagination.

        Loki servers enforce a max entries per query (typically 5000).
        This method paginates by advancing the start time past the last
        received entry until all logs are fetched or ``limit`` is reached.

        Args:
            query: LogQL query string.
            start_ns: Start time in nanoseconds.
            end_ns: End time in nanoseconds.
            limit: Max total number of log entries to collect.

        Returns:
            List of formatted log line strings, or empty list on failure.
        """
        all_formatted = []
        cursor_ns = start_ns
        batch_size = min(limit, self.default_limit)
        max_pages = 50  # Safety limit to prevent infinite loops

        for _ in range(max_pages):
            remaining = limit - len(all_formatted)
            if remaining <= 0:
                break
            fetch = min(batch_size, remaining)

            entries, last_ts = self._fetch_page(query, cursor_ns, end_ns, fetch)
            if not entries:
                break

            all_formatted.extend(entries)

            # Advance cursor past the last timestamp (+1 ns to avoid duplicates)
            if last_ts is not None:
                cursor_ns = last_ts + 1
            else:
                break

            # If we got fewer than requested, we've exhausted this range
            if len(entries) < fetch:
                break

        return all_formatted

    def _fetch_page(self, query, start_ns, end_ns, limit):
        """
        Execute a single query_range request against Loki.

        Returns:
            Tuple of (formatted_lines, last_timestamp_ns).
            On failure returns ([], None).
        """
        url = f"{self.loki_url}/loki/api/v1/query_range"
        params = {
            "query": query,
            "start": str(start_ns),
            "end": str(end_ns),
            "limit": limit,
            "direction": "forward",
        }

        try:
            resp = requests.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Loki connection failed: {e}")
            return [], None
        except requests.exceptions.Timeout:
            logger.warning(f"Loki query timed out after {self.timeout}s")
            return [], None
        except requests.exceptions.HTTPError as e:
            logger.warning(f"Loki HTTP error: {e}")
            return [], None
        except Exception as e:
            logger.warning(f"Loki query failed: {e}")
            return [], None

        return self._parse_response(data)

    def _parse_response(self, data):
        """
        Parse Loki query_range JSON response into a flat list of log lines.

        Loki returns streams, each containing a list of [timestamp, line] values.
        We flatten all streams, sort by timestamp, and format as readable lines.

        Args:
            data: Parsed JSON response from Loki.

        Returns:
            Tuple of (formatted_lines, last_timestamp_ns).
            Returns ([], None) if no entries found.
        """
        if data.get("status") != "success":
            logger.warning(f"Loki query returned status: {data.get('status')}")
            return [], None

        streams = data.get("data", {}).get("result", [])

        if not streams:
            return [], None

        all_entries = []
        for stream in streams:
            labels = stream.get("stream", {})
            # Build a short label prefix from stream labels
            host = labels.get("hostname", labels.get("host", labels.get("host_id", labels.get("instance", ""))))
            job = labels.get("job", "")
            prefix = f"[{job}]" if job else ""
            if host:
                prefix = f"[{job}@{host}]" if job else f"[{host}]"

            # "values" for streams result type, or extract from matrix
            values = stream.get("values", [])
            for ts_ns, line in values:
                all_entries.append((int(ts_ns), prefix, line))

        if not all_entries:
            return [], None

        # Sort by timestamp
        all_entries.sort(key=lambda x: x[0])
        last_ts = all_entries[-1][0]

        # Format lines
        formatted = []
        for ts_ns, prefix, line in all_entries:
            dt = datetime.datetime.fromtimestamp(int(ts_ns) / 1e9)
            ts_str = dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            if prefix:
                formatted.append(f"{ts_str} {prefix} {line}")
            else:
                formatted.append(f"{ts_str} | {line}")

        return formatted, last_ts

    def _save_and_attach(self, log_files, evidence, test_name):
        """
        Save collected log lines as .log files, zip them for Kiwi,
        and attach each log as plain text to Allure individually.

        Args:
            log_files: List of (label, lines) tuples.
            evidence: Evidence instance.
            test_name: Test name for the zip filename.

        Returns:
            Path to the created zip file.
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_name = f"RemoteLogs_{test_name}_{timestamp}.zip"
        zip_path = os.path.join(evidence.evidence_dir, zip_name)

        # Merge all streams into a single sorted timeline
        all_lines = []
        for _, lines in log_files:
            all_lines.extend(lines)
        all_lines.sort()  # Lexicographic sort works — lines start with YYYY-MM-DD HH:MM:SS.mmm

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for label, lines in log_files:
                filename = f"{label}.log"
                content = "\n".join(lines)
                zf.writestr(filename, content)
            zf.writestr("aggregated_timeline.log", "\n".join(all_lines))

        total_lines = sum(len(lines) for _, lines in log_files)
        logger.info(
            f"Remote logs saved: {zip_path} "
            f"({len(log_files)} streams, {total_lines} total lines)"
        )

        # Attach each log stream as individual plain text to Allure
        try:
            import allure

            for label, lines in log_files:
                content = "\n".join(lines)
                allure.attach(
                    content,
                    name=f"RemoteLog_{label}",
                    attachment_type=allure.attachment_type.TEXT,
                    extension="log",
                )
            allure.attach(
                "\n".join(all_lines),
                name="RemoteLog_aggregated_timeline",
                attachment_type=allure.attachment_type.TEXT,
                extension="log",
            )
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Failed to attach remote logs to Allure: {e}")

        return zip_path

    @staticmethod
    def _to_nanoseconds(t):
        """
        Convert a time value to nanoseconds (Loki's native timestamp format).

        Args:
            t: datetime object, epoch float (seconds), or epoch int (nanoseconds).

        Returns:
            Integer nanosecond timestamp.
        """
        if isinstance(t, datetime.datetime):
            return int(t.timestamp() * 1e9)
        if isinstance(t, (int, float)):
            # If value is small enough to be epoch seconds, convert
            if t < 1e12:
                return int(t * 1e9)
            # Already nanoseconds
            return int(t)
        raise ValueError(f"Unsupported time type: {type(t)}")
