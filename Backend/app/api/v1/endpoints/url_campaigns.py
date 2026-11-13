"""API endpoints for URL scraping and automated campaign generation."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.errors import to_user_friendly_error

logger = logging.getLogger(__name__)

from app.db.session import get_db_session
from app.db.models import Brand, User, UserRole
from app.api.dependencies import get_url_campaign_service
from app.services.url_crawler_service import UrlCampaignService
from app.domain.schemas.poster import PosterResponse

router = APIRouter(prefix="/campaigns", tags=["URL Campaigns & Scraping"])


class ScrapeUrlRequest(BaseModel):
    """Payload to preview scraped webpage content."""
    url: str = Field(..., description="Target webpage URL to scrape and analyze")


class ScrapeUrlPreviewResponse(BaseModel):
    """Clean extracted content preview from a webpage."""
    url: str
    title: str
    description: Optional[str] = None
    extracted_text: str
    source_type: str


class GenerateFromUrlRequest(BaseModel):
    """Payload to synthesize a complete poster campaign from a URL."""
    url: str = Field(..., description="Target webpage or product URL")
    aspect_ratio: str = Field(default="1:1", description="Target aspect ratio: 1:1, 4:5, 16:9, etc.")
    custom_instructions: Optional[str] = Field(
        default=None,
        description="Optional custom angle (e.g. 'Focus on the 20% discount' or 'Write an executive tech summary')",
    )
    creator_id: Optional[int] = Field(default=None, description="Creator user ID")


class GenerateFromUrlResponse(BaseModel):
    """Returns the generated poster and the scraped source metadata."""
    poster: PosterResponse
    source_preview: ScrapeUrlPreviewResponse


@router.post(
    "/preview-url",
    response_model=ScrapeUrlPreviewResponse,
    summary="Scrape and preview webpage text via Firecrawl",
)
async def preview_url_content(
    payload: ScrapeUrlRequest,
    url_service: UrlCampaignService = Depends(get_url_campaign_service),
):
    """Scrapes a target webpage without generating a poster yet so users can inspect the content."""
    try:
        scraped = await url_service.analyze_url_content(payload.url)
        return ScrapeUrlPreviewResponse(
            url=scraped.url,
            title=scraped.title,
            description=scraped.description,
            extracted_text=scraped.extracted_text,
            source_type=scraped.source_type,
        )
    except Exception as e:
        logger.error("ACTUAL INTERNAL EXCEPTION in URL preview scrape [TERMINAL LOG]: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=to_user_friendly_error(e, context="webpage analysis"),
        )


@router.post(
    "/from-url",
    response_model=GenerateFromUrlResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate full social poster and copy directly from a Web URL",
)
async def generate_from_url(
    payload: GenerateFromUrlRequest,
    db: AsyncSession = Depends(get_db_session),
    url_service: UrlCampaignService = Depends(get_url_campaign_service),
):
    """Scrapes a URL, distills the copy via LLM, renders a background, and creates a ready-to-review poster."""
    # Resolve brand settings
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
        poster, scraped = await url_service.generate_campaign_from_url(
            url=payload.url,
            brand=brand,
            aspect_ratio=payload.aspect_ratio,
            custom_instructions=payload.custom_instructions,
            db=db,
            creator_id=payload.creator_id,
        )
        await db.commit()
        await db.refresh(poster)

        return GenerateFromUrlResponse(
            poster=PosterResponse.model_validate(poster),
            source_preview=ScrapeUrlPreviewResponse(
                url=scraped.url,
                title=scraped.title,
                description=scraped.description,
                extracted_text=scraped.extracted_text,
                source_type=scraped.source_type,
            ),
        )
    except Exception as e:
        await db.rollback()
        logger.error("ACTUAL INTERNAL EXCEPTION in URL campaign generation [TERMINAL LOG]: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=to_user_friendly_error(e, context="URL campaign creation"),
        )
