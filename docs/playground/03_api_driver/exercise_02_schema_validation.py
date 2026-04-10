"""Exercise: API Schema Validation.

TODO: Validate API responses against Pydantic and JSON Schema.
"""

import pytest
from pydantic import BaseModel


class MemberResponse(BaseModel):
    """Pydantic model for a member response."""
    id: int
    username: str
    email: str
    full_name: str
    role: str


MEMBER_JSON_SCHEMA = {
    "type": "object",
    "required": ["id", "username", "email"],
    "properties": {
        "id": {"type": "integer"},
        "username": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "full_name": {"type": "string"},
        "role": {"type": "string"},
    },
}


@pytest.mark.api
class TestSchemaValidation:
    """Schema validation exercises."""

    def test_member_pydantic_schema(self, authenticated_api):
        """TODO: Validate a member response with Pydantic."""
        resp = authenticated_api.get("/api/members")
        resp.assert_status(200)
        members = resp.json()
        if members:
            from ankole.driver.api_driver import APIResponse
            single = APIResponse(
                status_code=200, headers={},
                _json=members[0],
            )
            single.assert_schema(MemberResponse)

    def test_member_json_schema(self, authenticated_api):
        """TODO: Validate a member response with JSON Schema."""
        resp = authenticated_api.get("/api/members")
        resp.assert_status(200)
        members = resp.json()
        if members:
            from ankole.driver.api_driver import APIResponse
            single = APIResponse(
                status_code=200, headers={},
                _json=members[0],
            )
            single.assert_json_schema(MEMBER_JSON_SCHEMA)
