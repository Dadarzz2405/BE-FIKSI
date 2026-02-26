from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import uuid, mimetypes

from app.db.session import get_db
from app.models.user import User
from app.core.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from app.api.dependencies import get_current_active_user
from app.core.gamification import xp_for_level, get_rank, next_rank_threshold

router = APIRouter()

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_AVATAR_SIZE     = 5 * 1024 * 1024


class RankInfo(BaseModel):
    name: str
    icon: str
    min_cp: int


class ShowProfile(BaseModel):
    id: str
    real_name: Optional[str]
    username: str
    avatar_url: Optional[str]
    bio: Optional[str]
    is_active: bool
    created_at: datetime
    # ── Gamification ─────────────────────────────────────────────────────────
    level:             int      = 1
    xp_current:        int      = 0
    xp_total:          int      = 0
    xp_to_next_level:  int      = 100
    reputation:        int      = 0
    cp_total:          int      = 0
    rank:              RankInfo = RankInfo(name="Bronze", icon="🥉", min_cp=0)
    cp_to_next_rank:   Optional[int] = None   # None = already at Diamond

    class Config:
        from_attributes = True


class UpdateProfileBody(BaseModel):
    username:   Optional[str] = None
    real_name:  Optional[str] = None
    bio:        Optional[str] = None
    avatar_url: Optional[str] = None


def _to_response(user: User) -> ShowProfile:
    level      = user.level      or 1
    xp_current = user.xp_current or 0
    reputation = user.reputation or 0
    cp_total   = user.cp_total   or 0
    rank_data  = get_rank(cp_total)
    next_thr   = next_rank_threshold(cp_total)

    return ShowProfile(
        id=str(user.id),
        real_name=user.real_name,
        username=user.username,
        avatar_url=user.avatar_url,
        bio=user.bio,
        is_active=user.is_active,
        created_at=user.created_at,
        level=level,
        xp_current=xp_current,
        xp_total=user.xp_total or 0,
        xp_to_next_level=xp_for_level(level),
        reputation=reputation,
        cp_total=cp_total,
        rank=RankInfo(**rank_data),
        cp_to_next_rank=(next_thr - cp_total) if next_thr else None,
    )


@router.patch("/me", response_model=ShowProfile)
def update_my_profile(
    body: UpdateProfileBody,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if body.username is not None:
        clean = body.username.strip()
        if not clean or len(clean) > 50:
            raise HTTPException(status_code=400, detail="Username must be 1–50 characters")
        if db.query(User).filter(User.username == clean, User.id != current_user.id).first():
            raise HTTPException(status_code=400, detail="Username already taken")
        current_user.username = clean
    if body.real_name  is not None: current_user.real_name  = body.real_name
    if body.bio        is not None: current_user.bio        = body.bio
    if body.avatar_url is not None: current_user.avatar_url = body.avatar_url
    current_user.updated_at = datetime.utcnow()
    db.commit(); db.refresh(current_user)
    return _to_response(current_user)


@router.post("/me/avatar", response_model=ShowProfile)
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(status_code=500, detail="Storage not configured")
    content_type = file.content_type or "image/jpeg"
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, GIF, or WebP images are allowed")
    data = await file.read()
    if len(data) > MAX_AVATAR_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 5 MB)")
    ext = mimetypes.guess_extension(content_type) or ".jpg"
    if ext == ".jpe": ext = ".jpg"
    filename = f"avatars/{current_user.id}_{uuid.uuid4()}{ext}"
    from supabase import create_client
    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    try:
        try:
            existing = client.storage.list_buckets()
            if not any(b["name"] == "avatars" for b in existing):
                client.storage.create_bucket("avatars", options={"public": True})
        except Exception:
            pass
        client.storage.from_("avatars").upload(filename, data, file_options={"content-type": content_type})
        url = client.storage.from_("avatars").get_public_url(filename)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Upload failed: {exc}")
    current_user.avatar_url = url
    current_user.updated_at = datetime.utcnow()
    db.commit(); db.refresh(current_user)
    return _to_response(current_user)


@router.get("/{username}", response_model=ShowProfile)
def get_profile(username: str, db: Session = Depends(get_db)):
    clean = username.lstrip("@")
    user = db.query(User).filter(User.username == clean).first()
    if not user:
        user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _to_response(user)


@router.get("/id/{user_id}", response_model=ShowProfile)
def get_profile_by_id(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _to_response(user)