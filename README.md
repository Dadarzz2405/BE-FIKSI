## Database setup (Supabase)

### 1. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Supabase credentials

Set your Supabase project URL and API key:

```bash
export SUPABASE_URL="https://<project-ref>.supabase.co"
export SUPABASE_KEY="<anon-or-service-role-key>"
```

Optional: if `DATABASE_URL` points to Supabase Postgres, `SUPABASE_URL` is auto-derived.

### 3. Initialize DB client

```bash
python -m app.db.init_db
```

### 4. Run API

```bash
uvicorn app.main:app --reload
```

On startup, the app verifies Supabase client initialization via `init_db()`.
