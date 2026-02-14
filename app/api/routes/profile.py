from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.db.session import get_db
from app.models.user import User

router = APIRouter()


class ShowProfile(BaseModel):
    id: str
    real_name: Optional[str]
    username: str
    avatar_url: Optional[str]
    bio: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/{username}", response_model=ShowProfile)
def get_profile(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return ShowProfile(
        id=str(user.id),
        real_name=user.real_name,
        username=user.username,
        avatar_url=user.avatar_url,
        bio=user.bio,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.get("/id/{user_id}", response_model=ShowProfile)
def get_profile_by_id(user_id: str, db: Session = Depends(get_db)):
    """Get user profile by user ID."""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return ShowProfile(
        id=str(user.id),
        real_name=user.real_name,
        username=user.username,
        avatar_url=user.avatar_url,
        bio=user.bio,
        is_active=user.is_active,
        created_at=user.created_at,
    )