from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel
from typing import List, Optional
from supabase import Client  # Make sure supabase-py is installed
from app.db.session import supabase
router = APIRouter()

def get_supabase() -> Client:
    return supabase
class HomepagePostResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    created_at: str
    author: Optional[str]

class HomepageStats(BaseModel):
    total_quizzes: int
    published_quizzes: int
    draft_quizzes: int

class HomepageResponse(BaseModel):
    title: str
    description: str
    status: str
    stats: HomepageStats
    featured_sections: List[str]

class HomepageFeedResponse(BaseModel):
    status: str
    latest_post: Optional[HomepagePostResponse]
    popular_posts: List[HomepagePostResponse]

def _fetch_published_posts(
    supabase: Client,
    limit: int,
) -> List[HomepagePostResponse]:
    try:
        response = (
            supabase.table("posts")
            .select("*")
            .eq("status", "published")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        posts = response.data or []
        return [HomepagePostResponse(**post) for post in posts]
    except Exception as exc:
        print(f"Error fetching posts: {exc}")
        return []


def _build_homepage_payload() -> HomepageResponse:
    return HomepageResponse(
        title="Dadarzz FIKSI",
        description="Build, publish, and manage quizzes in one place.",
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

@router.get("/health")
def homepage_health() -> dict[str, str]:
    return {"status": "homepage router ready"}


@router.get("/", response_model=HomepageFeedResponse)
def get_homepage(
    popular_limit: int = Query(default=5, ge=1, le=20),
    supabase: Client = Depends(get_supabase),
) -> HomepageFeedResponse:
    posts = _fetch_published_posts(supabase=supabase, limit=max(popular_limit, 1) + 1)
    latest_post = posts[0] if posts else None
    popular_posts = posts[1 : popular_limit + 1] if posts else []

    return HomepageFeedResponse(
        status="ok",
        latest_post=latest_post,
        popular_posts=popular_posts,
    )


@router.get("/posts", response_model=List[HomepagePostResponse])
def get_homepage_posts(
    limit: int = Query(default=10, ge=1, le=50),
    supabase: Client = Depends(get_supabase),
) -> List[HomepagePostResponse]:
    return _fetch_published_posts(supabase=supabase, limit=limit)
