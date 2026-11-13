"""API endpoints for video generation and poster-to-reel motion synthesis."""

import logging
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_generation_service
from app.core.config import settings
from app.core.errors import to_user_friendly_error
from app.db.models import Brand, Poster
from app.db.session import get_db_session
from app.domain.schemas.poster import PosterResponse
from app.services.generation_service import GenerationService
from app.services.video_service import VideoGenerationResult, VideoService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/videos", tags=["Video Generation (Wan 2.1)"])


def get_video_service() -> VideoService:
    """Dependency provider for VideoService."""
    return VideoService()


class GenerateVideoRequest(BaseModel):
    """Payload to synthesize a short-form video reel from an approved poster."""
    poster_id: int = Field(..., description="Target poster ID to animate")
    duration_seconds: int = Field(default=14, ge=3, le=20, description="Video duration in seconds (3 to 20)")
    headline: Optional[str] = Field(default=None, description="Updated headline text")
    quote: Optional[str] = Field(default=None, description="Updated reflection quote text")
    headline_color: Optional[str] = Field(default=None, description="Headline text color")
    quote_color: Optional[str] = Field(default=None, description="Quote text color")
    accent_color: Optional[str] = Field(default=None, description="Accent color")
    y_percent: Optional[int] = Field(default=None, description="Vertical placement percentage (15 to 85)")
    scale: Optional[float] = Field(default=None, description="Text scale (0.6 to 1.7)")
    rotation: Optional[int] = Field(default=None, description="Rotation degrees")
    skip_diffusion: Optional[bool] = Field(default=False, description="Fast-render mode to update typography & colors without re-running neural diffusion")


class GenerateVideoFromPromptRequest(BaseModel):
    """Payload to synthesize an actionable video reel directly from a creative prompt."""
    prompt: str = Field(..., description="Prompt describing the creative video or social campaign")
    aspect_ratio: str = Field(default="9:16", description="Aspect ratio (9:16 for Reels, 1:1, etc.)")
    duration_seconds: int = Field(default=14, ge=3, le=20, description="Video duration in seconds (3 to 20)")
    creator_id: Optional[int] = Field(default=None, description="Creator user ID")
    skip_diffusion: Optional[bool] = Field(default=False, description="Fast-render mode to skip neural diffusion")


class GenerateVideoFromPromptResponse(BaseModel):
    """Result containing both poster metadata and generated video reel details."""
    poster: PosterResponse
    video: VideoGenerationResult


@router.post(
    "/generate-from-prompt",
    response_model=GenerateVideoFromPromptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate creative concept and action-ready video reel directly from prompt",
)
async def generate_video_from_prompt(
    payload: GenerateVideoFromPromptRequest,
    db: AsyncSession = Depends(get_db_session),
    generation_service: GenerationService = Depends(get_generation_service),
    video_service: VideoService = Depends(get_video_service),
):
    """Synthesizes creative poster artwork and an animated 9:16 video reel from prompt instructions."""
    # Resolve Brand configuration
    brand_res = await db.execute(select(Brand).limit(1))
    brand = brand_res.scalars().first()
    if not brand:
        brand = Brand(
            team_name="42 WORKS Studio",
            tone_of_voice="Inspirational & Authoritative",
            primary_color="#1E3A8A",
            secondary_color="#FFC20E",
        )
        db.add(brand)
        await db.flush()

    try:
        # Step 1: Generate high-resolution creative visual and copy
        poster = await generation_service.generate_poster(
            raw_prompt=payload.prompt.strip(),
            brand=brand,
            aspect_ratio=payload.aspect_ratio,
            db=db,
            created_by_id=payload.creator_id,
        )
        await db.commit()
        await db.refresh(poster)

        # Step 2: Resolve CLEAN background image (WITHOUT baked-in text) to prevent double/overlapping text
        image_rel = (poster.background_image_url or poster.final_poster_url or "").replace("/static/", "").lstrip("/\\")
        candidates = [
            Path(settings.LOCAL_STORAGE_DIR) / image_rel,
            Path(settings.LOCAL_STORAGE_DIR) / "posters" / Path(image_rel).name,
            Path("Backend/storage") / image_rel,
            Path("Backend/storage/posters") / Path(image_rel).name,
            Path("storage") / image_rel,
            Path("storage/posters") / Path(image_rel).name,
        ]
        local_image_path = None
        for c in candidates:
            if c.exists():
                local_image_path = c
                break

        if not local_image_path or not local_image_path.exists():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Rendered poster image file for '{image_rel}' not found on disk.",
            )

        # Step 3: Animate into 9:16 cinema-grade short-form video reel using autonomous layout
        layout = dict(poster.layout_meta or {})
        video_result = await video_service.generate_video_from_poster(
            poster_image_path=local_image_path,
            headline=poster.headline,
            quote=poster.quote or "",
            duration_seconds=payload.duration_seconds or 14,
            headline_color=layout.get("headline_color"),
            quote_color=layout.get("quote_color"),
            accent_color=layout.get("accent_color"),
            y_percent=layout.get("y"),
            scale=layout.get("scale"),
            rotation=layout.get("rotation"),
            prompt=poster.prompt,
            motion_prompt=layout.get("video_motion_prompt"),
            skip_diffusion=getattr(payload, "skip_diffusion", False) or False,
        )

        # Step 4: Persist video_url to the poster in the database
        poster.video_url = video_result.video_url
        await db.commit()
        await db.refresh(poster)

        return GenerateVideoFromPromptResponse(
            poster=PosterResponse.model_validate(poster),
            video=video_result,
        )
    except Exception as exc:
        await db.rollback()
        logger.error("ACTUAL INTERNAL EXCEPTION in direct prompt-to-video [TERMINAL LOG]: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=to_user_friendly_error(exc, context="video reel generation"),
        )


@router.post(
    "/from-poster",
    response_model=VideoGenerationResult,
    status_code=status.HTTP_201_CREATED,
    summary="Generate 9:16 short-form video reel from poster using Wan 2.1 / Wan 2.2",
)
async def generate_video_from_poster(
    payload: GenerateVideoRequest,
    db: AsyncSession = Depends(get_db_session),
    video_service: VideoService = Depends(get_video_service),
):
    """Animates a static poster into an engaging short-form video reel for Instagram Reels and LinkedIn Video."""
    poster = await db.get(Poster, payload.poster_id)
    if not poster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Poster with ID {payload.poster_id} not found.",
        )

    layout = dict(poster.layout_meta or {})
    if payload.headline:
        poster.headline = payload.headline.strip()
    if payload.quote:
        poster.quote = payload.quote.strip()
    if payload.headline_color:
        layout["headline_color"] = payload.headline_color
    if payload.quote_color:
        layout["quote_color"] = payload.quote_color
    if payload.accent_color:
        layout["accent_color"] = payload.accent_color
    if payload.y_percent is not None:
        layout["y"] = payload.y_percent
    if payload.scale is not None:
        layout["scale"] = payload.scale
    if payload.rotation is not None:
        layout["rotation"] = payload.rotation
    poster.layout_meta = layout

    # Crucial: Prefer clean background image without text so typography isn't doubled/ghosted
    image_rel = (poster.background_image_url or poster.final_poster_url or "").replace("/static/", "").lstrip("/\\")
    candidates = [
        Path(settings.LOCAL_STORAGE_DIR) / image_rel,
        Path(settings.LOCAL_STORAGE_DIR) / "posters" / Path(image_rel).name,
        Path("Backend/storage") / image_rel,
        Path("Backend/storage/posters") / Path(image_rel).name,
        Path("storage") / image_rel,
        Path("storage/posters") / Path(image_rel).name,
    ]
    local_image_path = None
    for c in candidates:
        if c.exists():
            local_image_path = c
            break

    if not local_image_path or not local_image_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source poster image file for '{image_rel}' not found on disk.",
        )

    resolved_headline_color = payload.headline_color or layout.get("headline_color")
    resolved_quote_color = payload.quote_color or layout.get("quote_color")
    resolved_accent_color = payload.accent_color or layout.get("accent_color")
    resolved_y_percent = payload.y_percent if payload.y_percent is not None else layout.get("y")
    resolved_scale = payload.scale if payload.scale is not None else layout.get("scale", 1.0)
    resolved_rotation = payload.rotation if payload.rotation is not None else layout.get("rotation", 0)

    try:
        result = await video_service.generate_video_from_poster(
            poster_image_path=local_image_path,
            headline=poster.headline,
            quote=poster.quote or "",
            duration_seconds=payload.duration_seconds or 14,
            headline_color=resolved_headline_color,
            quote_color=resolved_quote_color,
            accent_color=resolved_accent_color,
            y_percent=resolved_y_percent,
            scale=resolved_scale,
            rotation=resolved_rotation,
            prompt=poster.prompt,
            motion_prompt=layout.get("video_motion_prompt"),
            skip_diffusion=getattr(payload, "skip_diffusion", False) or False,
        )
        # Persist video_url on the poster
        poster.video_url = result.video_url
        await db.commit()
        await db.refresh(poster)
        return result
    except Exception as exc:
        logger.error("ACTUAL INTERNAL EXCEPTION in video from poster [TERMINAL LOG]: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=to_user_friendly_error(exc, context="video motion animation"),
        )
