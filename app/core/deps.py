from collections.abc import Generator
from supabase import Client

from app.db.session import supabase


def get_supabase() -> Generator[Client, None, None]:
    yield supabase
