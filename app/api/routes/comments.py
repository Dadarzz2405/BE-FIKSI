from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional, List

from app.db.session import get_db
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.core.auth_service import supabase_auth
from app.core.gamification import award_points, get_rank

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────

class CommentCreate(BaseModel):
    content: str


class RankInfo(BaseModel):
    name: str
    icon: str
    min_cp: int


class CommentAuthor(BaseModel):
    username: str
    avatar_url: Optional[str]
    real_name: Optional[str]
    level: int = 1
    reputation: int = 0
    cp_total: int = 0
    rank: RankInfo = RankInfo(name="Bronze", icon="🥉", min_cp=0)


class CommentResponse(BaseModel):
    id: str
    post_id: str
    content: str
    is_accepted: bool
    created_at: str
    author_id: str
    upvote_count: int = 0
    has_upvoted: bool = False
    author: Optional[CommentAuthor]

    class Config:
        from_attributes = True


# ── Auth dependency ───────────────────────────────────────────────────────────

def get_current_user(authorization: str = Header(...), db: Session = Depends(get_db)) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    token = authorization.replace("Bearer ", "")
    try:
        resp = supabase_auth.get_user(token)
        if not resp.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication failed")
    user = db.query(User).filter(User.id == resp.user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")
    return user


def get_optional_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Auth dependency that returns None instead of raising when no token is present."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.replace("Bearer ", "").strip()
    if not token or token in ("null", "undefined"):
        return None
    try:
        resp = supabase_auth.get_user(token)
        if not resp.user:
            return None
        return db.query(User).filter(User.id == resp.user.id).first()
    except Exception:
        return None


def _author_response(u: User) -> CommentAuthor:
    cp = u.cp_total or 0
    return CommentAuthor(
        username=u.username,
        avatar_url=u.avatar_url,
        real_name=u.real_name,
        level=u.level or 1,
        reputation=u.reputation or 0,
        cp_total=cp,
        rank=RankInfo(**get_rank(cp)),
    )


def _comment_to_response(
    c: Comment,
    db: Session,
    viewer_id: Optional[str] = None,
) -> CommentResponse:
    from app.models.upvote import Upvote

    # Count upvotes from the upvotes table
    upvote_count = db.query(func.count(Upvote.id)).filter(
        Upvote.comment_id == c.id
    ).scalar() or 0

    has_upvoted = False
    if viewer_id:
        has_upvoted = db.query(Upvote).filter(
            Upvote.comment_id == c.id,
            Upvote.user_id    == viewer_id,
        ).first() is not None

    return CommentResponse(
        id=str(c.id),
        post_id=str(c.post_id),
        content=c.content,
        is_accepted=c.is_accepted,
        created_at=c.created_at.isoformat(),
        author_id=str(c.author_id),
        upvote_count=upvote_count,
        has_upvoted=has_upvoted,
        author=_author_response(c.author) if c.author else None,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/posts/{post_id}/comments", response_model=List[CommentResponse])
def list_comments(
    post_id: str,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comments = (
        db.query(Comment)
        .filter(Comment.post_id == post_id)
        .order_by(desc(Comment.is_accepted), Comment.created_at)
        .all()
    )
    viewer_id = str(current_user.id) if current_user else None
    return [_comment_to_response(c, db, viewer_id) for c in comments]


@router.post("/posts/{post_id}/comments", response_model=CommentResponse, status_code=201)
def create_comment(
    post_id: str,
    body: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id, Post.is_published == True).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if not body.content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty")
    if str(post.author_id) == str(current_user.id):
        raise HTTPException(status_code=400, detail="You cannot answer your own question")

    comment = Comment(
        post_id=post.id,
        author_id=current_user.id,
        content=body.content.strip(),
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    award_points(current_user.id, "comment_created", db)
    return _comment_to_response(comment, db, str(current_user.id))


@router.patch("/comments/{comment_id}/accept", response_model=CommentResponse)
def accept_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    post = db.query(Post).filter(Post.id == comment.post_id).first()
    if not post or str(post.author_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Only the post author can accept answers")

    db.query(Comment).filter(
        Comment.post_id == comment.post_id,
        Comment.is_accepted == True,
    ).update({"is_accepted": False})

    comment.is_accepted = True
    db.commit()
    db.refresh(comment)

    # Award the answerer (not the question asker)
    award_points(comment.author_id, "comment_accepted", db)
    return _comment_to_response(comment, db, str(current_user.id))


@router.post("/comments/{comment_id}/upvote", response_model=CommentResponse)
def upvote_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Toggle upvote on a comment. Returns the updated comment."""
    from app.models.upvote import Upvote

    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if str(comment.author_id) == str(current_user.id):
        raise HTTPException(status_code=400, detail="You cannot upvote your own answer")

    existing = db.query(Upvote).filter(
        Upvote.comment_id == comment_id,
        Upvote.user_id    == current_user.id,
    ).first()

    if existing:
        # Un-upvote
        db.delete(existing)
        db.commit()
    else:
        # Upvote — award points to the answer author
        db.add(Upvote(user_id=current_user.id, comment_id=comment_id))
        db.commit()
        award_points(comment.author_id, "comment_upvoted", db)

    db.refresh(comment)
    return _comment_to_response(comment, db, str(current_user.id))


@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if str(comment.author_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="You can only delete your own comments")
    db.delete(comment)
    db.commit()
    return None