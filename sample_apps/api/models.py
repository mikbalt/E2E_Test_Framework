"""
Ankole Framework - SQLAlchemy ORM Models
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    JSON,
)
from sqlalchemy.orm import relationship

from sample_apps.api.database import Base


class RoleModel(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    permissions = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    users = relationship("UserModel", back_populates="role")


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    role = relationship("RoleModel", back_populates="users")
    projects = relationship("ProjectModel", back_populates="creator")
    approvals = relationship("ApprovalModel", back_populates="approver")


class ProjectModel(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    description = Column(Text)
    status = Column(
        SAEnum(
            "draft",
            "pending_approval",
            "approved",
            "rejected",
            name="project_status",
            create_type=False,
        ),
        nullable=False,
        default="draft",
    )
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    required_approvals = Column(Integer, nullable=False, default=3)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    creator = relationship("UserModel", back_populates="projects")
    approvals = relationship(
        "ApprovalModel", back_populates="project", order_by="ApprovalModel.step_number"
    )


class ApprovalModel(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    step_number = Column(Integer, nullable=False)
    status = Column(
        SAEnum(
            "pending",
            "approved",
            "rejected",
            name="approval_status",
            create_type=False,
        ),
        nullable=False,
        default="pending",
    )
    comment = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    project = relationship("ProjectModel", back_populates="approvals")
    approver = relationship("UserModel", back_populates="approvals")
