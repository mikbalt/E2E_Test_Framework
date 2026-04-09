"""
Shared test data classes for Ankole Framework E2E tests.

Provides dataclasses with sensible defaults for the workspace application.
Override via from_env() or direct initialization.

Usage:
    from tests.test_data import MemberManagementData

    data = MemberManagementData.from_env()
"""

import os
from dataclasses import dataclass, field


@dataclass
class MemberManagementData:
    """Test data for member CRUD operations."""
    admin_username: str = "admin"
    admin_password: str = "admin123"

    member_username: str = "test_member_e2e"
    member_email: str = "test_member@example.com"
    member_password: str = "member123"
    member_role: str = "member"

    @classmethod
    def from_env(cls, **overrides):
        defaults = cls()
        kwargs = {
            "admin_username": os.environ.get("ADMIN_USERNAME", defaults.admin_username),
            "admin_password": os.environ.get("ADMIN_PASSWORD", defaults.admin_password),
            "member_username": os.environ.get("TEST_MEMBER_USERNAME", defaults.member_username),
            "member_email": os.environ.get("TEST_MEMBER_EMAIL", defaults.member_email),
            "member_password": os.environ.get("TEST_MEMBER_PASSWORD", defaults.member_password),
        }
        kwargs.update(overrides)
        return cls(**kwargs)


@dataclass
class SuspendReactivateData:
    """Test data for member suspend/reactivate flow."""
    admin_username: str = "admin"
    admin_password: str = "admin123"

    member_username: str = "test_suspend_e2e"
    member_email: str = "test_suspend@example.com"
    member_password: str = "member123"

    @classmethod
    def from_env(cls, **overrides):
        defaults = cls()
        kwargs = {
            "admin_username": os.environ.get("ADMIN_USERNAME", defaults.admin_username),
            "admin_password": os.environ.get("ADMIN_PASSWORD", defaults.admin_password),
            "member_username": os.environ.get("SUSPEND_MEMBER_USERNAME", defaults.member_username),
            "member_email": os.environ.get("SUSPEND_MEMBER_EMAIL", defaults.member_email),
            "member_password": os.environ.get("SUSPEND_MEMBER_PASSWORD", defaults.member_password),
        }
        kwargs.update(overrides)
        return cls(**kwargs)


@dataclass
class Approver:
    """A single approver's credentials."""
    username: str
    password: str


@dataclass
class ProjectApprovalData:
    """Test data for multi-step project approval workflow."""
    admin_username: str = "admin"
    admin_password: str = "admin123"

    project_name: str = "E2E Test Project"
    project_description: str = "Automated test project for approval workflow"
    required_approvals: int = 3

    approvers: list = field(default_factory=lambda: [
        Approver(username="approver1", password="approver123"),
        Approver(username="approver2", password="approver123"),
        Approver(username="approver3", password="approver123"),
    ])

    @classmethod
    def from_env(cls, **overrides):
        defaults = cls()
        kwargs = {
            "admin_username": os.environ.get("ADMIN_USERNAME", defaults.admin_username),
            "admin_password": os.environ.get("ADMIN_PASSWORD", defaults.admin_password),
            "project_name": os.environ.get("PROJECT_NAME", defaults.project_name),
        }

        approvers = []
        for i, default_approver in enumerate(defaults.approvers, start=1):
            approvers.append(Approver(
                username=os.environ.get(f"APPROVER{i}_USERNAME", default_approver.username),
                password=os.environ.get(f"APPROVER{i}_PASSWORD", default_approver.password),
            ))
        kwargs["approvers"] = approvers

        kwargs.update(overrides)
        return cls(**kwargs)


@dataclass
class LoginData:
    """Test data for login tests."""
    valid_username: str = "admin"
    valid_password: str = "admin123"
    invalid_username: str = "nonexistent"
    invalid_password: str = "wrongpassword"

    @classmethod
    def from_env(cls, **overrides):
        defaults = cls()
        kwargs = {
            "valid_username": os.environ.get("ADMIN_USERNAME", defaults.valid_username),
            "valid_password": os.environ.get("ADMIN_PASSWORD", defaults.valid_password),
        }
        kwargs.update(overrides)
        return cls(**kwargs)
