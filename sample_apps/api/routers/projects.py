"""
Ankole Framework - Projects Router

CRUD for projects plus multi-step approval / rejection workflow.
"""

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from sample_apps.api.dependencies import get_db, get_current_user
from sample_apps.api.models import UserModel, ProjectModel, ApprovalModel
from sample_apps.api.schemas import (
    ProjectCreate,
    ProjectOut,
    ProjectDetailOut,
    ApproveRequest,
    RejectRequest,
)

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=List[ProjectOut])
def list_projects(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Return all projects."""
    return db.query(ProjectModel).order_by(ProjectModel.id).all()


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Create a new project."""
    project = ProjectModel(
        name=body.name,
        description=body.description,
        required_approvals=body.required_approvals,
        created_by=current_user.id,
        status="draft",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectDetailOut)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get a single project with its approvals."""
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.post("/{project_id}/approve", response_model=ProjectDetailOut)
def approve_project(
    project_id: int,
    body: ApproveRequest = ApproveRequest(),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Approve the current step of a project.

    - Transitions a 'draft' project to 'pending_approval' on first approval.
    - Creates a new approval record for the next step.
    - Transitions to 'approved' once required_approvals is reached.
    """
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if project.status == "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project is already fully approved",
        )
    if project.status == "rejected":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project has been rejected",
        )

    # Determine the next step number
    existing_approvals = (
        db.query(ApprovalModel)
        .filter(ApprovalModel.project_id == project_id)
        .order_by(ApprovalModel.step_number)
        .all()
    )
    next_step = len(existing_approvals) + 1

    # Check if user already approved this project
    already_approved = any(a.approver_id == current_user.id for a in existing_approvals)
    if already_approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already approved this project",
        )

    # Create the approval record
    approval = ApprovalModel(
        project_id=project_id,
        approver_id=current_user.id,
        step_number=next_step,
        status="approved",
        comment=body.comment,
    )
    db.add(approval)

    # Update project status
    if project.status == "draft":
        project.status = "pending_approval"

    if next_step >= project.required_approvals:
        project.status = "approved"

    project.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(project)
    return project


@router.post("/{project_id}/reject", response_model=ProjectDetailOut)
def reject_project(
    project_id: int,
    body: RejectRequest = RejectRequest(),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Reject a project."""
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if project.status == "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reject an already-approved project",
        )
    if project.status == "rejected":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project is already rejected",
        )

    # Determine the next step number for the rejection record
    existing_count = (
        db.query(ApprovalModel)
        .filter(ApprovalModel.project_id == project_id)
        .count()
    )
    next_step = existing_count + 1

    rejection = ApprovalModel(
        project_id=project_id,
        approver_id=current_user.id,
        step_number=next_step,
        status="rejected",
        comment=body.comment,
    )
    db.add(rejection)

    project.status = "rejected"
    project.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(project)
    return project
