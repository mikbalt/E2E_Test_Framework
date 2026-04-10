"""Test Data Factory — Faker-powered factories with automatic cleanup.

Provides reusable factories for generating test data with LIFO cleanup
to ensure test isolation::

    def test_member_crud(data_factory, api_driver):
        member = data_factory.members.create_via_api(api_driver)
        # ... test logic ...
        # cleanup happens automatically via CleanupTracker
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


class CleanupTracker:
    """LIFO stack that tracks created resources for automatic cleanup.

    Resources are cleaned up in reverse creation order to respect
    dependency chains (e.g., delete member before deleting project).
    """

    def __init__(self):
        self._stack: list[tuple[str, Any, Any]] = []  # (resource_type, resource_id, callback)

    def push(self, resource_type: str, resource_id: Any, callback: Any) -> None:
        """Register a resource for cleanup."""
        self._stack.append((resource_type, resource_id, callback))
        logger.debug(f"Cleanup registered: {resource_type} #{resource_id}")

    def cleanup_all(self) -> list[str]:
        """Execute all cleanup callbacks in LIFO order. Returns list of errors."""
        errors = []
        while self._stack:
            resource_type, resource_id, callback = self._stack.pop()
            try:
                callback()
                logger.info(f"Cleaned up: {resource_type} #{resource_id}")
            except Exception as e:
                msg = f"Failed to cleanup {resource_type} #{resource_id}: {e}"
                logger.warning(msg)
                errors.append(msg)
        return errors

    @property
    def pending_count(self) -> int:
        """Number of resources pending cleanup."""
        return len(self._stack)


@runtime_checkable
class CleanupBackend(Protocol):
    """Protocol for cleanup strategies."""

    def delete(self, resource_type: str, resource_id: Any) -> None: ...


class APICleanupBackend:
    """Cleanup resources via API DELETE calls."""

    ENDPOINTS = {
        "member": "/api/members/{id}",
        "project": "/api/projects/{id}",
        "role": "/api/roles/{id}",
    }

    def __init__(self, api_driver: Any):
        self._api = api_driver

    def delete(self, resource_type: str, resource_id: Any) -> None:
        """Delete a resource via API."""
        endpoint_template = self.ENDPOINTS.get(resource_type)
        if not endpoint_template:
            raise ValueError(f"Unknown resource type: {resource_type}")
        endpoint = endpoint_template.format(id=resource_id)
        resp = self._api.delete(endpoint)
        if resp.status_code not in (200, 204, 404):
            raise RuntimeError(
                f"Cleanup DELETE {endpoint} returned {resp.status_code}"
            )


class DBCleanupBackend:
    """Cleanup resources via direct database DELETE."""

    TABLES = {
        "member": "members",
        "project": "projects",
    }

    def __init__(self, db_driver: Any):
        self._db = db_driver

    def delete(self, resource_type: str, resource_id: Any) -> None:
        """Delete a resource via DB."""
        table = self.TABLES.get(resource_type)
        if not table:
            raise ValueError(f"Unknown resource type: {resource_type}")
        self._db.execute(f"DELETE FROM {table} WHERE id = %s", (resource_id,))


class MemberFactory:
    """Factory for generating test member data."""

    def __init__(self, cleanup_tracker: CleanupTracker | None = None):
        self._tracker = cleanup_tracker
        self._counter = 0

    def build(self, **overrides) -> dict[str, Any]:
        """Build a member dict without creating it (in-memory only).

        Args:
            **overrides: Fields to override in the generated data.

        Returns:
            Dict with member fields.
        """
        from faker import Faker

        fake = Faker()
        self._counter += 1
        data = {
            "username": f"test_{fake.user_name()}_{self._counter}",
            "email": fake.email(),
            "full_name": fake.name(),
            "role": "member",
            "password": "Test@12345",
        }
        data.update(overrides)
        return data

    def create_via_api(self, api_driver: Any, **overrides) -> dict[str, Any]:
        """Create a member via API and register for cleanup.

        Args:
            api_driver: APIDriver instance (must be authenticated).
            **overrides: Fields to override.

        Returns:
            API response JSON (created member data).
        """
        payload = self.build(**overrides)
        resp = api_driver.post("/api/members", json=payload)
        resp.assert_status(201)
        created = resp.json()

        if self._tracker:
            resource_id = created.get("id")
            self._tracker.push(
                "member",
                resource_id,
                lambda rid=resource_id: api_driver.delete(f"/api/members/{rid}"),
            )

        logger.info(f"Created member via API: {created.get('username', payload['username'])}")
        return created


class ProjectFactory:
    """Factory for generating test project data."""

    def __init__(self, cleanup_tracker: CleanupTracker | None = None):
        self._tracker = cleanup_tracker
        self._counter = 0

    def build(self, **overrides) -> dict[str, Any]:
        """Build a project dict without creating it (in-memory only)."""
        from faker import Faker

        fake = Faker()
        self._counter += 1
        data = {
            "name": f"Test Project {fake.bs().title()} {self._counter}",
            "description": fake.paragraph(nb_sentences=2),
            "status": "draft",
        }
        data.update(overrides)
        return data

    def create_via_api(self, api_driver: Any, **overrides) -> dict[str, Any]:
        """Create a project via API and register for cleanup."""
        payload = self.build(**overrides)
        resp = api_driver.post("/api/projects", json=payload)
        resp.assert_status(201)
        created = resp.json()

        if self._tracker:
            resource_id = created.get("id")
            self._tracker.push(
                "project",
                resource_id,
                lambda rid=resource_id: api_driver.delete(f"/api/projects/{rid}"),
            )

        logger.info(f"Created project via API: {created.get('name', payload['name'])}")
        return created


class RoleFactory:
    """Factory for generating test role data."""

    def __init__(self, cleanup_tracker: CleanupTracker | None = None):
        self._tracker = cleanup_tracker
        self._counter = 0

    def build(self, **overrides) -> dict[str, Any]:
        """Build a role dict without creating it (in-memory only)."""
        from faker import Faker

        fake = Faker()
        self._counter += 1
        data = {
            "name": f"Test Role {fake.job().title()} {self._counter}",
            "description": fake.sentence(),
        }
        data.update(overrides)
        return data

    def create_via_api(self, api_driver: Any, **overrides) -> dict[str, Any]:
        """Create a role via API and register for cleanup."""
        payload = self.build(**overrides)
        resp = api_driver.post("/api/roles", json=payload)
        resp.assert_status(201)
        created = resp.json()

        if self._tracker:
            resource_id = created.get("id")
            self._tracker.push(
                "role",
                resource_id,
                lambda rid=resource_id: api_driver.delete(f"/api/roles/{rid}"),
            )

        logger.info(f"Created role via API: {created.get('name', payload['name'])}")
        return created


class DataFactory:
    """Aggregates all sub-factories with shared cleanup.

    Usage::

        factory = DataFactory()
        member = factory.members.build(role="admin")
        project = factory.projects.create_via_api(api_driver)
        factory.cleanup_all()  # Cleans up in reverse order
    """

    def __init__(self):
        self.tracker = CleanupTracker()
        self.members = MemberFactory(cleanup_tracker=self.tracker)
        self.projects = ProjectFactory(cleanup_tracker=self.tracker)
        self.roles = RoleFactory(cleanup_tracker=self.tracker)

    def cleanup_all(self) -> list[str]:
        """Clean up all created resources."""
        return self.tracker.cleanup_all()
