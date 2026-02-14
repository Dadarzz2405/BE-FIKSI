from app.db.session import supabase

def init_db() -> None:
    # Supabase manages schema externally (SQL editor, migrations, or CLI).
    # This call only verifies that the client is configured.
    _ = supabase


if __name__ == "__main__":
    init_db()
    print("Supabase client initialized.")
