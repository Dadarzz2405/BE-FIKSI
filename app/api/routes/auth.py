from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Any
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.core.auth_service import supabase_auth
from app.core.config import FRONTEND_URL

router = APIRouter()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class LoginRequest(BaseModel):
    email: str = Field(..., description="Username atau alamat email")
    password: str


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    username: str
    real_name: Optional[str] = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class SignupResponse(BaseModel):
    access_token: Optional[str] = None
    token_type: str = "bearer"
    user: dict
    requires_email_verification: bool = False
    message: str


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    real_name: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


# ============================================================================
# HELPERS
# ============================================================================

def _make_unique_username(base: str, db: Session) -> str:
    import re
    slug = re.sub(r"[^a-z0-9_]", "", base.lower().replace(" ", "_"))[:30] or "user"
    username = slug
    counter = 1
    while db.query(User).filter(User.username == username).first():
        username = f"{slug}{counter}"
        counter += 1
    return username


def _get_or_create_supabase_user(auth_user: Any, db: Session) -> User:
    """
    Find existing user by Supabase Auth id or email, or create one on first login
    (e.g. after Supabase native Google OAuth).
    """
    auth_id = str(auth_user.id)
    email: str = getattr(auth_user, "email", "") or ""
    metadata = getattr(auth_user, "user_metadata", None) or {}
    real_name: Optional[str] = (
        metadata.get("full_name")
        or metadata.get("name")
        or metadata.get("real_name")
    )
    avatar_url: Optional[str] = metadata.get("avatar_url") or metadata.get("picture")

    user = db.query(User).filter(User.id == auth_user.id).first()
    if user:
        return user

    if email:
        user = db.query(User).filter(User.email == email).first()
        if user:
            return user  # Same email, e.g. existing email signup or linked identity

    # First-time OAuth login — auto-create DB row
    base = (real_name or "").replace(" ", "_") or (email.split("@")[0] if email else "user")
    username = _make_unique_username(base, db)

    new_user = User(
        id=auth_user.id,
        email=email or f"{auth_id}@oauth.local",
        username=username,
        real_name=real_name,
        avatar_url=avatar_url,
        hashed_password="",
        is_active=True,
        bio="",
        subscription="Free",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/login", response_model=AuthResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    try:
        login_identifier = credentials.email.strip()
        if not login_identifier:
            raise HTTPException(status_code=400, detail="Username or email is required")

        login_email = login_identifier
        if "@" not in login_identifier:
            user_by_username = db.query(User).filter(
                User.username == login_identifier
            ).first()
            if not user_by_username:
                raise HTTPException(
                    status_code=401, detail="Invalid username/email or password"
                )
            login_email = user_by_username.email

        auth_response = supabase_auth.sign_in(email=login_email, password=credentials.password)

        if not auth_response.user:
            raise HTTPException(status_code=401, detail="Invalid username/email or password")
        if not auth_response.session:
            raise HTTPException(
                status_code=403, detail="Email not verified. Please verify your email first."
            )

        user = db.query(User).filter(User.id == auth_response.user.id).first()
        if not user:
            auth_email = getattr(auth_response.user, "email", None)
            if auth_email:
                user = db.query(User).filter(User.email == auth_email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found in database")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is not active.")

        return AuthResponse(
            access_token=auth_response.session.access_token,
            user={
                "id": str(user.id), "email": user.email, "username": user.username,
                "real_name": user.real_name, "avatar_url": user.avatar_url,
                "bio": user.bio, "is_active": user.is_active,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        if "email not confirmed" in str(e).lower():
            raise HTTPException(status_code=403, detail="Email belum diverifikasi. Cek inbox Anda.")
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed. Please try again.")


@router.post("/signup", response_model=SignupResponse)
def signup(signup_data: SignupRequest, db: Session = Depends(get_db)):
    try:
        existing = db.query(User).filter(
            (User.email == signup_data.email) | (User.username == signup_data.username)
        ).first()
        if existing:
            field = "email" if existing.email == signup_data.email else "username"
            raise HTTPException(
                status_code=400,
                detail="User with this email already exists" if field == "email" else "Username is already taken",
            )

        auth_response = supabase_auth.sign_up(
            email=signup_data.email,
            password=signup_data.password,
            redirect_url=f"{FRONTEND_URL.rstrip('/')}/auth/callback",
        )
        if not auth_response.user:
            raise HTTPException(status_code=400, detail="Failed to create user account")

        has_session = bool(auth_response.session)
        new_user = User(
            id=auth_response.user.id,
            email=signup_data.email,
            username=signup_data.username,
            real_name=signup_data.real_name,
            hashed_password="",
            is_active=has_session,
            bio="",
            subscription="Free",
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return SignupResponse(
            access_token=auth_response.session.access_token if has_session else None,
            requires_email_verification=not has_session,
            message=(
                "Account created. Please verify your email before logging in."
                if not has_session else "Account created successfully."
            ),
            user={
                "id": str(new_user.id), "email": new_user.email, "username": new_user.username,
                "real_name": new_user.real_name, "avatar_url": new_user.avatar_url,
                "bio": new_user.bio, "is_active": new_user.is_active,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed. Please try again.")


@router.get("/google/url")
def get_google_oauth_url(redirect_to: Optional[str] = None):
    """
    Return the Supabase native Google OAuth URL. Frontend should redirect the
    user to this URL. After sign-in, Supabase redirects to your frontend
    (redirect_to or FRONTEND_URL/auth/callback) with the session in the URL;
    the frontend Supabase client can then get the access_token and send it
    as Bearer token to the API.
    """
    redirect_url = (redirect_to or f"{FRONTEND_URL.rstrip('/')}/auth/callback").strip()
    url = supabase_auth.get_oauth_sign_in_url(provider="google", redirect_to=redirect_url)
    return {"url": url}


@router.post("/logout")
def logout():
    try:
        supabase_auth.sign_out()
    except Exception:
        pass
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def get_current_user(authorization: str = Header(...), db: Session = Depends(get_db)):
    """
    Validate Supabase access token (email/password or native Google OAuth).
    Creates a local User row on first login for OAuth users.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header.")

    token = authorization.replace("Bearer ", "").strip()
    if not token or token in ("null", "undefined"):
        raise HTTPException(status_code=401, detail="No valid token. Please log in again.")

    try:
        auth_user_resp = supabase_auth.get_user(token)
        if not auth_user_resp.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        auth_user = auth_user_resp.user
        user = db.query(User).filter(User.id == auth_user.id).first()
        if not user:
            user = db.query(User).filter(User.email == auth_user.email).first() if getattr(auth_user, "email", None) else None
        if not user:
            user = _get_or_create_supabase_user(auth_user, db)

        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is not active.")

        return UserResponse(
            id=str(user.id), email=user.email, username=user.username,
            real_name=user.real_name, avatar_url=user.avatar_url,
            bio=user.bio, is_active=user.is_active,
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get current user error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


@router.get("/health")
def auth_health():
    return {"status": "auth router ready"}