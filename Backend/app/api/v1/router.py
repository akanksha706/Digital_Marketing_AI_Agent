"""Central API v1 router consolidating all domain endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db_session
from app.api.v1.endpoints import (
    posters,
    reviews,
    schedules,
    admin,
    auth,
    assistant,
    linkedin_oauth,
    url_campaigns,
    custom_creatives,
    videos,
)

api_router = APIRouter()

# System endpoints
@api_router.get("/health", tags=["System"])
async def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "service": "AI Poster & Social Content Studio",
        "version": "1.0.0",
    }

# Studio Guide Steps (Stored in PostgreSQL `studio_guides` table)
@api_router.get("/studio/guide-steps", tags=["Studio Guide"])
async def get_studio_guide_steps(db: AsyncSession = Depends(get_db_session)):
    """Fetch live step-by-step studio guide stored in PostgreSQL studio_guides table."""
    result = await db.execute(
        text("SELECT id, step_number, title, badge, short_description, detailed_instructions, icon, feature_highlight FROM studio_guides ORDER BY step_number ASC")
    )
    rows = result.mappings().all()
    return [dict(r) for r in rows]

# Domain endpoints
api_router.include_router(auth.router)
api_router.include_router(posters.router)
api_router.include_router(reviews.router)
api_router.include_router(schedules.router)
api_router.include_router(admin.router)
api_router.include_router(assistant.router)
api_router.include_router(linkedin_oauth.router)
api_router.include_router(url_campaigns.router)
api_router.include_router(custom_creatives.router)
api_router.include_router(videos.router)
