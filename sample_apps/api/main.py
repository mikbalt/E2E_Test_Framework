"""
Ankole Framework - FastAPI REST API

Entry point for the application. Assembles middleware, routers, and
startup logic. Run with:

    uvicorn sample_apps.api.main:app --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sample_apps.api.database import SessionLocal
from sample_apps.api.models import UserModel
from sample_apps.api.dependencies import pwd_context
from sample_apps.api.routers import auth, members, roles, projects, health

# ---------------------------------------------------------------------------
# Seed helper - rehash placeholder passwords on startup
# ---------------------------------------------------------------------------

_SEED_PASSWORDS = {
    "admin": "admin123",
    "approver1": "approver123",
    "approver2": "approver123",
    "approver3": "approver123",
    "member1": "member123",
    "member2": "member123",
}


def _seed_passwords() -> None:
    """Re-hash seed user passwords if they still have the placeholder value."""
    db = SessionLocal()
    try:
        for username, plain in _SEED_PASSWORDS.items():
            user = db.query(UserModel).filter(UserModel.username == username).first()
            if user and user.password_hash == "placeholder_will_be_set_by_app":
                user.password_hash = pwd_context.hash(plain)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Application lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup: seed passwords
    try:
        _seed_passwords()
    except Exception:
        pass  # DB might not be ready yet; that is fine
    yield
    # Shutdown: nothing special


# ---------------------------------------------------------------------------
# Create FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Ankole Framework API",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Mount routers
# ---------------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(members.router)
app.include_router(roles.router)
app.include_router(projects.router)
app.include_router(health.router)
