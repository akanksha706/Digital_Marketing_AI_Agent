"""API endpoints for poster review, plain-language edits, and approval locks."""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import to_user_friendly_error

logger = logging.getLogger(__name__)

from app.db.session import get_db_session
from app.db.models import Poster
from app.domain.schemas.poster import PosterResponse
from app.domain.schemas.review import (
    EditPosterRequest,
    ApprovalRequest,
    RejectRequest,
    RevisionResponse,
    ReviewActionResponse,
)
from app.api.dependencies import get_review_service
from app.services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["Reviews & Approvals"])


@router.post(
    "/{poster_id}/edit",
    response_model=PosterResponse,
    summary="Request revisions using plain language instructions or direct field edits",
)
@router.post(
    "/posters/{poster_id}/edit",
    response_model=PosterResponse,
    include_in_schema=False,
)
async def request_poster_edit(
    poster_id: int,
    payload: EditPosterRequest,
    db: AsyncSession = Depends(get_db_session),
    review_service: ReviewService = Depends(get_review_service),
):
    """Re-composite poster with updated copy from instructions or direct edits without re-generating background."""
    try:
        updated_poster = await review_service.apply_plain_language_edit(
            poster_id=poster_id,
            instruction=payload.instruction,
            headline=payload.headline,
            headline_y_ratio=payload.headline_y_ratio,
            headline_scale=payload.headline_scale,
            quote=payload.quote,
            quote_y_ratio=payload.quote_y_ratio,
            quote_scale=payload.quote_scale,
            caption=payload.caption,
            hashtags=payload.hashtags,
            layout_meta=payload.layout_meta,
            primary_color=payload.primary_color,
            secondary_color=payload.secondary_color,
            quote_color=payload.quote_color,
            user_id=payload.user_id,
            db=db,
        )
        return updated_poster
    except ValueError as e:
        logger.warning("Poster revision validation warning: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("ACTUAL INTERNAL EXCEPTION in poster revision [TERMINAL LOG]: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=to_user_friendly_error(e, context="poster revision"),
        )


@router.post(
    "/{poster_id}/approve",
    response_model=ReviewActionResponse,
    summary="Approve and lock poster for publishing",
)
@router.post(
    "/posters/{poster_id}/approve",
    response_model=ReviewActionResponse,
    include_in_schema=False,
)
async def approve_poster(
    poster_id: int,
    payload: ApprovalRequest = ApprovalRequest(reviewer_id=1),
    db: AsyncSession = Depends(get_db_session),
    review_service: ReviewService = Depends(get_review_service),
):
    """Lock poster state and unlock LinkedIn / Instagram publishing."""
    try:
        poster = await review_service.approve_poster(
            poster_id=poster_id,
            reviewer_id=payload.reviewer_id,
            notes=payload.notes,
            db=db,
        )
        return ReviewActionResponse(
            poster_id=poster.id,
            status=poster.status,
            message="Poster successfully approved and locked. Ready for publishing.",
            updated_at=poster.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{poster_id}/unlock",
    response_model=ReviewActionResponse,
    summary="Unlock an approved poster back to in-review for further edits",
)
@router.post(
    "/posters/{poster_id}/unlock",
    response_model=ReviewActionResponse,
    include_in_schema=False,
)
async def unlock_poster(
    poster_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Unlock poster state allowing revisions and modifications."""
    poster = await db.get(Poster, poster_id)
    if not poster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Poster not found")
    poster.status = PostStatus.IN_REVIEW
    poster.approval_locked_at = None
    await db.commit()
    await db.refresh(poster)
    return ReviewActionResponse(
        poster_id=poster.id,
        status=poster.status,
        message="Poster successfully unlocked for revisions.",
        updated_at=poster.updated_at,
    )


@router.get(
    "/posters",
    response_model=List[PosterResponse],
    summary="List posters for review or library",
)
async def list_review_posters(
    limit: int = 50,
    skip: int = 0,
    db: AsyncSession = Depends(get_db_session),
):
    """List recent posters for review modal or library."""
    query = (
        select(Poster)
        .order_by(desc(Poster.created_at))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.post(
    "/{poster_id}/reject",
    response_model=ReviewActionResponse,
    summary="Reject poster with reason",
)
async def reject_poster(
    poster_id: int,
    payload: RejectRequest,
    db: AsyncSession = Depends(get_db_session),
    review_service: ReviewService = Depends(get_review_service),
):
    """Mark poster as rejected."""
    try:
        poster = await review_service.reject_poster(
            poster_id=poster_id,
            reviewer_id=payload.reviewer_id,
            reason=payload.reason,
            db=db,
        )
        return ReviewActionResponse(
            poster_id=poster.id,
            status=poster.status,
            message=f"Poster marked as rejected: {payload.reason}",
            updated_at=poster.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{poster_id}/revisions",
    response_model=List[RevisionResponse],
    summary="Retrieve complete revision history for a poster",
)
async def get_poster_revisions(
    poster_id: int,
    db: AsyncSession = Depends(get_db_session),
    review_service: ReviewService = Depends(get_review_service),
):
    """Fetch chronological audit trail of all changes requested for this poster."""
    revisions = await review_service.get_revisions(poster_id=poster_id, db=db)
    return revisions
