"""
Ankole Framework - Pydantic Schemas (request / response models)
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: List[str] = []


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None


class RoleOut(RoleBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Members (Users)
# ---------------------------------------------------------------------------

class MemberBase(BaseModel):
    username: str
    email: str
    role_id: int


class MemberCreate(MemberBase):
    password: str


class MemberUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    role_id: Optional[int] = None
    password: Optional[str] = None


class MemberOut(MemberBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------------------------------------------------------------------------
# Projects & Approvals
# ---------------------------------------------------------------------------

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    required_approvals: int = 3


class ProjectCreate(ProjectBase):
    pass


class ApprovalOut(BaseModel):
    id: int
    project_id: int
    approver_id: int
    step_number: int
    status: str
    comment: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectOut(ProjectBase):
    id: int
    status: str
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectDetailOut(ProjectOut):
    approvals: List[ApprovalOut] = []

    model_config = ConfigDict(from_attributes=True)


class ApproveRequest(BaseModel):
    comment: Optional[str] = None


class RejectRequest(BaseModel):
    comment: Optional[str] = None


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class HealthOut(BaseModel):
    status: str
    db: str
    version: str
