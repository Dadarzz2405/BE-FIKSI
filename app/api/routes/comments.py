from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List

from app.db.session import get_db
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.core.auth_service import supabase_auth

router = APIRouter()


# ============================================================================
# SCHEMAS
# ============================================================================

class CommentCreate(BaseModel):
    content: str


class CommentAuthor(BaseModel):
    username: str
    avatar_url: Optional[str]
    real_name: Optional[str]


class CommentResponse(BaseModel):
    id: str
    post_id: str
    content: str
    is_accepted: bool
    created_at: str
    author_id: str
    author: Optional[CommentAuthor]

    class Config:
        from_attributes = True


# ============================================================================
# AUTH DEPENDENCY (same pattern as posts)
# ============================================================================

def get_current_user(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    token = authorization.replace("Bearer ", "")
    try:
        auth_user = supabase_auth.get_user(token)
        if not auth_user.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication failed")

    user = db.query(User).filter(User.id == auth_user.user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")
    return user


def _comment_to_response(c: Comment) -> CommentResponse:
    author = None
    if c.author:
        author = CommentAuthor(
            username=c.author.username,
            avatar_url=c.author.avatar_url,
            real_name=c.author.real_name,
        )
    return CommentResponse(
        id=str(c.id),
        post_id=str(c.post_id),
        content=c.content,
        is_accepted=c.is_accepted,
        created_at=c.created_at.isoformat(),
        author_id=str(c.author_id),
        author=author,
    )


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/posts/{post_id}/comments", response_model=List[CommentResponse])
def list_comments(post_id: str, db: Session = Depends(get_db)):
    """List all comments/answers for a post. Accepted answer shown first."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comments = (
        db.query(Comment)
        .filter(Comment.post_id == post_id)
        .order_by(desc(Comment.is_accepted), Comment.created_at)
        .all()
    )
    return [_comment_to_response(c) for c in comments]


@router.post("/posts/{post_id}/comments", response_model=CommentResponse, status_code=201)
def create_comment(
    post_id: str,
    body: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add an answer/comment to a post."""
    post = db.query(Post).filter(Post.id == post_id, Post.is_published == True).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if not body.content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty")

    comment = Comment(
        post_id=post.id,
        author_id=current_user.id,
        content=body.content.strip(),
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return _comment_to_response(comment)


@router.patch("/comments/{comment_id}/accept", response_model=CommentResponse)
def accept_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a comment as the accepted/best answer. Only the post author can do this."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    post = db.query(Post).filter(Post.id == comment.post_id).first()
    if not post or str(post.author_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Only the post author can accept answers")

    # Unaccept any previously accepted comment on this post
    db.query(Comment).filter(
        Comment.post_id == comment.post_id,
        Comment.is_accepted == True,
    ).update({"is_accepted": False})

    comment.is_accepted = True
    db.commit()
    db.refresh(comment)
    return _comment_to_response(comment)


@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a comment. Only the comment author can delete."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if str(comment.author_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="You can only delete your own comments")

    db.delete(comment)
    db.commit()
    return None