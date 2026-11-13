"""API endpoints for user custom image uploads with Llama-Guard 3 moderation."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_custom_image_service
from app.core.errors import to_user_friendly_error
from app.db.models import Brand
from app.db.session import get_db_session
from app.domain.schemas.poster import PosterResponse
from app.services.custom_upload_service import CustomImageService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/custom-creatives", tags=["Custom Image Uploads"])


@router.post(
    "/upload-and-generate",
    response_model=PosterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload custom image and generate poster with Llama-Guard 3 safety verification",
)
async def upload_and_generate_poster(
    image: UploadFile = File(..., description="User uploaded image file (PNG, JPG, WEBP)"),
    prompt: str = Form(..., description="Creative prompt, occasion, or product instructions"),
    aspect_ratio: str = Form("1:1", description="Aspect ratio (1:1, 4:5, 16:9, etc.)"),
    creator_id: Optional[int] = Form(None, description="Creator user ID"),
    db: AsyncSession = Depends(get_db_session),
    custom_service: CustomImageService = Depends(get_custom_image_service),
):
    """Verifies prompt with Llama-Guard 3, uploads user image, crafts copy, and returns finalized poster."""
    # Validate image mime type
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a valid image (PNG, JPG, JPEG, WEBP).",
        )

    # Resolve Brand configuration
    brand_res = await db.execute(select(Brand).limit(1))
    brand = brand_res.scalars().first()
    if not brand:
        brand = Brand(
            team_name="42 WORKS Studio",
            tone_of_voice="Inspirational & Celebratory",
            primary_color="#1E3A8A",
            secondary_color="#FFC20E",
        )
        db.add(brand)
        await db.flush()

    try:
        image_bytes = await image.read()
        poster = await custom_service.generate_from_uploaded_image(
            image_bytes=image_bytes,
            prompt=prompt.strip(),
            brand=brand,
            aspect_ratio=aspect_ratio,
            db=db,
            creator_id=creator_id,
            filename=image.filename,
        )
        await db.commit()
        await db.refresh(poster)
        return PosterResponse.model_validate(poster)
    except ValueError as val_err:
        await db.rollback()
        logger.warning("Custom upload validation warning: %s", val_err)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=to_user_friendly_error(val_err, context="custom image request"),
        )
    except Exception as exc:
        await db.rollback()
        logger.error("ACTUAL INTERNAL EXCEPTION in custom_creatives [TERMINAL LOG]: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=to_user_friendly_error(exc, context="poster creation"),
        )
