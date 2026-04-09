"""
Ankole Framework - Auth Router

POST /api/auth/login  -> Authenticate and return JWT
POST /api/auth/logout -> Client-side token discard
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from sample_apps.api.dependencies import get_db, get_current_user, pwd_context, create_access_token
from sample_apps.api.models import UserModel
from sample_apps.api.schemas import LoginRequest, TokenOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate a user and return a JWT access token."""
    user = db.query(UserModel).filter(UserModel.username == body.username).first()
    if not user or not pwd_context.verify(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended",
        )
    access_token = create_access_token(data={"sub": user.id, "username": user.username})
    return TokenOut(access_token=access_token)


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(current_user: UserModel = Depends(get_current_user)):
    """
    Logout endpoint.  JWT is stateless so true server-side invalidation
    is not performed here.  The client should discard the token.
    """
    return {"detail": "Successfully logged out"}
