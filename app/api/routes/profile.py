from fastapi import APIRouter
from pydantic import BaseModel
from supabase import Client
from typing import List, Optional
from app.db.session import supabase
from datetime import datetime
router = APIRouter()

def get_supabase() -> Client:
    return supabase

class ShowProfile(BaseModel):
    id: int
    real_name: str
    username: str
    avatar_url: str
    bio: Optional[str]
    is_active: bool
    created_at: datetime