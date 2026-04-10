"""HTTP API driver using httpx.

Wraps httpx with JWT token management, response assertions, and retry logic::

    from ankole.driver.api_driver import APIDriver

    with APIDriver(base_url="http://localhost:8000") as api:
        api.login("admin", "admin123")
        resp = api.get("/api/members")
        resp.assert_status(200)
        members = resp.json()
"""

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
    """Wrapper around httpx.Response with assertion helpers."""

    status_code: int
    headers: dict
    _json: Any = None
    _text: str = ""

    def json(self) -> Any:
        """Return parsed JSON body."""
        return self._json

    @property
    def text(self) -> str:
        """Return response body as text."""
        return self._text

    def assert_status(self, expected: int) -> "APIResponse":
        """Assert response status code."""
        assert self.status_code == expected, (
            f"Expected status {expected}, got {self.status_code}: {self._text[:200]}"
        )
        return self

    def assert_json_key(self, key: str, value: Any = None) -> "APIResponse":
        """Assert JSON response contains a key, optionally with specific value."""
        data = self.json()
        assert key in data, f"Key '{key}' not found in response: {data}"
        if value is not None:
            assert data[key] == value, (
                f"Expected {key}={value!r}, got {data[key]!r}"
            )
        return self

    def assert_json_list_length(self, min_length: int = 0) -> "APIResponse":
        """Assert JSON response is a list with minimum length."""
        data = self.json()
        assert isinstance(data, list), f"Expected list, got {type(data).__name__}"
        assert len(data) >= min_length, (
            f"Expected at least {min_length} items, got {len(data)}"
        )
        return self

    def assert_schema(self, model_class: Any) -> "APIResponse":
        """Validate response JSON against a Pydantic v2 model.

        Args:
            model_class: Pydantic BaseModel subclass.

        Returns:
            self for chaining.

        Raises:
            AssertionError: If validation fails.
        """
        data = self.json()
        try:
            model_class.model_validate(data)
        except Exception as e:
            raise AssertionError(
                f"Schema validation failed for {model_class.__name__}: {e}"
            ) from e
        return self

    def assert_json_schema(self, schema: dict) -> "APIResponse":
        """Validate response JSON against a JSON Schema dict.

        Args:
            schema: JSON Schema dictionary.

        Returns:
            self for chaining.
        """
        import jsonschema

        data = self.json()
        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.ValidationError as e:
            raise AssertionError(
                f"JSON Schema validation failed: {e.message}"
            ) from e
        return self

    def assert_matches_openapi(self, spec_path: str, operation_id: str) -> "APIResponse":
        """Validate response against an OpenAPI specification.

        Loads the OpenAPI spec, finds the operation by ID, extracts the
        response schema for the current status code, and validates.

        Args:
            spec_path: Path to OpenAPI spec file (YAML or JSON).
            operation_id: Operation ID to match.

        Returns:
            self for chaining.
        """
        import json as json_mod
        import yaml
        import jsonschema

        with open(spec_path, "r") as f:
            if spec_path.endswith(".json"):
                spec = json_mod.load(f)
            else:
                spec = yaml.safe_load(f)

        # Find operation by operationId
        response_schema = None
        for path_obj in spec.get("paths", {}).values():
            for method_obj in path_obj.values():
                if isinstance(method_obj, dict) and method_obj.get("operationId") == operation_id:
                    status_str = str(self.status_code)
                    resp_def = method_obj.get("responses", {}).get(status_str, {})
                    content = resp_def.get("content", {})
                    json_content = content.get("application/json", {})
                    response_schema = json_content.get("schema")
                    break
            if response_schema:
                break

        if response_schema is None:
            raise AssertionError(
                f"No schema found for operation '{operation_id}' "
                f"with status {self.status_code} in {spec_path}"
            )

        try:
            jsonschema.validate(instance=self.json(), schema=response_schema)
        except jsonschema.ValidationError as e:
            raise AssertionError(
                f"OpenAPI validation failed for '{operation_id}': {e.message}"
            ) from e
        return self


class APIDriver:
    """HTTP client wrapper with JWT token management.

    Supports context manager protocol for automatic cleanup.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
        token_endpoint: str = "/api/auth/login",
        token_field: str = "access_token",
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.token_endpoint = token_endpoint
        self.token_field = token_field

        self._client = None
        self._token: str | None = None

    def start(self) -> "APIDriver":
        """Create httpx client."""
        import httpx

        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
        )
        logger.info(f"APIDriver started: {self.base_url}")
        return self

    def close(self) -> None:
        """Close httpx client."""
        if self._client:
            self._client.close()
        self._token = None
        logger.info("APIDriver closed")

    def __enter__(self) -> "APIDriver":
        return self.start()

    def __exit__(self, *args) -> None:
        self.close()

    # -- Auth -----------------------------------------------------------------

    def login(self, username: str, password: str) -> APIResponse:
        """Authenticate and store JWT token."""
        resp = self.post(
            self.token_endpoint,
            json={"username": username, "password": password},
        )
        if resp.status_code == 200:
            data = resp.json()
            self._token = data.get(self.token_field)
            logger.info(f"Logged in as: {username}")
        return resp

    def logout(self) -> None:
        """Clear stored token."""
        self._token = None
        logger.info("Logged out (token cleared)")

    @property
    def is_authenticated(self) -> bool:
        """Check if a token is stored."""
        return self._token is not None

    # -- HTTP methods ---------------------------------------------------------

    def _headers(self) -> dict:
        """Build request headers with auth token if available."""
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _wrap_response(self, resp) -> APIResponse:
        """Convert httpx.Response to APIResponse."""
        try:
            json_data = resp.json()
        except Exception:
            json_data = None
        return APIResponse(
            status_code=resp.status_code,
            headers=dict(resp.headers),
            _json=json_data,
            _text=resp.text,
        )

    def get(self, path: str, **kwargs) -> APIResponse:
        """Send GET request."""
        kwargs.setdefault("headers", self._headers())
        resp = self._client.get(path, **kwargs)
        logger.debug(f"GET {path} -> {resp.status_code}")
        return self._wrap_response(resp)

    def post(self, path: str, **kwargs) -> APIResponse:
        """Send POST request."""
        kwargs.setdefault("headers", self._headers())
        resp = self._client.post(path, **kwargs)
        logger.debug(f"POST {path} -> {resp.status_code}")
        return self._wrap_response(resp)

    def put(self, path: str, **kwargs) -> APIResponse:
        """Send PUT request."""
        kwargs.setdefault("headers", self._headers())
        resp = self._client.put(path, **kwargs)
        logger.debug(f"PUT {path} -> {resp.status_code}")
        return self._wrap_response(resp)

    def patch(self, path: str, **kwargs) -> APIResponse:
        """Send PATCH request."""
        kwargs.setdefault("headers", self._headers())
        resp = self._client.patch(path, **kwargs)
        logger.debug(f"PATCH {path} -> {resp.status_code}")
        return self._wrap_response(resp)

    def delete(self, path: str, **kwargs) -> APIResponse:
        """Send DELETE request."""
        kwargs.setdefault("headers", self._headers())
        resp = self._client.delete(path, **kwargs)
        logger.debug(f"DELETE {path} -> {resp.status_code}")
        return self._wrap_response(resp)
