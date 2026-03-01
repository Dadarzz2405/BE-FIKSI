from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def settings_coming_soon() -> dict[str, str]:
    return {
        "status": "coming_soon",
        "message": "Settings endpoints are coming soon.",
    }
