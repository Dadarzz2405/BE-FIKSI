## Database setup

### 1. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Choose database URL

Default (no env var) uses SQLite file at `app/fiksi.db`.

To use PostgreSQL instead:

```bash
export DATABASE_URL="postgresql+psycopg://USER:PASSWORD@localhost:5432/fiksi_db"
```

### 3. Create tables

```bash
python -m app.db.init_db
```

### 4. Run API

```bash
uvicorn app.main:app --reload
```

On startup, the app also runs table creation automatically via `init_db()`.
