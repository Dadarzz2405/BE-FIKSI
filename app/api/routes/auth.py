from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.core.auth_service import supabase_auth

router = APIRouter()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class LoginRequest(BaseModel):
    """Login request payload."""
    email: EmailStr
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
        # Authenticate with Supabase Auth
        auth_response = supabase_auth.sign_in(
            email=credentials.email,
            password=credentials.password
        )
        
        if not auth_response.user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        # Get user from database
        user = db.query(User).filter(User.email == credentials.email).first()
        
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
        print(f"Login error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Login failed. Please try again."
        )


@router.post("/signup", response_model=AuthResponse)
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
        
        # Create user in Supabase Auth
        auth_response = supabase_auth.sign_up(
            email=signup_data.email,
            password=signup_data.password
        )
        
        if not auth_response.user:
            raise HTTPException(
                status_code=400,
                detail="Failed to create user account"
            )
        
        # Create user in database
        new_user = User(
            id=auth_response.user.id,  # Use Supabase user ID for consistency
            email=signup_data.email,
            username=signup_data.username,
            real_name=signup_data.real_name,
            hashed_password="",  # Password is handled by Supabase Auth
            is_active=True,
            bio="",
            subscription="Free"
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Return token and user info
        return AuthResponse(
            access_token=auth_response.session.access_token,
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
        
        access_token = authorization.replace("Bearer ", "")
        
        auth_user = supabase_auth.get_user(access_token)
        
        if not auth_user.user:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )
        
        # Get user from database
        user = db.query(User).filter(User.id == auth_user.user.id).first()
        
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