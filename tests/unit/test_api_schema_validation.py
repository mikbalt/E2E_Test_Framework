"""Unit tests for API Schema Validation (APIResponse extensions)."""

import pytest

from ankole.driver.api_driver import APIResponse


class TestAssertSchema:
    """Tests for Pydantic v2 schema validation."""

    def test_assert_schema_passes(self):
        from pydantic import BaseModel

        class MemberSchema(BaseModel):
            id: int
            username: str

        resp = APIResponse(
            status_code=200,
            headers={},
            _json={"id": 1, "username": "admin"},
        )
        result = resp.assert_schema(MemberSchema)
        assert result is resp  # chainable

    def test_assert_schema_fails(self):
        from pydantic import BaseModel

        class MemberSchema(BaseModel):
            id: int
            username: str

        resp = APIResponse(
            status_code=200,
            headers={},
            _json={"id": "not_an_int"},  # missing username, bad id type
        )
        with pytest.raises(AssertionError, match="Schema validation failed"):
            resp.assert_schema(MemberSchema)


class TestAssertJsonSchema:
    """Tests for JSON Schema validation."""

    def test_assert_json_schema_passes(self):
        schema = {
            "type": "object",
            "required": ["id", "name"],
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
            },
        }
        resp = APIResponse(
            status_code=200,
            headers={},
            _json={"id": 1, "name": "Project Alpha"},
        )
        result = resp.assert_json_schema(schema)
        assert result is resp

    def test_assert_json_schema_fails(self):
        schema = {
            "type": "object",
            "required": ["id"],
            "properties": {"id": {"type": "integer"}},
        }
        resp = APIResponse(
            status_code=200,
            headers={},
            _json={"id": "not_integer"},
        )
        with pytest.raises(AssertionError, match="JSON Schema validation failed"):
            resp.assert_json_schema(schema)


class TestAssertMatchesOpenapi:
    """Tests for OpenAPI spec validation."""

    def test_assert_matches_openapi_passes(self, tmp_path):
        import yaml

        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/api/members": {
                    "get": {
                        "operationId": "listMembers",
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "integer"},
                                                },
                                            },
                                        }
                                    }
                                }
                            }
                        },
                    }
                }
            },
        }
        spec_path = tmp_path / "openapi.yaml"
        spec_path.write_text(yaml.dump(spec))

        resp = APIResponse(
            status_code=200,
            headers={},
            _json=[{"id": 1}, {"id": 2}],
        )
        result = resp.assert_matches_openapi(str(spec_path), "listMembers")
        assert result is resp

    def test_assert_matches_openapi_fails_no_operation(self, tmp_path):
        import yaml

        spec = {"openapi": "3.0.0", "paths": {}}
        spec_path = tmp_path / "openapi.yaml"
        spec_path.write_text(yaml.dump(spec))

        resp = APIResponse(status_code=200, headers={}, _json={})
        with pytest.raises(AssertionError, match="No schema found"):
            resp.assert_matches_openapi(str(spec_path), "nonExistent")
