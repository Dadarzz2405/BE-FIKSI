# app/core/auth_service.py
from urllib.parse import urlencode
from supabase import Client, create_client
from typing import Optional
from app.core.config import SUPABASE_URL, SUPABASE_ANON_KEY  # ← anon key only


class SupabaseAuthService:
    def __init__(self):
        self._client: Optional[Client] = None

    @property
    def client(self) -> Client:
        if self._client is None:
            # Auth service always uses the anon key — it validates user JWTs,
            # which Supabase checks against its own secret, not your service key.
            self._client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        return self._client

    def sign_up(self, email: str, password: str, redirect_url: Optional[str] = None):
        credentials: dict = {"email": email, "password": password}
        if redirect_url:
            credentials["options"] = {"emailRedirectTo": redirect_url}
        return self.client.auth.sign_up(credentials)

    def sign_in(self, email: str, password: str):
        return self.client.auth.sign_in_with_password({"email": email, "password": password})

    def sign_out(self):
        return self.client.auth.sign_out()

    def get_user(self, access_token: str):
        return self.client.auth.get_user(access_token)

    def get_oauth_sign_in_url(self, provider: str, redirect_to: str) -> str:
        base = SUPABASE_URL.rstrip("/")
        params = urlencode({"provider": provider, "redirect_to": redirect_to})
        return f"{base}/auth/v1/authorize?{params}"


supabase_auth = SupabaseAuthService()