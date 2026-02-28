# Homepage routes for displaying feed, posts, and platform statistics
from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

# Import database session dependency and models
from app.db.session import get_db
from app.models.post import Post

# Create router for homepage endpoints
router = APIRouter()


# ── Response Models ────────────────────────────────────────────────────────────

class HomepagePostResponse(BaseModel):
    """Schema for post items shown on homepage."""
    id: str
    title: str
    description: Optional[str] = None
    created_at: str
    author: Optional[str] = None
    image_url: Optional[str] = None

    class Config:
        from_attributes = True


class HomepageStats(BaseModel):
    """Schema for platform statistics."""
    total_quizzes: int
    published_quizzes: int
    draft_quizzes: int


class HomepageResponse(BaseModel):
    """Schema for full homepage response."""
    title: str
    description: str
    status: str
    stats: HomepageStats
    featured_sections: List[str]


class HomepageFeedResponse(BaseModel):
    """Schema for homepage feed (latest + popular posts)."""
    status: str
    latest_post: Optional[HomepagePostResponse]
    popular_posts: List[HomepagePostResponse]


# ── Helper Functions ──────────────────────────────────────────────────────────

def _fetch_published_posts(
    db: Session,
    limit: int,
) -> List[HomepagePostResponse]:
    """Fetch published posts from database, ordered by newest first."""
    try:
        # Query published posts, ordered by creation date (newest first)
        posts = (
            db.query(Post)
            .filter(Post.is_published == True)
            .order_by(desc(Post.created_at))
            .limit(limit)
            .all()
        )
        
        # Convert to response schema
        return [
            HomepagePostResponse(
                id=str(post.id),
                title=post.title,
                description=post.excerpt,
                created_at=post.created_at.isoformat(),
                author=post.author.username if post.author else None,
                image_url=post.image_url,
            )
            for post in posts
        ]
    except Exception as exc:
        print(f"Error fetching posts: {exc}")
        return []


def _build_homepage_payload() -> HomepageResponse:
    """Build static homepage payload with platform info."""
    return HomepageResponse(
        title="Dadarzz FIKSI",
        description="Prototype.",
        status="ok",
        stats=HomepageStats(
            total_quizzes=0,
            published_quizzes=0,
            draft_quizzes=0,
        ),
        featured_sections=[
            "Latest Quizzes",
            "Trending Topics",
            "Your Drafts",
        ],
    )


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/health")
def homepage_health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "homepage router ready"}


@router.get("/", response_model=HomepageFeedResponse)
def get_homepage(
    popular_limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
) -> HomepageFeedResponse:
    """Get homepage feed with latest and popular posts."""
    # Fetch posts (one extra to separate latest from popular)
    posts = _fetch_published_posts(db=db, limit=max(popular_limit, 1) + 1)
    # First post is the latest
    latest_post = posts[0] if posts else None
    # Remaining posts are popular
    popular_posts = posts[1 : popular_limit + 1] if posts else []

    return HomepageFeedResponse(
        status="ok",
        latest_post=latest_post,
        popular_posts=popular_posts,
    )


@router.get("/posts", response_model=List[HomepagePostResponse])
def get_homepage_posts(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> List[HomepagePostResponse]:
    """Get all published posts with optional limit."""
    return _fetch_published_posts(db=db, limit=limit)