"""Solution: API Schema Validation."""

import pytest
from pydantic import BaseModel

from ankole.driver.api_driver import APIResponse


class MemberResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str


@pytest.mark.api
class TestSchemaValidationSolution:
    def test_member_pydantic(self, authenticated_api):
        resp = authenticated_api.get("/api/members")
        members = resp.assert_status(200).json()
        if members:
            single = APIResponse(status_code=200, headers={}, _json=members[0])
            single.assert_schema(MemberResponse)
