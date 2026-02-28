# app/core/config.py
# Environment variable loading and application configuration

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Environment toggle ───────────────────────────────────────
# Set APP_ENV=dev or APP_ENV=prod in .env (default: dev)
APP_ENV = os.getenv("APP_ENV", "dev").lower()

if APP_ENV not in ("dev", "prod"):
    raise RuntimeError(f"APP_ENV must be 'dev' or 'prod', got '{APP_ENV}'")

_is_prod = APP_ENV == "prod"
_prefix = "PROD" if _is_prod else "DEV"

# ── Resolved config values ───────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_URL = os.getenv(
    f"{_prefix}_DATABASE_URL",
    f"sqlite:///{BASE_DIR / 'fiksi.db'}",
)

SUPABASE_URL = os.getenv(f"{_prefix}_SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv(f"{_prefix}_SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv(f"{_prefix}_SUPABASE_SERVICE_ROLE_KEY", "")

# Legacy alias kept for backward compatibility
SUPABASE_KEY = SUPABASE_ANON_KEY

# Frontend URL for CORS and redirects
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# ── Startup validation ───────────────────────────────────────
if not SUPABASE_URL:
    raise RuntimeError(f"{_prefix}_SUPABASE_URL is not set in .env")
if not SUPABASE_ANON_KEY:
    raise RuntimeError(f"{_prefix}_SUPABASE_ANON_KEY is not set in .env")
if not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError(f"{_prefix}_SUPABASE_SERVICE_ROLE_KEY is not set in .env")

# Print active environment at startup
print(f"🌍 Running in {'⚠️  PRODUCTION' if _is_prod else '🛠️  DEV'} mode "
      f"(APP_ENV={APP_ENV})")