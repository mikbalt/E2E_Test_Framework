"""A07:2021 - Cross-Site Scripting (XSS).

Tests for reflected and stored XSS via API inputs.
"""

import pytest

from tests.security.payloads import XSS_PAYLOADS

pytestmark = [pytest.mark.security, pytest.mark.owasp]


class TestXSSInMemberFields:
    """XSS via member creation fields."""

    @pytest.mark.parametrize("payload", XSS_PAYLOADS[:4])
    def test_xss_in_username(self, authed_api, payload):
        """XSS payloads in username must be rejected or escaped."""
        resp = authed_api.post(
            "/api/members",
            json={
                "username": payload,
                "email": "xss@test.com",
                "role": "viewer",
            },
        )
        if resp.status_code in (201, 200):
            data = resp.json()
            stored_name = data.get("username", "")
            # Must be escaped — raw script tags must not appear
            assert "<script>" not in stored_name
            # Cleanup
            member_id = data.get("id")
            if member_id:
                authed_api.delete(f"/api/members/{member_id}")
        else:
            # Rejection is also acceptable
            assert resp.status_code in (400, 422)


class TestXSSInProjectDescription:
    """XSS via project description field."""

    def test_xss_in_project_description(self, authed_api):
        """XSS payload in project description must be sanitized."""
        payload = "<script>alert('xss')</script>"
        resp = authed_api.post(
            "/api/projects",
            json={
                "name": "XSS Test Project",
                "description": payload,
            },
        )
        if resp.status_code in (200, 201):
            data = resp.json()
            stored_desc = data.get("description", "")
            assert "<script>" not in stored_desc
            # Cleanup
            project_id = data.get("id")
            if project_id:
                authed_api.delete(f"/api/projects/{project_id}")
        else:
            assert resp.status_code in (400, 422)


class TestContentTypeValidation:
    """Verify API enforces Content-Type: application/json."""

    def test_rejects_html_content_type(self, authed_api):
        """API should reject requests with text/html content type."""
        client = authed_api._client
        resp = client.post(
            "/api/members",
            content=b"<html><body>test</body></html>",
            headers={
                "Content-Type": "text/html",
                "Authorization": f"Bearer {authed_api._token}",
            },
        )
        assert resp.status_code in (400, 415, 422)
