import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SQLITE_PATH = BASE_DIR / "fiksi.db"

# Override in env for Postgres/MySQL, e.g.:
# postgresql+psycopg://user:password@localhost:5432/fiksi_db
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH}")
