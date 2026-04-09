"""
Ankole Framework - Roles Router

Full CRUD for roles.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from sample_apps.api.dependencies import get_db, get_current_user
from sample_apps.api.models import RoleModel, UserModel
from sample_apps.api.schemas import RoleCreate, RoleUpdate, RoleOut

router = APIRouter(prefix="/api/roles", tags=["roles"])


@router.get("", response_model=List[RoleOut])
def list_roles(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Return all roles."""
    return db.query(RoleModel).order_by(RoleModel.id).all()


@router.post("", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
def create_role(
    body: RoleCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Create a new role."""
    if db.query(RoleModel).filter(RoleModel.name == body.name).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Role '{body.name}' already exists",
        )
    role = RoleModel(
        name=body.name,
        description=body.description,
        permissions=body.permissions,
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@router.get("/{role_id}", response_model=RoleOut)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get a single role by ID."""
    role = db.query(RoleModel).filter(RoleModel.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role


@router.put("/{role_id}", response_model=RoleOut)
def update_role(
    role_id: int,
    body: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Update an existing role."""
    role = db.query(RoleModel).filter(RoleModel.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    if body.name is not None:
        existing = db.query(RoleModel).filter(
            RoleModel.name == body.name, RoleModel.id != role_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Role '{body.name}' already exists",
            )
        role.name = body.name

    if body.description is not None:
        role.description = body.description

    if body.permissions is not None:
        role.permissions = body.permissions

    db.commit()
    db.refresh(role)
    return role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Delete a role."""
    role = db.query(RoleModel).filter(RoleModel.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    # Prevent deletion if users are assigned to this role
    user_count = db.query(UserModel).filter(UserModel.role_id == role_id).count()
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete role: {user_count} user(s) are still assigned to it",
        )
    db.delete(role)
    db.commit()
    return None
