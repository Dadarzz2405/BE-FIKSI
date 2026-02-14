from fastapi import APIRouter, FastAPI, HTTPException
from app.db.session import supabase
from pydantic import BaseModel, EmailStr
import os
from dotenv import load_dotenv
load_dotenv()
app = FastAPI()
router = APIRouter()

ENV = os.getenv("ENV", "local")  # set ENV=prod in production
REDIRECT_URL = os.getenv("REDIRECT_URL_PROD") if ENV == "prod" else os.getenv("REDIRECT_URL_LOCAL")

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str

@router.get("/health")
def auth_health() -> dict[str, str]:
    return {"status": "auth router ready"}

@router.post("/signup")
def signup(req: SignUpRequest):
    try:
        user = supabase.auth.sign_up(
            email=req.email,
            password=req.password,
            options={"emailRedirectTo": REDIRECT_URL} 
        )
        return {"message": "Signup successful! Please check your email to verify."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
app.include_router(router, prefix="/auth")