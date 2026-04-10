"""ZAP Passive Scan tests.

Requires a running OWASP ZAP instance. Set ZAP_API_URL to enable.
"""

import pytest

pytestmark = [pytest.mark.security, pytest.mark.zap]


class TestZAPPassiveScan:
    """Run ZAP passive scan and check for high-risk alerts."""

    def test_no_high_alerts(self, zap_scanner, api_config):
        """Passive scan must not find High-risk alerts."""
        target = api_config.get("base_url", "http://localhost:8000")
        zap_scanner.set_target(target)
        zap_scanner.run_spider(target)
        zap_scanner.run_passive_scan()

        report = zap_scanner.generate_report(scan_type="passive")
        high_alerts = report.alerts_at_or_above("High")
        assert len(high_alerts) == 0, (
            f"Found {len(high_alerts)} High+ alerts:\n"
            + "\n".join(f"  - {a.name} ({a.risk}) at {a.url}" for a in high_alerts)
        )

    def test_generate_report(self, zap_scanner, api_config):
        """Verify report generation works and contains expected fields."""
        target = api_config.get("base_url", "http://localhost:8000")
        zap_scanner.set_target(target)
        report = zap_scanner.generate_report()
        assert report.target_url == target
        assert isinstance(report.summary, str)
