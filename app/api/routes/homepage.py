from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_homepage():
    return {
        "title": "Dadarzz FIKSI",
        "description": "Trying to make this work",
        "status": "ok"
    }
