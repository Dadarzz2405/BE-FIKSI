# app/core/auth_service.py
# Supabase authentication service wrapper

from urllib.parse import urlencode
# Supabase Python client for authentication and data access
from supabase import Client, create_client
from typing import Optional
# Import configuration with Supabase credentials
from app.core.config import SUPABASE_URL, SUPABASE_ANON_KEY  # ← anon key only


# Singleton service class to manage Supabase authentication operations
class SupabaseAuthService:
    def __init__(self):
        # Lazy-loaded Supabase client instance
        self._client: Optional[Client] = None

    @property
    def client(self) -> Client:
        """Initialize and cache Supabase client on first access."""
        if self._client is None:
            # Auth service always uses the anon key — it validates user JWTs,
            # which Supabase checks against its own secret, not your service key.
            self._client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        return self._client

    def sign_up(self, email: str, password: str, redirect_url: Optional[str] = None):
        """Create a new user account with optional redirect URL for email confirmation."""
        credentials: dict = {"email": email, "password": password}
        if redirect_url:
            credentials["options"] = {"emailRedirectTo": redirect_url}
        return self.client.auth.sign_up(credentials)

    def sign_in(self, email: str, password: str):
        """Authenticate user with email and password."""
        return self.client.auth.sign_in_with_password({"email": email, "password": password})

    def sign_out(self):
        """Sign out the current user."""
        return self.client.auth.sign_out()

    def get_user(self, access_token: str):
        """Retrieve user info from a valid JWT access token."""
        return self.client.auth.get_user(access_token)

    def get_oauth_sign_in_url(self, provider: str, redirect_to: str) -> str:
        """Generate OAuth login URL for social authentication."""
        base = SUPABASE_URL.rstrip("/")
        params = urlencode({"provider": provider, "redirect_to": redirect_to})
        return f"{base}/auth/v1/authorize?{params}"


# Global singleton instance for authentication service
supabase_auth = SupabaseAuthService()