"""
app/core/gamification.py

Unified points service for Nusa CoNex.
Three parallel currencies:
  XP  – drives levels, earned by everyone for participation
  REP – drives rank tier, earned by quality contributions
  CP  – Challenge Points, earned competitively (quizzes + best answers)

Event table
───────────────────────────────────────────────────────────
event                  XP    REP   CP    notes
───────────────────────────────────────────────────────────
post_created            5     2     0    asking a question
comment_created        10     5     0    posting an answer
comment_accepted       25    15    20    your answer is best
comment_upvoted         5     3     2    someone upvoted you
quiz_easy_pass         10     3     5    quiz score ≥ 60%
quiz_medium_pass       15     6    12
quiz_hard_pass         20    10    25
quiz_expert_pass       30    15    50
───────────────────────────────────────────────────────────
"""

from math import floor
from sqlalchemy.orm import Session


# ── Rank tiers (driven by CP — Challenge Points) ─────────────────────────────
# CP accumulates slowly (quizzes are the primary source), so tiers are
# intentionally challenging to reach. Reference rates for a dedicated user:
#   easy quiz = 5 CP  │  medium = 12  │  hard = 25  │  expert = 50
#   accepted answer = 20 CP  │  upvote = 2 CP
#
#  Bronze  → Silver  :  100 CP  (~8 medium quizzes passed)
#  Silver  → Gold    :  500 CP  (~20 hard quizzes passed)
#  Gold    → Platinum: 1500 CP  (~60 hard quizzes, or ~30 expert)
#  Platinum→ Diamond : 5000 CP  (~100 expert quizzes — elite only)

RANK_TIERS = [
    (5000, "Diamond",  "💎"),
    (1500, "Platinum", "⚡"),
    (500,  "Gold",     "🥇"),
    (100,  "Silver",   "🥈"),
    (0,    "Bronze",   "🥉"),
]

# ── Point awards per event ────────────────────────────────────────────────────

EVENTS: dict[str, tuple[int, int, int]] = {
    #                             XP   REP   CP
    "post_created":             (  5,   2,   0),
    "comment_created":          ( 10,   5,   0),
    "comment_accepted":         ( 25,  15,  20),
    "comment_upvoted":          (  5,   3,   2),
    "quiz_easy_pass":           ( 10,   3,   5),
    "quiz_medium_pass":         ( 15,   6,  12),
    "quiz_hard_pass":           ( 20,  10,  25),
    "quiz_expert_pass":         ( 30,  15,  50),
}

# ── Pure helpers ──────────────────────────────────────────────────────────────

def xp_for_level(level: int) -> int:
    """XP required to advance from `level` to `level + 1`."""
    return max(1, floor(100 * (level ** 1.5)))


def get_rank(cp_total: int) -> dict:
    """Return rank tier for a given CP (Challenge Points) total."""
    for threshold, name, icon in RANK_TIERS:
        if cp_total >= threshold:
            return {"name": name, "icon": icon, "min_cp": threshold}
    return {"name": "Bronze", "icon": "🥉", "min_cp": 0}


def next_rank_threshold(cp_total: int) -> int | None:
    """Return the CP needed for the next tier, or None if already Diamond."""
    for threshold, _, _ in reversed(RANK_TIERS):
        if cp_total < threshold:
            return threshold
    return None


def quiz_event_name(difficulty: str, score_pct: float) -> str | None:
    """
    Map a quiz result to an event name.
    Returns None if score < 60% (no reward for failing).
    """
    if score_pct < 0.60:
        return None
    mapping = {
        "easy":   "quiz_easy_pass",
        "medium": "quiz_medium_pass",
        "hard":   "quiz_hard_pass",
        "expert": "quiz_expert_pass",
    }
    return mapping.get(difficulty.lower())


# ── Main award function ───────────────────────────────────────────────────────

def award_points(user_id, event: str, db: Session) -> dict:
    """
    Award XP, REP, and CP to a user for a named event.
    Handles XP overflow and level-ups automatically.
    Returns a summary dict; returns {} for unknown events or missing users.
    """
    from app.models.user import User   # local import to avoid circular

    if event not in EVENTS:
        return {}

    xp_amount, rep_amount, cp_amount = EVENTS[event]

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {}

    levels_gained = 0

    # ── XP + level-up loop ────────────────────────────────────────────────
    user.xp_total   = (user.xp_total   or 0) + xp_amount
    user.xp_current = (user.xp_current or 0) + xp_amount

    while True:
        needed = xp_for_level(user.level or 1)
        if user.xp_current >= needed:
            user.xp_current -= needed
            user.level       = (user.level or 1) + 1
            levels_gained   += 1
        else:
            break

    # ── REP (floor = 0) ───────────────────────────────────────────────────
    user.reputation = max(0, (user.reputation or 0) + rep_amount)

    # ── CP (floor = 0) ────────────────────────────────────────────────────
    user.cp_total = max(0, (user.cp_total or 0) + cp_amount)

    db.commit()

    return {
        "event":         event,
        "xp_gained":     xp_amount,
        "rep_gained":    rep_amount,
        "cp_gained":     cp_amount,
        "leveled_up":    levels_gained > 0,
        "levels_gained": levels_gained,
        "new_level":     user.level,
        "new_xp":        user.xp_current,
        "new_rep":       user.reputation,
        "new_cp":        user.cp_total,
        "new_rank":      get_rank(user.cp_total),
    }


# ── Per-subject helpers ───────────────────────────────────────────────────────

def get_subject_rank(rp_total: int, subject_id, db: Session) -> dict:
    """
    Look up the rank tier for a given RP total within a specific subject.
    Falls back to hardcoded RANK_TIERS if no subject-specific ranks exist.
    """
    from app.models.subject_rank import SubjectRank

    ranks = (
        db.query(SubjectRank)
        .filter(SubjectRank.subject_id == subject_id)
        .order_by(SubjectRank.min_rp.desc())
        .all()
    )
    if ranks:
        for r in ranks:
            if rp_total >= r.min_rp:
                return {"name": r.name, "icon": r.icon, "min_rp": r.min_rp}
        # If nothing matched, return the lowest tier
        lowest = ranks[-1]
        return {"name": lowest.name, "icon": lowest.icon, "min_rp": lowest.min_rp}

    # Fallback to global rank tiers (using RP as if it were CP)
    return get_rank(rp_total)


def award_subject_points(user_id, subject_id, event: str, db: Session) -> dict:
    """
    Award XP and RP to a user for a specific subject, plus global rollup.
    - Subject progress: XP + RP (rank points drive per-subject rank)
    - Global User: XP + REP + CP (unchanged behavior)
    Returns a combined summary dict.
    """
    from app.models.user import User
    from app.models.user_subject_progress import UserSubjectProgress

    if event not in EVENTS:
        return {}

    xp_amount, rep_amount, cp_amount = EVENTS[event]

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {}

    # ── Global rollup (same as award_points) ──────────────────────────────
    levels_gained = 0
    user.xp_total   = (user.xp_total   or 0) + xp_amount
    user.xp_current = (user.xp_current or 0) + xp_amount

    while True:
        needed = xp_for_level(user.level or 1)
        if user.xp_current >= needed:
            user.xp_current -= needed
            user.level       = (user.level or 1) + 1
            levels_gained   += 1
        else:
            break

    user.reputation = max(0, (user.reputation or 0) + rep_amount)
    user.cp_total   = max(0, (user.cp_total   or 0) + cp_amount)

    # ── Per-subject progress ──────────────────────────────────────────────
    progress = (
        db.query(UserSubjectProgress)
        .filter(
            UserSubjectProgress.user_id    == user_id,
            UserSubjectProgress.subject_id == subject_id,
        )
        .first()
    )
    if not progress:
        progress = UserSubjectProgress(
            user_id=user_id,
            subject_id=subject_id,
        )
        db.add(progress)

    subject_levels_gained = 0
    progress.xp_total   = (progress.xp_total   or 0) + xp_amount
    progress.xp_current = (progress.xp_current or 0) + xp_amount

    while True:
        needed = xp_for_level(progress.level or 1)
        if progress.xp_current >= needed:
            progress.xp_current -= needed
            progress.level       = (progress.level or 1) + 1
            subject_levels_gained += 1
        else:
            break

    # RP = XP + REP combined for the subject rank (simple approach)
    progress.rank_points = (progress.rank_points or 0) + rep_amount + cp_amount

    db.commit()

    return {
        "event":                event,
        "xp_gained":            xp_amount,
        "rep_gained":           rep_amount,
        "cp_gained":            cp_amount,
        "leveled_up":           levels_gained > 0,
        "levels_gained":        levels_gained,
        "new_level":            user.level,
        "new_xp":               user.xp_current,
        "new_rep":              user.reputation,
        "new_cp":               user.cp_total,
        "new_rank":             get_rank(user.cp_total),
        "subject_level":        progress.level,
        "subject_xp":           progress.xp_current,
        "subject_rp":           progress.rank_points,
        "subject_leveled_up":   subject_levels_gained > 0,
        "subject_rank":         get_subject_rank(progress.rank_points, subject_id, db),
    }