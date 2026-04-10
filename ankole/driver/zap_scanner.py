"""OWASP ZAP scanner driver.

Wraps the ZAP API (zapv2) for passive and active security scanning::

    from ankole.driver.zap_scanner import ZAPScanner

    with ZAPScanner(api_url="http://localhost:8080", api_key="key") as zap:
        zap.set_target("http://target:8000")
        zap.run_spider("http://target:8000")
        zap.run_passive_scan()
        report = zap.generate_report()
        print(report.summary)
"""

import logging
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

RISK_LEVELS = {"Informational": 0, "Low": 1, "Medium": 2, "High": 3}


@dataclass
class ZAPAlert:
    """Single ZAP alert."""

    alert_ref: str
    name: str
    risk: str
    confidence: str
    url: str
    cwe_id: int = 0
    description: str = ""
    solution: str = ""

    @property
    def risk_level(self) -> int:
        return RISK_LEVELS.get(self.risk, 0)


@dataclass
class ZAPScanReport:
    """Collection of ZAP alerts with filtering."""

    target_url: str
    alerts: list[ZAPAlert] = field(default_factory=list)
    scan_type: str = "passive"

    def alerts_at_or_above(self, risk: str) -> list[ZAPAlert]:
        """Return alerts at or above the given risk level."""
        threshold = RISK_LEVELS.get(risk, 0)
        return [a for a in self.alerts if a.risk_level >= threshold]

    @property
    def summary(self) -> str:
        """Human-readable summary."""
        counts = {}
        for alert in self.alerts:
            counts[alert.risk] = counts.get(alert.risk, 0) + 1
        parts = [f"{k}: {v}" for k, v in sorted(counts.items())]
        return (
            f"ZAP {self.scan_type} scan on {self.target_url} — "
            f"{len(self.alerts)} alerts ({', '.join(parts) or 'none'})"
        )


class ZAPScanner:
    """OWASP ZAP API wrapper for security scanning.

    Implements SecurityScannerProtocol from ankole.driver.base.
    """

    def __init__(
        self,
        api_url: str = "http://localhost:8080",
        api_key: str = "",
    ):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self._zap = None
        self._target: str | None = None

    def start(self) -> "ZAPScanner":
        """Connect to ZAP API."""
        from zapv2 import ZAPv2

        self._zap = ZAPv2(
            apikey=self.api_key,
            proxies={"http": self.api_url, "https": self.api_url},
        )
        logger.info(f"ZAPScanner connected: {self.api_url}")
        return self

    def close(self) -> None:
        """Cleanup ZAP connection."""
        self._zap = None
        logger.info("ZAPScanner closed")

    def __enter__(self) -> "ZAPScanner":
        return self.start()

    def __exit__(self, *args) -> None:
        self.close()

    def set_target(self, url: str) -> None:
        """Set the target URL for scanning."""
        self._target = url
        logger.info(f"ZAP target set: {url}")

    def configure_auth(self, token: str, header: str = "Authorization") -> None:
        """Configure JWT authentication via replacer rule."""
        self._zap.replacer.add_rule(
            description="Auth Header",
            enabled=True,
            matchtype="REQ_HEADER",
            matchregex=False,
            matchstring=header,
            replacement=f"Bearer {token}",
        )
        logger.info("ZAP auth configured via replacer")

    def run_spider(self, url: str | None = None, max_duration: int = 60) -> int:
        """Run ZAP spider on target URL. Returns number of URLs found."""
        target = url or self._target
        if not target:
            raise ValueError("No target URL set")

        scan_id = self._zap.spider.scan(target)
        logger.info(f"Spider started (id={scan_id}) on {target}")

        start = time.time()
        while int(self._zap.spider.status(scan_id)) < 100:
            if time.time() - start > max_duration:
                self._zap.spider.stop(scan_id)
                logger.warning("Spider timed out")
                break
            time.sleep(2)

        results = self._zap.spider.results(scan_id)
        logger.info(f"Spider complete: {len(results)} URLs found")
        return len(results)

    def run_passive_scan(self, max_wait: int = 30) -> int:
        """Wait for passive scan to complete. Returns number of records."""
        start = time.time()
        while int(self._zap.pscan.records_to_scan) > 0:
            if time.time() - start > max_wait:
                logger.warning("Passive scan wait timed out")
                break
            time.sleep(1)

        count = int(self._zap.pscan.records_to_scan)
        logger.info(f"Passive scan complete ({count} records remaining)")
        return count

    def run_active_scan(self, url: str | None = None, max_duration: int = 300) -> int:
        """Run ZAP active scan. Returns scan ID."""
        target = url or self._target
        if not target:
            raise ValueError("No target URL set")

        scan_id = self._zap.ascan.scan(target)
        logger.info(f"Active scan started (id={scan_id}) on {target}")

        start = time.time()
        while int(self._zap.ascan.status(scan_id)) < 100:
            if time.time() - start > max_duration:
                self._zap.ascan.stop(scan_id)
                logger.warning("Active scan timed out")
                break
            time.sleep(5)

        logger.info("Active scan complete")
        return int(scan_id)

    def get_alerts(self, base_url: str | None = None) -> list[ZAPAlert]:
        """Retrieve all alerts, optionally filtered by base URL."""
        target = base_url or self._target or ""
        raw_alerts = self._zap.core.alerts(baseurl=target)

        alerts = []
        for raw in raw_alerts:
            alerts.append(
                ZAPAlert(
                    alert_ref=raw.get("alertRef", ""),
                    name=raw.get("name", ""),
                    risk=raw.get("risk", "Informational"),
                    confidence=raw.get("confidence", ""),
                    url=raw.get("url", ""),
                    cwe_id=int(raw.get("cweid", 0)),
                    description=raw.get("description", ""),
                    solution=raw.get("solution", ""),
                )
            )
        return alerts

    def generate_report(self, scan_type: str = "passive") -> ZAPScanReport:
        """Generate a scan report with all current alerts."""
        alerts = self.get_alerts()
        return ZAPScanReport(
            target_url=self._target or "",
            alerts=alerts,
            scan_type=scan_type,
        )
