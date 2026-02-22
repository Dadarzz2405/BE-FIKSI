from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional, List

from app.db.session import get_db
from app.models.category import Category
from app.models.post import Post

router = APIRouter()


# ============================================================================
# SCHEMAS
# ============================================================================

class CategoryResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str]
    icon: Optional[str]
    post_count: int = 0

    class Config:
        from_attributes = True


class CategoryListResponse(BaseModel):
    categories: List[CategoryResponse]
    total: int


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/", response_model=CategoryListResponse)
def list_categories(db: Session = Depends(get_db)):
    """List all categories with their post counts."""
    categories = db.query(Category).order_by(Category.name).all()

    result = []
    for cat in categories:
        count = (
            db.query(func.count(Post.id))
            .filter(Post.category_id == cat.id, Post.is_published == True)
            .scalar()
        ) or 0
        result.append(CategoryResponse(
            id=str(cat.id),
            name=cat.name,
            slug=cat.slug,
            description=cat.description,
            icon=cat.icon,
            post_count=count,
        ))

    return CategoryListResponse(categories=result, total=len(result))


@router.get("/{slug}", response_model=CategoryResponse)
def get_category(slug: str, db: Session = Depends(get_db)):
    """Get a single category by slug."""
    cat = db.query(Category).filter(Category.slug == slug).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    count = (
        db.query(func.count(Post.id))
        .filter(Post.category_id == cat.id, Post.is_published == True)
        .scalar()
    ) or 0

    return CategoryResponse(
        id=str(cat.id),
        name=cat.name,
        slug=cat.slug,
        description=cat.description,
        icon=cat.icon,
        post_count=count,
    )


@router.get("/{slug}/posts")
def get_posts_by_category(
    slug: str,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Get all published posts in a category."""
    cat = db.query(Category).filter(Category.slug == slug).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    offset = (page - 1) * limit
    query = db.query(Post).filter(
        Post.category_id == cat.id,
        Post.is_published == True,
    )
    total = query.count()
    posts = query.order_by(desc(Post.created_at)).offset(offset).limit(limit).all()

    return {
        "category": {"id": str(cat.id), "name": cat.name, "slug": cat.slug, "icon": cat.icon},
        "posts": [
            {
                "id": str(p.id),
                "title": p.title,
                "excerpt": p.excerpt,
                "image_url": p.image_url,
                "created_at": p.created_at.isoformat(),
                "author": {
                    "username": p.author.username,
                    "avatar_url": p.author.avatar_url,
                } if p.author else None,
            }
            for p in posts
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }