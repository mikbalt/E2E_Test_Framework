"""Security testing payload collections.

Common attack payloads for OWASP Top 10 testing. These payloads are intentionally
benign — they test whether the application properly rejects or sanitizes input,
not whether exploits succeed.
"""

SQL_INJECTION_PAYLOADS = [
    "' OR '1'='1",
    "' OR '1'='1' --",
    "'; DROP TABLE users; --",
    "' UNION SELECT NULL, NULL, NULL --",
    "1' AND 1=1 --",
    "admin'--",
    "' OR 1=1#",
    "1; WAITFOR DELAY '0:0:5'--",
]

XSS_PAYLOADS = [
    "<script>alert('xss')</script>",
    "<img src=x onerror=alert('xss')>",
    "<svg onload=alert('xss')>",
    "javascript:alert('xss')",
    "<body onload=alert('xss')>",
    "'\"><script>alert('xss')</script>",
    "<iframe src='javascript:alert(1)'>",
    "<input onfocus=alert('xss') autofocus>",
]

COMMAND_INJECTION_PAYLOADS = [
    "; ls -la",
    "| cat /etc/passwd",
    "$(whoami)",
    "`id`",
    "&& echo vulnerable",
    "|| echo vulnerable",
]

PATH_TRAVERSAL_PAYLOADS = [
    "../../../etc/passwd",
    "..\\..\\..\\windows\\system32\\config\\sam",
    "....//....//....//etc/passwd",
    "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
]

REQUIRED_SECURITY_HEADERS = [
    "X-Content-Type-Options",
    "X-Frame-Options",
    "X-XSS-Protection",
    "Strict-Transport-Security",
    "Content-Security-Policy",
]

DEFAULT_CREDENTIALS = [
    ("admin", "admin"),
    ("admin", "password"),
    ("root", "root"),
    ("test", "test"),
    ("admin", "123456"),
    ("user", "user"),
]
