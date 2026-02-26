"""
Shared authentication dependency for API routes.
Looks up the user by Supabase auth ID first, then falls back to email,
matching the same logic used in auth.py's _get_or_create_supabase_user.
"""
# FastAPI dependencies and HTTP exception handling
from fastapi import HTTPException, Header, Depends
# SQLAlchemy ORM for database queries
from sqlalchemy.orm import Session

# Local imports for database and authentication
from app.db.session import get_db
from app.models.user import User
from app.core.auth_service import supabase_auth


# Dependency function to authenticate users via Bearer token
def get_current_active_user(
    authorization: str = Header(...),
    db: Session = Depends(get_db),
) -> User:
    """
    Validate a Supabase Bearer token and return the matching DB user.

    Lookup order:
      1. By Supabase auth UUID (fast path)
      2. By email (fallback for users whose DB id differs from auth id,
         e.g. email-signup users where ids may have diverged)

    Auto-activates the user if is_active is False but token is valid,
    because a valid Supabase token is proof of successful authentication.
    """
    # Validate authorization header format
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    # Extract token from header and validate it's not null/undefined
    token = authorization[7:].strip()
    if not token or token in ("null", "undefined"):
        raise HTTPException(status_code=401, detail="No valid token provided")

    # Verify token with Supabase authentication service
    try:
        resp = supabase_auth.get_user(token)
        if not resp.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication failed")

    auth_user = resp.user

    # Primary lookup: Try by Supabase auth UUID
    user = db.query(User).filter(User.id == auth_user.id).first()

    # Fallback lookup: Try by email (handles id mismatch from email signup flow)
    if not user:
        email = getattr(auth_user, "email", None)
        if email:
            user = db.query(User).filter(User.email == email).first()

    # User not found in database
    if not user:
        raise HTTPException(status_code=404, detail="User not found in database")

    # Auto-activate: valid token = authenticated user, so ensure is_active is True
    if not user.is_active:
        user.is_active = True
        db.commit()
        db.refresh(user)

    return user