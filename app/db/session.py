from supabase import Client, create_client

from app.core.config import SUPABASE_KEY, SUPABASE_URL


def create_supabase_client() -> Client:
    if not SUPABASE_URL:
        raise ValueError(
            "Missing SUPABASE_URL. Set SUPABASE_URL in your environment."
        )
    if not SUPABASE_KEY:
        raise ValueError(
            "Missing SUPABASE_KEY (or SUPABASE_ANON_KEY / SUPABASE_SERVICE_ROLE_KEY)."
        )
    return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase: Client = create_supabase_client()
