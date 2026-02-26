from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List

from app.db.session import get_db
from app.models.user import User
from app.core.gamification import get_rank

router = APIRouter()


class LeaderboardEntry(BaseModel):
    rank_position: int
    user_id:    str
    username:   str
    real_name:  str | None
    avatar_url: str | None
    level:      int
    xp_total:   int
    reputation: int
    cp_total:   int
    rank_name:  str
    rank_icon:  str


@router.get("/", response_model=List[LeaderboardEntry])
def get_leaderboard(
    sort_by: str = Query(
        default="reputation",
        regex="^(reputation|xp_total|cp_total|level)$",
        description="Sort column: reputation | xp_total | cp_total | level",
    ),
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    sort_col = {
        "reputation": User.reputation,
        "xp_total":   User.xp_total,
        "cp_total":   User.cp_total,
        "level":      User.level,
    }.get(sort_by, User.reputation)

    users = (
        db.query(User)
        .filter(User.is_active == True)
        .order_by(desc(sort_col))
        .limit(limit)
        .all()
    )

    return [
        LeaderboardEntry(
            rank_position=i + 1,
            user_id=str(u.id),
            username=u.username,
            real_name=u.real_name,
            avatar_url=u.avatar_url,
            level=u.level      or 1,
            xp_total=u.xp_total   or 0,
            reputation=u.reputation or 0,
            cp_total=u.cp_total   or 0,
            rank_name=get_rank(u.reputation or 0)["name"],
            rank_icon=get_rank(u.reputation or 0)["icon"],
        )
        for i, u in enumerate(users)
    ]