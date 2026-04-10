"""ZAP Active Scan tests.

Requires a running OWASP ZAP instance. Marked slow — active scans can take minutes.
"""

import pytest

pytestmark = [pytest.mark.security, pytest.mark.zap, pytest.mark.slow]


class TestZAPActiveScan:
    """Run ZAP active scan and check alerts against risk threshold."""

    def test_no_alerts_above_threshold(self, zap_scanner, api_config, security_config):
        """Active scan alerts must not exceed configured risk threshold."""
        target = api_config.get("base_url", "http://localhost:8000")
        threshold = security_config.get("zap", {}).get("risk_threshold", "Medium")

        zap_scanner.set_target(target)
        zap_scanner.run_spider(target)
        zap_scanner.run_active_scan(target)

        report = zap_scanner.generate_report(scan_type="active")
        critical_alerts = report.alerts_at_or_above(threshold)
        assert len(critical_alerts) == 0, (
            f"Found {len(critical_alerts)} alerts at or above {threshold}:\n"
            + "\n".join(
                f"  - {a.name} ({a.risk}) at {a.url}" for a in critical_alerts
            )
        )
