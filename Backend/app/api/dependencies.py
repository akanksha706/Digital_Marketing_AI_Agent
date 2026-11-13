"""Dependency injection providers for services and adapters."""

from typing import Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.adapters.safety.guardrails import GuardrailsSafetyChecker
from app.adapters.scrapers.firecrawl_adapter import FirecrawlScraperAdapter
from app.adapters.ai.cloudflare_text import CloudflareTextGenerator
from app.adapters.ai.cloudflare_image import CloudflareImageGenerator
from app.adapters.storage.local_storage import LocalStorageProvider
from app.services.poster_compositor import PosterCompositor
from app.adapters.publishers.linkedin_adapter import LinkedInPublisherAdapter
from app.adapters.publishers.instagram_adapter import InstagramPublisherAdapter
from app.services.generation_service import GenerationService
from app.services.custom_upload_service import CustomImageService
from app.services.url_crawler_service import UrlCampaignService
from app.services.review_service import ReviewService
from app.services.video_service import VideoService
from app.services.scheduling_service import SchedulingService
from app.services.knowledge_graph import KnowledgeGraphService
from app.workers.scheduler_worker import SchedulerWorker


def get_generation_service() -> GenerationService:
    """Instantiate GenerationService with configured adapters."""
    return GenerationService(
        safety_checker=GuardrailsSafetyChecker(),
        text_generator=CloudflareTextGenerator(),
        image_generator=CloudflareImageGenerator(),
        storage_provider=LocalStorageProvider(),
        compositor=PosterCompositor(),
    )


def get_knowledge_graph_service() -> KnowledgeGraphService:
    """Instantiate KnowledgeGraphService."""
    return KnowledgeGraphService()


def get_video_service() -> VideoService:
    """Instantiate VideoService for cinema reel and video motion synthesis."""
    return VideoService()


def get_review_service() -> ReviewService:
    """Instantiate ReviewService with storage, compositor, knowledge graph, and video service dependencies."""
    return ReviewService(
        storage_provider=LocalStorageProvider(),
        compositor=PosterCompositor(),
        knowledge_graph=KnowledgeGraphService(),
        video_service=get_video_service(),
    )


def get_scheduling_service() -> SchedulingService:
    """Instantiate SchedulingService with social publisher adapters."""
    return SchedulingService(
        linkedin_publisher=LinkedInPublisherAdapter(),
        instagram_publisher=InstagramPublisherAdapter(),
    )


def get_scheduler_worker() -> SchedulerWorker:
    """Instantiate SchedulerWorker with social publisher adapters."""
    return SchedulerWorker(
        linkedin_publisher=LinkedInPublisherAdapter(),
        instagram_publisher=InstagramPublisherAdapter(),
    )


def get_url_campaign_service() -> UrlCampaignService:
    """Instantiate UrlCampaignService with Firecrawl scraper and generation pipeline."""
    return UrlCampaignService(
        scraper_adapter=FirecrawlScraperAdapter(),
        text_generator=CloudflareTextGenerator(),
        generation_service=get_generation_service(),
    )


def get_custom_image_service() -> CustomImageService:
    """Instantiate CustomImageService with Llama-Guard 3 safety checker, image generator, and compositor."""
    return CustomImageService(
        safety_checker=GuardrailsSafetyChecker(),
        text_generator=CloudflareTextGenerator(),
        image_generator=CloudflareImageGenerator(),
        storage_provider=LocalStorageProvider(),
        compositor=PosterCompositor(),
    )
