"""
Ankole Framework - Members Router

CRUD + suspend / reactivate for users (called "members" in the API).
"""

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from sample_apps.api.dependencies import get_db, get_current_user, pwd_context
from sample_apps.api.models import UserModel
from sample_apps.api.schemas import MemberCreate, MemberUpdate, MemberOut

router = APIRouter(prefix="/api/members", tags=["members"])


@router.get("", response_model=List[MemberOut])
def list_members(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Return all members."""
    return db.query(UserModel).order_by(UserModel.id).all()


@router.post("", response_model=MemberOut, status_code=status.HTTP_201_CREATED)
def create_member(
    body: MemberCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Create a new member."""
    if db.query(UserModel).filter(UserModel.username == body.username).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{body.username}' already exists",
        )
    if db.query(UserModel).filter(UserModel.email == body.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{body.email}' already exists",
        )

    user = UserModel(
        username=body.username,
        email=body.email,
        password_hash=pwd_context.hash(body.password),
        role_id=body.role_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{member_id}", response_model=MemberOut)
def get_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get a single member by ID."""
    user = db.query(UserModel).filter(UserModel.id == member_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    return user


@router.put("/{member_id}", response_model=MemberOut)
def update_member(
    member_id: int,
    body: MemberUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Update an existing member."""
    user = db.query(UserModel).filter(UserModel.id == member_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    if body.username is not None:
        existing = db.query(UserModel).filter(
            UserModel.username == body.username, UserModel.id != member_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username '{body.username}' already exists",
            )
        user.username = body.username

    if body.email is not None:
        existing = db.query(UserModel).filter(
            UserModel.email == body.email, UserModel.id != member_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{body.email}' already exists",
            )
        user.email = body.email

    if body.role_id is not None:
        user.role_id = body.role_id

    if body.password is not None:
        user.password_hash = pwd_context.hash(body.password)

    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Delete a member."""
    user = db.query(UserModel).filter(UserModel.id == member_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    db.delete(user)
    db.commit()
    return None


@router.post("/{member_id}/suspend", response_model=MemberOut)
def suspend_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Suspend a member (set is_active=False)."""
    user = db.query(UserModel).filter(UserModel.id == member_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    user.is_active = False
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user


@router.post("/{member_id}/reactivate", response_model=MemberOut)
def reactivate_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Reactivate a suspended member (set is_active=True)."""
    user = db.query(UserModel).filter(UserModel.id == member_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    user.is_active = True
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user
