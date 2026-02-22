from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
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
    """Login request payload."""
    email: str = Field(..., description="Username atau alamat email")
    password: str


class SignupRequest(BaseModel):
    """Signup request payload."""
    email: EmailStr
    password: str
    username: str
    real_name: Optional[str] = None


class AuthResponse(BaseModel):
    """Authentication response with token and user info."""
    access_token: str
    token_type: str = "bearer"
    user: dict


class SignupResponse(BaseModel):
    """Signup response supporting email-confirmation flow."""
    access_token: Optional[str] = None
    token_type: str = "bearer"
    user: dict
    requires_email_verification: bool = False
    message: str


class UserResponse(BaseModel):
    """User information response."""
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
# AUTHENTICATION ENDPOINTS
# ============================================================================

@router.post("/login", response_model=AuthResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    try:
        login_identifier = credentials.email.strip()
        if not login_identifier:
            raise HTTPException(
                status_code=400,
                detail="Username or email is required"
            )

        user_by_identifier = None
        login_email = login_identifier

        # Support both username and email login.
        if "@" not in login_identifier:
            user_by_identifier = db.query(User).filter(User.username == login_identifier).first()
            if not user_by_identifier:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid username/email or password"
                )
            login_email = user_by_identifier.email

        # Authenticate with Supabase Auth
        auth_response = supabase_auth.sign_in(
            email=login_email,
            password=credentials.password
        )
        
        if not auth_response.user:
            raise HTTPException(
                status_code=401,
                detail="Invalid username/email or password"
            )
        
        if not auth_response.session:
            raise HTTPException(
                status_code=403,
                detail="Email not verified or session not available. Please verify your email first."
            )
        
        # Get user from database
        user = db.query(User).filter(User.id == auth_response.user.id).first()

        # Seeded users or legacy rows may not share Supabase Auth UUID.
        if not user:
            auth_email = getattr(auth_response.user, "email", None)
            if auth_email:
                user = db.query(User).filter(User.email == auth_email).first()
        
        if not user and user_by_identifier:
            user = user_by_identifier
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found in database"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=403,
                detail="Account is not active. Please verify your email."
            )
        
        # Return token and user info
        return AuthResponse(
            access_token=auth_response.session.access_token,
            user={
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "real_name": user.real_name,
                "avatar_url": user.avatar_url,
                "bio": user.bio,
                "is_active": user.is_active,
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        err_msg = str(e).lower()
        if "email not confirmed" in err_msg or "email_not_confirmed" in err_msg:
            raise HTTPException(
                status_code=403,
                detail="Email belum diverifikasi. Cek inbox Anda dan klik tautan verifikasi dari kami."
            )
        print(f"Login error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Login failed. Please try again."
        )


@router.post("/signup", response_model=SignupResponse)
def signup(signup_data: SignupRequest, db: Session = Depends(get_db)):
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == signup_data.email) | (User.username == signup_data.username)
        ).first()
        
        if existing_user:
            if existing_user.email == signup_data.email:
                raise HTTPException(
                    status_code=400,
                    detail="User with this email already exists"
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Username is already taken"
                )
        
        # Create user in Supabase Auth (redirect_url must be in Supabase Dashboard → Auth → URL Configuration → Redirect URLs)
        auth_response = supabase_auth.sign_up(
            email=signup_data.email,
            password=signup_data.password,
            redirect_url=f"{FRONTEND_URL.rstrip('/')}/auth/callback",
        )
        
        if not auth_response.user:
            raise HTTPException(
                status_code=400,
                detail="Failed to create user account"
            )
        
        # Create user in database
        has_session = bool(auth_response.session)
        new_user = User(
            id=auth_response.user.id,  # Use Supabase user ID for consistency
            email=signup_data.email,
            username=signup_data.username,
            real_name=signup_data.real_name,
            hashed_password="",  # Password is handled by Supabase Auth
            is_active=has_session,
            bio="",
            subscription="Free"
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Return token and user info
        return SignupResponse(
            access_token=auth_response.session.access_token if has_session else None,
            requires_email_verification=not has_session,
            message=(
                "Account created. Please verify your email before logging in."
                if not has_session
                else "Account created successfully."
            ),
            user={
                "id": str(new_user.id),
                "email": new_user.email,
                "username": new_user.username,
                "real_name": new_user.real_name,
                "avatar_url": new_user.avatar_url,
                "bio": new_user.bio,
                "is_active": new_user.is_active,
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Signup error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Registration failed. Please try again."
        )


@router.post("/logout")
def logout():
    try:
        supabase_auth.sign_out()
        return {"message": "Logged out successfully"}
    except Exception as e:
        print(f"Logout error: {e}")
        # Even if logout fails on server, return success
        # Client will clear token anyway
        return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
def get_current_user(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):

    try:
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization header format. Expected: Bearer <token>"
            )
        
        access_token = authorization.replace("Bearer ", "").strip()
        if not access_token or access_token in ("null", "undefined"):
            raise HTTPException(
                status_code=401,
                detail="No valid token. Please log in again."
            )
        
        auth_user = supabase_auth.get_user(access_token)
        
        if not auth_user.user:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )
        
        # Get user from database
        user = db.query(User).filter(User.id == auth_user.user.id).first()

        # Fallback for legacy/seeded records where DB UUID differs from Supabase UUID.
        if not user:
            auth_email = getattr(auth_user.user, "email", None)
            if auth_email:
                user = db.query(User).filter(User.email == auth_email).first()
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found in database"
            )
        
        return UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            real_name=user.real_name,
            avatar_url=user.avatar_url,
            bio=user.bio,
            is_active=user.is_active,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get current user error: {e}")
        raise HTTPException(
            status_code=401,
            detail="Authentication failed"
        )


@router.get("/health")
def auth_health():
    return {"status": "auth router ready"}
