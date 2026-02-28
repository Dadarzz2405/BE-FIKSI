## Database setup (Supabase)

### 1. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Supabase credentials

Use environment-specific variables (`DEV_`/`PROD_`) and keep key roles separate:

```bash
export APP_ENV="dev"  # or prod
export DEV_SUPABASE_URL="https://<project-ref>.supabase.co"
export DEV_SUPABASE_ANON_KEY="<publishable-or-anon-key>"
export DEV_SUPABASE_SERVICE_ROLE_KEY="<service-role-key>" # server-only
```

Notes:
- `SERVICE_ROLE_KEY` (or `*_SUPABASE_SERVICE_ROLE_KEY`) is for backend/admin operations only.
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` is supported as anon-key input for frontend-safe usage.
- Never expose service role keys in frontend/public environments.

### 3. Initialize DB client

```bash
python -m app.db.init_db
```

### 4. Run API

```bash
uvicorn app.main:app --reload
```

On startup, the app validates Supabase URL + anon key. Privileged endpoints (storage/admin) require `SERVICE_ROLE_KEY`.
