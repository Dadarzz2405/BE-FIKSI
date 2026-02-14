"""Authentication service using Supabase Auth (not database operations)."""
from supabase import Client, create_client
from typing import Optional

from app.core.config import SUPABASE_URL, SUPABASE_KEY


class SupabaseAuthService:
    """Service for Supabase authentication operations only."""
    
    def __init__(self):
        self._client: Optional[Client] = None
        
    @property
    def client(self) -> Client:
        """Lazy-load Supabase client for auth operations."""
        if self._client is None:
            if not SUPABASE_URL or not SUPABASE_KEY:
                raise ValueError(
                    "Supabase credentials not configured. "
                    "Set SUPABASE_URL and SUPABASE_KEY environment variables."
                )
            self._client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return self._client
    
    def sign_up(self, email: str, password: str, redirect_url: Optional[str] = None):
        """Register a new user with Supabase Auth."""
        options = {"emailRedirectTo": redirect_url} if redirect_url else {}
        return self.client.auth.sign_up(
            email=email,
            password=password,
            options=options
        )
    
    def sign_in(self, email: str, password: str):
        """Sign in an existing user."""
        return self.client.auth.sign_in_with_password(
            email=email,
            password=password
        )
    
    def sign_out(self):
        """Sign out the current user."""
        return self.client.auth.sign_out()
    
    def get_user(self, access_token: str):
        """Get user information from access token."""
        return self.client.auth.get_user(access_token)


# Singleton instance
supabase_auth = SupabaseAuthService()