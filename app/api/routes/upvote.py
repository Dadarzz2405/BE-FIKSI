from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.db.session import get_db
from app.models.upvote import Upvote
from app.models.post import Post
from app.models.user import User
from app.api.dependencies import get_current_active_user
from app.core.auth_service import supabase_auth

router = APIRouter()


class UpvoteResponse(BaseModel):
    upvote_count: int
    is_upvoted: bool


@router.get("/posts/{post_id}/upvote", response_model=UpvoteResponse)
def get_upvote_status(
    post_id: str,
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    """Get upvote count and whether the current user has upvoted."""
    post = db.query(Post).filter(Post.id == post_id, Post.is_published == True).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    count = (
        db.query(func.count(Upvote.id))
        .filter(Upvote.post_id == post_id)
        .scalar()
    ) or 0

    is_upvoted = False
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
        if token and token not in ("null", "undefined"):
            try:
                resp = supabase_auth.get_user(token)
                if resp.user:
                    existing = (
                        db.query(Upvote)
                        .filter(Upvote.user_id == resp.user.id, Upvote.post_id == post_id)
                        .first()
                    )
                    is_upvoted = existing is not None
            except Exception:
                pass

    return UpvoteResponse(upvote_count=count, is_upvoted=is_upvoted)


@router.post("/posts/{post_id}/upvote", response_model=UpvoteResponse)
def toggle_upvote(
    post_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Toggle upvote on a post. Returns new count and upvote state."""
    post = db.query(Post).filter(Post.id == post_id, Post.is_published == True).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if str(post.author_id) == str(current_user.id):
        raise HTTPException(status_code=400, detail="You cannot upvote your own post")

    existing = (
        db.query(Upvote)
        .filter(Upvote.user_id == current_user.id, Upvote.post_id == post_id)
        .first()
    )

    if existing:
        db.delete(existing)
        db.commit()
        is_upvoted = False
    else:
        upvote = Upvote(user_id=current_user.id, post_id=post_id)
        db.add(upvote)
        db.commit()
        is_upvoted = True

    count = (
        db.query(func.count(Upvote.id))
        .filter(Upvote.post_id == post_id)
        .scalar()
    ) or 0

    return UpvoteResponse(upvote_count=count, is_upvoted=is_upvoted)