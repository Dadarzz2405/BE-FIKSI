from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def quizzes_coming_soon() -> dict[str, str]:
    return {
        "status": "coming_soon",
        "message": "Quizzes endpoints are coming soon.",
    }
