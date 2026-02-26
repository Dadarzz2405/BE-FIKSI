"""
app/api/routes/quiz_submissions.py

Handles quiz answer submissions and awards XP / REP / CP based on
score percentage and difficulty.

Drop this alongside your existing quiz routes and register it in main.py:
    app.include_router(quiz_submissions.router, tags=["Quizzes"])
"""
# Core FastAPI imports for routing and dependency injection
from fastapi import APIRouter, Depends, HTTPException, Header
# Pydantic for request/response data validation
from pydantic import BaseModel
# SQLAlchemy for database sessions
from sqlalchemy.orm import Session
from typing import Optional

# Local imports for database, models, and authentication
from app.db.session import get_db
from app.models.user import User
from app.core.auth_service import supabase_auth
from app.core.gamification import award_points, quiz_event_name

# Create router instance for quiz submission endpoints
router = APIRouter()


# Request model for quiz submission data
class QuizSubmission(BaseModel):
    quiz_id:    str
    score:      int   # number of correct answers
    total:      int   # total number of questions
    difficulty: str   # "easy" | "medium" | "hard" | "expert"


# Response model containing quiz results and rewards earned
class QuizResult(BaseModel):
    score:      int
    total:      int
    score_pct:  float
    passed:     bool
    event:      Optional[str]
    xp_gained:  int = 0
    rep_gained: int = 0
    cp_gained:  int = 0
    leveled_up: bool = False
    new_level:  int = 1
    message:    str

# Dependency function to extract and validate the current user from JWT token
def get_current_user(authorization: str = Header(...), db: Session = Depends(get_db)) -> User:
    # Validate that the authorization header follows "Bearer <token>" format
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    # Extract the token by removing "Bearer " prefix
    token = authorization.replace("Bearer ", "")
    
    try:
        # Verify the token with Supabase and get user info
        resp = supabase_auth.get_user(token)
        if not resp.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication failed")
    
    # Query database for the user matching the token
    user = db.query(User).filter(User.id == resp.user.id).first()
    
    # Ensure user exists and is active
    if not user or not user.is_active:
        raise HTTPException(status_code=403, detail="User not found or inactive")
    return user


# POST endpoint to submit a completed quiz and calculate rewards
@router.post("/quizzes/submit", response_model=QuizResult)
def submit_quiz(
    body: QuizSubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submit a completed quiz and receive XP / REP / CP awards.

    Score threshold:  ≥ 60% to pass (earn points).
    Difficulty scales award amounts — see gamification.py EVENTS table.
    """
    # Validate that total questions is greater than 0
    if body.total <= 0:
        raise HTTPException(status_code=400, detail="total must be > 0")
    
    # Validate that score is within the range of total questions
    if not 0 <= body.score <= body.total:
        raise HTTPException(status_code=400, detail="score must be between 0 and total")

    # Calculate the percentage score (e.g., 15/20 = 0.75)
    score_pct = body.score / body.total
    
    # Determine the event type based on difficulty and score percentage
    event     = quiz_event_name(body.difficulty, score_pct)

    # If event is None, user didn't meet 60% threshold - return failed result
    if event is None:
        return QuizResult(
            score=body.score,
            total=body.total,
            score_pct=round(score_pct, 2),
            passed=False,
            event=None,
            message=f"Score {body.score}/{body.total} ({round(score_pct*100)}%) — need ≥60% to earn points.",
        )

    # Award points to the user based on the event type
    result = award_points(current_user.id, event, db)

    # Format difficulty label for a readable message
    difficulty_label = body.difficulty.capitalize()
    
    # Return successful result with all earned points and user progression info
    # Return successful result with all earned points and user progression info
    return QuizResult(
        score=body.score,
        total=body.total,
        score_pct=round(score_pct, 2),
        passed=True,
        event=event,
        xp_gained=result.get("xp_gained", 0),
        rep_gained=result.get("rep_gained", 0),
        cp_gained=result.get("cp_gained", 0),
        leveled_up=result.get("leveled_up", False),
        new_level=result.get("new_level", current_user.level or 1),
        # Create a celebratory message with emoji if user leveled up
        message=(
            f"{'🎉 Level up! ' if result.get('leveled_up') else ''}"
            f"{difficulty_label} quiz passed! "
            f"+{result['xp_gained']} XP · +{result['rep_gained']} REP · +{result['cp_gained']} CP"
        ),
    )