"""Unit tests for the Test Data Factory module."""

import pytest

from ankole.testing.data_factory import (
    CleanupTracker,
    DataFactory,
    MemberFactory,
    ProjectFactory,
)


class TestCleanupTracker:
    """Tests for CleanupTracker."""

    def test_push_and_cleanup(self):
        tracker = CleanupTracker()
        cleaned = []
        tracker.push("member", 1, lambda: cleaned.append("member_1"))
        tracker.push("project", 2, lambda: cleaned.append("project_2"))

        assert tracker.pending_count == 2
        tracker.cleanup_all()
        assert tracker.pending_count == 0
        # LIFO order: project_2 first, then member_1
        assert cleaned == ["project_2", "member_1"]

    def test_cleanup_handles_errors(self):
        tracker = CleanupTracker()
        tracker.push("ok", 1, lambda: None)
        tracker.push("fail", 2, lambda: (_ for _ in ()).throw(RuntimeError("boom")))
        tracker.push("ok2", 3, lambda: None)

        errors = tracker.cleanup_all()
        # The failing callback should produce one error
        assert len(errors) == 1
        assert "boom" in errors[0]
        assert tracker.pending_count == 0

    def test_empty_cleanup(self):
        tracker = CleanupTracker()
        errors = tracker.cleanup_all()
        assert errors == []


class TestMemberFactory:
    """Tests for MemberFactory."""

    def test_build_returns_dict(self):
        factory = MemberFactory()
        member = factory.build()
        assert isinstance(member, dict)
        assert "username" in member
        assert "email" in member
        assert "full_name" in member
        assert "role" in member
        assert member["role"] == "member"

    def test_build_with_overrides(self):
        factory = MemberFactory()
        member = factory.build(role="admin", email="custom@test.com")
        assert member["role"] == "admin"
        assert member["email"] == "custom@test.com"

    def test_build_generates_unique_usernames(self):
        factory = MemberFactory()
        m1 = factory.build()
        m2 = factory.build()
        assert m1["username"] != m2["username"]


class TestProjectFactory:
    """Tests for ProjectFactory."""

    def test_build_returns_dict(self):
        factory = ProjectFactory()
        project = factory.build()
        assert isinstance(project, dict)
        assert "name" in project
        assert "description" in project
        assert "status" in project
        assert project["status"] == "draft"

    def test_build_with_overrides(self):
        factory = ProjectFactory()
        project = factory.build(status="active", name="My Project")
        assert project["status"] == "active"
        assert project["name"] == "My Project"


class TestDataFactory:
    """Tests for DataFactory aggregate."""

    def test_has_sub_factories(self):
        factory = DataFactory()
        assert hasattr(factory, "members")
        assert hasattr(factory, "projects")
        assert isinstance(factory.members, MemberFactory)
        assert isinstance(factory.projects, ProjectFactory)

    def test_shared_cleanup_tracker(self):
        factory = DataFactory()
        cleaned = []
        factory.tracker.push("test", 1, lambda: cleaned.append("done"))
        factory.cleanup_all()
        assert cleaned == ["done"]

    def test_build_does_not_register_cleanup(self):
        factory = DataFactory()
        factory.members.build()
        factory.projects.build()
        assert factory.tracker.pending_count == 0
