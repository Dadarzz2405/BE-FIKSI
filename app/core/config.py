# app/core/config.py
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'fiksi.db'}")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")

# Anon key: public key for auth flows and RLS-respecting operations
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# Service role key: bypasses RLS, ONLY for server-side admin/storage operations
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# Legacy alias — kept so existing code that imports SUPABASE_KEY still works
# Points to anon key intentionally; service role is accessed explicitly
SUPABASE_KEY = SUPABASE_ANON_KEY

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Fail fast at startup rather than getting cryptic errors later
if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL environment variable is not set")
if not SUPABASE_ANON_KEY:
    raise RuntimeError("SUPABASE_ANON_KEY environment variable is not set")
if not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY environment variable is not set")