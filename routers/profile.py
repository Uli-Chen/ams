from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path
import time

from database import get_db
from security import get_current_user
from models import User
from schemas import UserMeResponse, ProfileUpdateRequest, PasswordChangeRequest
from routers.auth import get_password_hash, verify_password

router = APIRouter()

AVATAR_DIR = Path("static") / "avatars"
ALLOWED_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
MAX_AVATAR_BYTES = 2 * 1024 * 1024  # 2MB


@router.get("/me", response_model=UserMeResponse)
async def me(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserMeResponse)
async def update_profile(
    payload: ProfileUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(current_user, k, v)
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.put("/me/password")
async def change_password(
    payload: PasswordChangeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    current_user.hashed_password = get_password_hash(payload.new_password)
    await db.commit()
    return {"message": "Password updated"}


@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTS:
        raise HTTPException(status_code=400, detail="Unsupported image type")

    contents = await file.read()
    if len(contents) > MAX_AVATAR_BYTES:
        raise HTTPException(status_code=400, detail="Avatar too large (max 2MB)")

    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"user_{current_user.id}_{int(time.time())}{suffix}"
    file_path = AVATAR_DIR / filename
    file_path.write_bytes(contents)

    current_user.avatar_url = f"/static/avatars/{filename}"
    await db.commit()
    await db.refresh(current_user)
    return {"avatar_url": current_user.avatar_url}

