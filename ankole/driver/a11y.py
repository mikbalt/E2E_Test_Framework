"""Accessibility testing via axe-core injection.

Injects axe-core into Playwright pages and runs WCAG compliance scans::

    scanner = A11yScanner()
    report = scanner.scan(web_driver, tags=["wcag2a", "wcag2aa"])
    report.assert_no_violations(impact=["critical", "serious"])
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

AXE_CDN_URL = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js"


@dataclass
class A11yViolation:
    """Single accessibility violation."""

    rule_id: str
    impact: str  # "minor", "moderate", "serious", "critical"
    description: str
    help_url: str
    nodes: list[dict[str, Any]] = field(default_factory=list)

    @property
    def target_selectors(self) -> list[str]:
        """CSS selectors of affected elements."""
        targets = []
        for node in self.nodes:
            for target in node.get("target", []):
                if isinstance(target, list):
                    targets.extend(target)
                else:
                    targets.append(target)
        return targets


@dataclass
class A11yReport:
    """Accessibility scan results."""

    url: str
    violations: list[A11yViolation] = field(default_factory=list)
    passes: int = 0
    inapplicable: int = 0
    incomplete: int = 0

    @property
    def violation_count(self) -> int:
        """Total number of violations."""
        return len(self.violations)

    def violations_by_impact(self, impact: list[str] | None = None) -> list[A11yViolation]:
        """Filter violations by impact level."""
        if not impact:
            return self.violations
        return [v for v in self.violations if v.impact in impact]

    def assert_no_violations(
        self, impact: list[str] | None = None, msg: str | None = None,
    ) -> "A11yReport":
        """Assert no violations at specified impact levels.

        Args:
            impact: Impact levels to check (e.g., ["critical", "serious"]).
                   If None, checks all violations.
            msg: Custom error message.

        Returns:
            self for chaining.
        """
        filtered = self.violations_by_impact(impact)
        if filtered:
            details = "\n".join(
                f"  - [{v.impact.upper()}] {v.rule_id}: {v.description} "
                f"({len(v.nodes)} elements)"
                for v in filtered
            )
            error = msg or (
                f"Found {len(filtered)} accessibility violation(s) "
                f"at {self.url}:\n{details}"
            )
            raise AssertionError(error)
        return self

    def attach_to_allure(self) -> "A11yReport":
        """Attach report to Allure as JSON."""
        try:
            import allure

            report_data = {
                "url": self.url,
                "violations": [
                    {
                        "rule_id": v.rule_id,
                        "impact": v.impact,
                        "description": v.description,
                        "help_url": v.help_url,
                        "elements": v.target_selectors,
                    }
                    for v in self.violations
                ],
                "summary": {
                    "violations": self.violation_count,
                    "passes": self.passes,
                    "inapplicable": self.inapplicable,
                    "incomplete": self.incomplete,
                },
            }
            allure.attach(
                json.dumps(report_data, indent=2),
                name="Accessibility Report",
                attachment_type=allure.attachment_type.JSON,
            )
        except ImportError:
            pass
        return self

    def summary(self) -> str:
        """Human-readable summary."""
        return (
            f"A11y Report for {self.url}: "
            f"{self.violation_count} violations, {self.passes} passes, "
            f"{self.inapplicable} inapplicable, {self.incomplete} incomplete"
        )


class A11yScanner:
    """Accessibility scanner using axe-core via Playwright page.evaluate().

    Injects axe-core from CDN into the page and runs WCAG compliance scans.
    """

    def __init__(
        self,
        axe_cdn_url: str = AXE_CDN_URL,
        default_tags: list[str] | None = None,
        disabled_rules: list[str] | None = None,
    ):
        self.axe_cdn_url = axe_cdn_url
        self.default_tags = default_tags or ["wcag2a", "wcag2aa"]
        self.disabled_rules = disabled_rules or []

    def _inject_axe(self, page: Any) -> None:
        """Inject axe-core library into the page."""
        is_loaded = page.evaluate("typeof window.axe !== 'undefined'")
        if not is_loaded:
            page.evaluate(
                """async (url) => {
                    const script = document.createElement('script');
                    script.src = url;
                    document.head.appendChild(script);
                    await new Promise((resolve, reject) => {
                        script.onload = resolve;
                        script.onerror = reject;
                    });
                }""",
                self.axe_cdn_url,
            )
            logger.debug("axe-core injected into page")

    def scan(
        self,
        driver: Any,
        selector: str | None = None,
        tags: list[str] | None = None,
        disabled_rules: list[str] | None = None,
    ) -> A11yReport:
        """Run accessibility scan on the current page.

        Args:
            driver: WebDriver instance with a `page` property.
            selector: CSS selector to scope the scan (default: entire page).
            tags: WCAG tags to test (e.g., ["wcag2a", "wcag2aa"]).
            disabled_rules: Rule IDs to skip.

        Returns:
            A11yReport with scan results.
        """
        page = driver.page
        self._inject_axe(page)

        effective_tags = tags or self.default_tags
        effective_disabled = disabled_rules or self.disabled_rules

        # Build axe.run options
        options = {"runOnly": {"type": "tag", "values": effective_tags}}
        if effective_disabled:
            options["rules"] = {rule: {"enabled": False} for rule in effective_disabled}

        context = f"'{selector}'" if selector else "document"

        results = page.evaluate(
            f"""async (options) => {{
                const results = await window.axe.run({context}, options);
                return results;
            }}""",
            options,
        )

        # Parse violations
        violations = []
        for v in results.get("violations", []):
            violations.append(A11yViolation(
                rule_id=v["id"],
                impact=v.get("impact", "unknown"),
                description=v.get("description", ""),
                help_url=v.get("helpUrl", ""),
                nodes=v.get("nodes", []),
            ))

        report = A11yReport(
            url=page.url,
            violations=violations,
            passes=len(results.get("passes", [])),
            inapplicable=len(results.get("inapplicable", [])),
            incomplete=len(results.get("incomplete", [])),
        )

        logger.info(report.summary())
        return report
