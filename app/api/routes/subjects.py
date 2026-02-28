from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional, List
import uuid

from app.db.session import get_db
from app.models.academic_category import AcademicCategory
from app.models.subject import Subject
from app.models.post import Post

router = APIRouter()


# ============================================================================
# SCHEMAS
# ============================================================================

class SubjectResponse(BaseModel):
    id: str
    name: str
    slug: str
    icon: Optional[str]
    academic_category_id: str
    post_count: int = 0

    class Config:
        from_attributes = True


class SubjectListResponse(BaseModel):
    subjects: List[SubjectResponse]
    total: int


class CategoryGroupingResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str]
    icon: Optional[str]
    subjects: List[SubjectResponse]

    class Config:
        from_attributes = True


class GroupedSubjectsResponse(BaseModel):
    categories: List[CategoryGroupingResponse]
    total_categories: int
    total_subjects: int


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/", response_model=SubjectListResponse)
def list_subjects(db: Session = Depends(get_db)):
    """List all subjects with their post counts."""
    subjects = db.query(Subject).order_by(Subject.name).all()

    result = []
    for sub in subjects:
        count = (
            db.query(func.count(Post.id))
            .filter(Post.subject_id == sub.id, Post.is_published == True)
            .scalar()
        ) or 0
        result.append(SubjectResponse(
            id=str(sub.id),
            name=sub.name,
            slug=sub.slug,
            icon=sub.icon,
            academic_category_id=str(sub.academic_category_id),
            post_count=count,
        ))

    return SubjectListResponse(subjects=result, total=len(result))


@router.get("/grouped", response_model=GroupedSubjectsResponse)
def list_grouped_subjects(db: Session = Depends(get_db)):
    """List all academic categories with their nested subjects."""
    categories = db.query(AcademicCategory).order_by(AcademicCategory.name).all()
    
    result = []
    total_subjects = 0
    
    for cat in categories:
        subjects = db.query(Subject).filter(Subject.academic_category_id == cat.id).order_by(Subject.name).all()
        
        subject_responses = []
        for sub in subjects:
            count = (
                db.query(func.count(Post.id))
                .filter(Post.subject_id == sub.id, Post.is_published == True)
                .scalar()
            ) or 0
            subject_responses.append(SubjectResponse(
                id=str(sub.id),
                name=sub.name,
                slug=sub.slug,
                icon=sub.icon,
                academic_category_id=str(sub.academic_category_id),
                post_count=count,
            ))
            total_subjects += 1
            
        result.append(CategoryGroupingResponse(
            id=str(cat.id),
            name=cat.name,
            slug=cat.slug,
            description=cat.description,
            icon=cat.icon,
            subjects=subject_responses
        ))
        
    return GroupedSubjectsResponse(
        categories=result, 
        total_categories=len(result),
        total_subjects=total_subjects
    )


@router.get("/{slug}", response_model=SubjectResponse)
def get_subject(slug: str, db: Session = Depends(get_db)):
    """Get a single subject by slug."""
    sub = db.query(Subject).filter(Subject.slug == slug).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subject not found")

    count = (
        db.query(func.count(Post.id))
        .filter(Post.subject_id == sub.id, Post.is_published == True)
        .scalar()
    ) or 0

    return SubjectResponse(
        id=str(sub.id),
        name=sub.name,
        slug=sub.slug,
        icon=sub.icon,
        academic_category_id=str(sub.academic_category_id),
        post_count=count,
    )


@router.get("/{slug}/posts")
def get_posts_by_subject(
    slug: str,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Get all published posts in a subject."""
    sub = db.query(Subject).filter(Subject.slug == slug).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subject not found")

    offset = (page - 1) * limit
    query = db.query(Post).filter(
        Post.subject_id == sub.id,
        Post.is_published == True,
    )
    total = query.count()
    posts = query.order_by(desc(Post.created_at)).offset(offset).limit(limit).all()

    return {
        "subject": {
            "id": str(sub.id), 
            "name": sub.name, 
            "slug": sub.slug, 
            "icon": sub.icon,
            "academic_category_id": str(sub.academic_category_id)
        },
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
