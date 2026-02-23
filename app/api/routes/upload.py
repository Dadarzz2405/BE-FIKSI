# app/api/routes/upload.py
import uuid
import mimetypes
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query

from app.models.user import User
from app.api.dependencies import get_current_active_user
from app.core.storage_service import (
    upload_file, ALLOWED_IMAGE_TYPES, MAX_FILE_SIZE, EXTENSION_MAP, VALID_BUCKETS
)

router = APIRouter()


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    bucket: str = Query(default="post-images"),
    current_user: User = Depends(get_current_active_user),
):
    if bucket not in VALID_BUCKETS:
        raise HTTPException(status_code=400, detail=f"Invalid bucket. Choose from: {VALID_BUCKETS}")

    content_type = file.content_type or "image/jpeg"
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, GIF, or WebP images are allowed")

    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large — maximum 5 MB")

    ext = EXTENSION_MAP.get(content_type, ".jpg")
    filename = f"{uuid.uuid4()}{ext}"

    try:
        url = upload_file(bucket, filename, data, content_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"url": url, "filename": filename}