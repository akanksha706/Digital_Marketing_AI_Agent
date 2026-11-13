"""API endpoints for poster generation and retrieval."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.db.session import get_db_session
from app.db.models import (
    Poster,
    Brand,
    User,
    UserRole,
    PostStatus,
    PosterRevision,
    ScheduledJob,
)
from app.domain.schemas.poster import GeneratePosterRequest, PosterResponse
from app.api.dependencies import get_generation_service
from app.core.errors import to_user_friendly_error
from app.services.generation_service import GenerationService
from app.services.google_calendar_service import GoogleCalendarService

router = APIRouter(prefix="/posters", tags=["Posters"])


async def _get_or_create_default_brand(db: AsyncSession, brand_id: int) -> Brand:
    """Ensure a brand exists for generation, creating a default one if not found."""
    brand = await db.get(Brand, brand_id)
    if not brand:
        brand = Brand(
            id=brand_id,
            team_name="Digital Marketing Team",
            primary_color="#f59e0b",
            secondary_color="#ffffff",
            font_family="Inter",
            tone_of_voice="inspiring and festive",
            banned_words=["spam", "unverified"],
            default_hashtags=["#DigitalMarketing", "#Creatives"],
        )
        db.add(brand)
        await db.flush()
    return brand


async def _get_or_create_default_user(db: AsyncSession, brand_id: int) -> User:
    """Ensure a creator user exists, creating a default one if not found."""
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            email="creator@company.com",
            hashed_password="hashed_dev_password",
            role=UserRole.MEMBER,
            brand_id=brand_id,
        )
        db.add(user)
        await db.flush()
    return user


@router.post(
    "/generate",
    response_model=PosterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a branded poster and copy from a single prompt",
)
async def generate_poster(
    payload: GeneratePosterRequest,
    db: AsyncSession = Depends(get_db_session),
    generation_service: GenerationService = Depends(get_generation_service),
):
    """Sanitize prompt, trigger parallel text & background AI jobs, composite poster, and persist."""
    try:
        brand = await _get_or_create_default_brand(db, payload.brand_id)
        user = await _get_or_create_default_user(db, brand.id)

        poster = await generation_service.generate_poster(
            raw_prompt=payload.prompt,
            brand=brand,
            created_by_id=user.id,
            db=db,
            aspect_ratio=payload.aspect_ratio,
        )
        await db.commit()
        await db.refresh(poster)
        return poster
    except ValueError as e:
        logger.warning("Poster generation validation warning: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=to_user_friendly_error(e, context="prompt input"),
        )
    except Exception as e:
        logger.error("ACTUAL INTERNAL EXCEPTION in poster generation [TERMINAL LOG]: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=to_user_friendly_error(e, context="poster generation"),
        )


@router.get(
    "/calendar-inspirations",
    summary="Fetch calendar-driven upcoming festival and event inspirations",
)
async def get_calendar_inspirations(
    limit: int = 5,
    category: Optional[str] = None,
    format: Optional[str] = "poster",
):
    """Return upcoming festivals dynamically fetched from official Google Calendar, adapted for poster or video."""
    return await GoogleCalendarService.get_upcoming_occasions(
        limit=limit, category=category, format_type=format
    )


@router.get(
    "/autocomplete",
    summary="Predictive prompt completion for Google Colab / Gmail style tab-to-type",
)
async def get_prompt_autocomplete(text: str = ""):
    """Return smart ghost-text completion suffix."""
    continuation = await GoogleCalendarService.get_smart_autocomplete(text)
    return {"completion": continuation or ""}


@router.get(
    "/{poster_id}",
    response_model=PosterResponse,
    summary="Retrieve poster details by ID",
)
async def get_poster(
    poster_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Fetch poster by primary key."""
    poster = await db.get(Poster, poster_id)
    if not poster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Poster with ID {poster_id} not found.",
        )
    return poster


@router.delete(
    "/{poster_id}",
    summary="Delete or archive a poster",
)
async def delete_poster(
    poster_id: int,
    force_hard_delete: bool = False,
    db: AsyncSession = Depends(get_db_session),
):
    """Delete unapproved drafts or soft-archive published posters to preserve Admin tracking."""
    poster = await db.get(Poster, poster_id)
    if not poster:
        # Idempotent delete: if already removed from database, succeed cleanly
        return {
            "message": f"Poster {poster_id} already deleted from database.",
            "status": "deleted",
            "id": poster_id,
        }

    # If the poster was already published and not explicitly force-purged by an Admin, soft-archive it
    if poster.status == PostStatus.PUBLISHED and not force_hard_delete:
        poster.is_archived = True
        await db.commit()
        return {
            "message": f"Poster {poster_id} was already published; archived to preserve Admin tracking & analytics.",
            "status": "archived",
            "id": poster_id,
        }

    # Delete revisions and scheduled jobs
    rev_query = await db.execute(select(PosterRevision).where(PosterRevision.poster_id == poster_id))
    for r in rev_query.scalars().all():
        await db.delete(r)

    job_query = await db.execute(select(ScheduledJob).where(ScheduledJob.poster_id == poster_id))
    for j in job_query.scalars().all():
        await db.delete(j)

    await db.delete(poster)
    await db.commit()
    return {"message": f"Poster {poster_id} successfully deleted", "status": "deleted", "id": poster_id}


@router.patch(
    "/{poster_id}/archive",
    response_model=PosterResponse,
    summary="Toggle archive state of a poster",
)
async def toggle_archive_poster(
    poster_id: int,
    archive: Optional[bool] = None,
    db: AsyncSession = Depends(get_db_session),
):
    """Archive or unarchive a poster."""
    poster = await db.get(Poster, poster_id)
    if not poster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Poster with ID {poster_id} not found.",
        )
    if archive is None:
        poster.is_archived = not poster.is_archived
    else:
        poster.is_archived = archive

    await db.commit()
    await db.refresh(poster)
    return poster


@router.get(
    "",
    response_model=List[PosterResponse],
    summary="List posters",
)
async def list_posters(
    skip: int = 0,
    limit: int = 20,
    include_archived: bool = False,
    archived_only: bool = False,
    db: AsyncSession = Depends(get_db_session),
):
    """Retrieve paginated list of generated posters with optional archive filtering."""
    query = select(Poster)
    if archived_only:
        query = query.where(Poster.is_archived == True)
    elif not include_archived:
        query = query.where(Poster.is_archived == False)

    result = await db.execute(
        query.order_by(Poster.created_at.desc()).offset(skip).limit(limit)
    )
    return result.scalars().all()
