# app/core/storage_service.py
from functools import lru_cache
from supabase import create_client, Client
from app.core.config import SUPABASE_URL, SERVICE_ROLE_KEY

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
EXTENSION_MAP = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}
VALID_BUCKETS = {"post-images", "avatars"}


def _bucket_name(bucket) -> str:
    """Support supabase-py returning bucket dicts or typed objects."""
    if isinstance(bucket, dict):
        return str(bucket.get("name", ""))
    return str(getattr(bucket, "name", ""))


@lru_cache(maxsize=1)
def get_storage_client() -> Client:
    """
    Returns a singleton Supabase client initialized with the service role key.
    This client bypasses RLS and is safe ONLY for server-side use.
    Never pass this client or its key to frontend code.
    """
    if not SERVICE_ROLE_KEY:
        raise RuntimeError("SERVICE_ROLE_KEY is not set for privileged storage operations")
    return create_client(SUPABASE_URL, SERVICE_ROLE_KEY)


def ensure_bucket_exists(bucket_name: str, public: bool = True) -> None:
    """
    Idempotently ensure a storage bucket exists with correct visibility.
    Called once per upload rather than at startup, since bucket creation
    is cheap and avoids needing a lifespan hook.
    """
    client = get_storage_client()
    try:
        existing = client.storage.list_buckets()
        existing_names = {_bucket_name(b) for b in (existing or [])}
        if bucket_name not in existing_names:
            client.storage.create_bucket(bucket_name, options={"public": public})
    except Exception as e:
        # Non-fatal: bucket may already exist or another instance created it
        # Log but don't crash — the upload attempt will surface the real error
        print(f"[storage] ensure_bucket_exists warning for '{bucket_name}': {e}")


def upload_file(bucket_name: str, filename: str, data: bytes, content_type: str) -> str:
    """
    Upload bytes to Supabase Storage and return the public URL.
    Raises ValueError for invalid inputs, RuntimeError for upload failures.
    """
    if bucket_name not in VALID_BUCKETS:
        raise ValueError(f"Invalid bucket '{bucket_name}'. Must be one of: {VALID_BUCKETS}")
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError(f"Unsupported content type '{content_type}'")
    if len(data) > MAX_FILE_SIZE:
        raise ValueError(f"File too large: {len(data)} bytes (max {MAX_FILE_SIZE})")

    ensure_bucket_exists(bucket_name, public=True)
    client = get_storage_client()

    try:
        client.storage.from_(bucket_name).upload(
            filename,
            data,
            file_options={"content-type": content_type, "upsert": "true"},
        )
    except Exception as e:
        raise RuntimeError(f"Storage upload failed: {e}") from e

    return client.storage.from_(bucket_name).get_public_url(filename)
