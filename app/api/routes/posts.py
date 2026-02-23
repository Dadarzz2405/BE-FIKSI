from fastapi import APIRouter, Depends, HTTPException, Header, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
from datetime import datetime

from app.db.session import get_db
from app.models.post import Post
from app.models.user import User
from app.core.auth_service import supabase_auth

router = APIRouter()


# ============================================================================
# SCHEMAS
# ============================================================================

class PostCreate(BaseModel):
    title: str
    content: str
    excerpt: Optional[str] = None
    image_url: Optional[str] = None
    is_published: bool = True
    category_id: Optional[str] = None


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    image_url: Optional[str] = None
    is_published: Optional[bool] = None
    category_id: Optional[str] = None


class AuthorInfo(BaseModel):
    username: str
    real_name: Optional[str]
    avatar_url: Optional[str]


class CategoryInfo(BaseModel):
    id: str
    name: str
    slug: str
    icon: Optional[str]


class PostResponse(BaseModel):
    id: str
    title: str
    content: str
    excerpt: Optional[str]
    image_url: Optional[str]
    is_published: bool
    created_at: str
    updated_at: str
    author_id: str
    author: Optional[AuthorInfo] = None
    category_id: Optional[str] = None
    category: Optional[CategoryInfo] = None

    class Config:
        from_attributes = True


class PostListResponse(BaseModel):
    posts: List[PostResponse]
    total: int
    page: int
    limit: int


# ============================================================================
# AUTH DEPENDENCY
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


def _post_to_response(post: Post) -> PostResponse:
    author_info = None
    if post.author:
        author_info = AuthorInfo(
            username=post.author.username,
            real_name=post.author.real_name,
            avatar_url=post.author.avatar_url,
        )

    category_info = None
    if post.category:
        category_info = CategoryInfo(
            id=str(post.category.id),
            name=post.category.name,
            slug=post.category.slug,
            icon=post.category.icon,
        )

    return PostResponse(
        id=str(post.id),
        title=post.title,
        content=post.content,
        excerpt=post.excerpt,
        image_url=post.image_url,
        is_published=post.is_published,
        created_at=post.created_at.isoformat(),
        updated_at=post.updated_at.isoformat(),
        author_id=str(post.author_id),
        author=author_info,
        category_id=str(post.category_id) if post.category_id else None,
        category=category_info,
    )


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/", response_model=PostListResponse)
def list_posts(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    category_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """List all published posts, paginated. Optionally filter by category_id."""
    offset = (page - 1) * limit
    query = db.query(Post).filter(Post.is_published == True)
    if category_id:
        query = query.filter(Post.category_id == category_id)
    total = query.count()
    posts = (
        query.order_by(desc(Post.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )
    return PostListResponse(
        posts=[_post_to_response(p) for p in posts],
        total=total,
        page=page,
        limit=limit,
    )


# ✅ FIX: register both /my and /my/ so either URL works
@router.get("/my", response_model=PostListResponse)
@router.get("/my/", response_model=PostListResponse, include_in_schema=False)
def list_my_posts(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List posts by the authenticated user (published + drafts)."""
    offset = (page - 1) * limit
    query = db.query(Post).filter(Post.author_id == current_user.id)
    total = query.count()
    posts = (
        query.order_by(desc(Post.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )
    return PostListResponse(
        posts=[_post_to_response(p) for p in posts],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{post_id}", response_model=PostResponse)
def get_post(post_id: str, db: Session = Depends(get_db)):
    """Get a single published post by ID."""
    post = db.query(Post).filter(Post.id == post_id, Post.is_published == True).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return _post_to_response(post)


@router.post("/", response_model=PostResponse, status_code=201)
def create_post(
    body: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new post. Requires authentication."""
    import uuid as _uuid
    post = Post(
        title=body.title,
        content=body.content,
        excerpt=body.excerpt or body.content[:160],
        image_url=body.image_url,
        is_published=body.is_published,
        author_id=current_user.id,
        category_id=_uuid.UUID(body.category_id) if body.category_id else None,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return _post_to_response(post)


@router.put("/{post_id}", response_model=PostResponse)
def update_post(
    post_id: str,
    body: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a post. Only the author can edit."""
    import uuid as _uuid
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if str(post.author_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="You can only edit your own posts")

    if body.title is not None:
        post.title = body.title
    if body.content is not None:
        post.content = body.content
        if body.excerpt is None:
            post.excerpt = body.content[:160]
    if body.excerpt is not None:
        post.excerpt = body.excerpt
    if body.image_url is not None:
        post.image_url = body.image_url
    if body.is_published is not None:
        post.is_published = body.is_published
    if body.category_id is not None:
        post.category_id = _uuid.UUID(body.category_id) if body.category_id else None

    post.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(post)
    return _post_to_response(post)


@router.delete("/{post_id}", status_code=204)
def delete_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a post. Only the author can delete."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if str(post.author_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="You can only delete your own posts")

    db.delete(post)
    db.commit()
    return None