# app/core/config.py
# Environment variable loading and application configuration

import os
# Utilities for file path handling
from pathlib import Path
# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Get base directory for database file location
BASE_DIR = Path(__file__).resolve().parent.parent
# Database connection URL from environment or fallback to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'fiksi.db'}")

# Supabase API endpoint
SUPABASE_URL = os.getenv("SUPABASE_URL", "")

# Anon key: public key for auth flows and RLS-respecting operations
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# Service role key: bypasses RLS, ONLY for server-side admin/storage operations
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# Legacy alias — kept so existing code that imports SUPABASE_KEY still works
# Points to anon key intentionally; service role is accessed explicitly
SUPABASE_KEY = SUPABASE_ANON_KEY

# Frontend URL for CORS and redirects
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Fail fast at startup rather than getting cryptic errors later
if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL environment variable is not set")
if not SUPABASE_ANON_KEY:
    raise RuntimeError("SUPABASE_ANON_KEY environment variable is not set")
if not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY environment variable is not set")