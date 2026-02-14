import os
from urllib.parse import urlparse
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SQLITE_PATH = BASE_DIR / "fiksi.db"

# Override in env for Postgres/MySQL, e.g.:
# postgresql+psycopg://user:password@localhost:5432/fiksi_db
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH}")


def _derive_supabase_url_from_database_url(database_url: str | None) -> str | None:
    if not database_url:
        return None

    parsed = urlparse(database_url)
    host = parsed.hostname
    if not host or not host.endswith(".supabase.co"):
        return None

    # Supabase Postgres host is usually db.<project-ref>.supabase.co.
    if host.startswith("db."):
        host = host[3:]
    return f"https://{host}"


SUPABASE_URL = os.getenv("SUPABASE_URL") or _derive_supabase_url_from_database_url(DATABASE_URL)
SUPABASE_KEY = (
    os.getenv("SUPABASE_KEY")
    or os.getenv("SUPABASE_ANON_KEY")
    or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)
