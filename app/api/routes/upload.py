from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from sqlalchemy.orm import Session
import uuid
import mimetypes

from app.db.session import get_db
from app.models.user import User
from app.core.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from app.api.dependencies import get_current_active_user

router = APIRouter()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_SIZE = 5 * 1024 * 1024  # 5 MB


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    bucket: str = Query(default="post-images"),
    current_user: User = Depends(get_current_active_user),
):
    """Upload an image to Supabase Storage and return its public URL."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(status_code=500, detail="Storage not configured on server")

    content_type = file.content_type or "image/jpeg"
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, GIF, or WebP images are allowed")

    data = await file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File too large — maximum size is 5 MB")

    ext = mimetypes.guess_extension(content_type) or ".jpg"
    if ext == ".jpe":
        ext = ".jpg"
    filename = f"{uuid.uuid4()}{ext}"

    from supabase import create_client
    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    try:
        try:
            existing = client.storage.list_buckets()
            if not any(b["name"] == bucket for b in existing):
                client.storage.create_bucket(bucket, options={"public": True})
        except Exception:
            pass

        client.storage.from_(bucket).upload(
            filename,
            data,
            file_options={"content-type": content_type},
        )
        url = client.storage.from_(bucket).get_public_url(filename)
        return {"url": url, "filename": filename}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Upload failed: {exc}")