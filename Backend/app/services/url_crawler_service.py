"""Service for synthesizing complete social marketing campaigns and posters from web URLs."""

import logging
import re
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters.scrapers.firecrawl_adapter import FirecrawlScraperAdapter, ScrapedWebpageData
from app.interfaces.text_generator import AbstractTextGenerator, PosterPlan
from app.services.generation_service import GenerationService
from app.db.models import Poster, Brand

logger = logging.getLogger(__name__)


class UrlCampaignService:
    """Takes a web URL, extracts its core insights, and generates tailored marketing posters and copy."""

    def __init__(
        self,
        scraper_adapter: FirecrawlScraperAdapter,
        text_generator: AbstractTextGenerator,
        generation_service: GenerationService,
    ):
        self.scraper_adapter = scraper_adapter
        self.text_generator = text_generator
        self.generation_service = generation_service

    async def analyze_url_content(self, url: str) -> ScrapedWebpageData:
        """Scrape webpage content via Firecrawl or direct intelligent DOM parsing."""
        return await self.scraper_adapter.scrape_url(url)

    async def generate_campaign_from_url(
        self,
        url: str,
        brand: Brand,
        aspect_ratio: str = "1:1",
        custom_instructions: Optional[str] = None,
        db: Optional[AsyncSession] = None,
        creator_id: Optional[int] = None,
    ) -> tuple[Poster, ScrapedWebpageData]:
        """Scrapes webpage, distills advertising or thought leadership copy, and renders full poster."""
        # 1. Scrape webpage content
        scraped_data = await self.scraper_adapter.scrape_url(url)

        # 2. Construct intelligent, highly contextual prompt instructing LLM to format content appropriately
        page_intent = scraped_data.source_type.upper()
        user_req = custom_instructions.strip() if custom_instructions else ""
        combined_text = f"{scraped_data.title} {scraped_data.extracted_text}".lower()
        is_tech = bool(re.search(r"\b(software|ai|cloud|developer|api|tech|technology|coding|neural|saas|hardware)\b", combined_text))
        is_product = scraped_data.source_type == "product" or "product" in user_req.lower()

        if is_product:
            clean_title = scraped_data.title.split("-")[0].split("|")[0].strip()
            prompt_directive = (
                f"Create a high-converting promotional advertisement campaign for:\n"
                f"Product: '{clean_title}'\n"
                f"URL: {url}\n"
                f"Product Description:\n{scraped_data.extracted_text[:1200]}\n\n"
                f"User Directive: {user_req or 'Focus on product quality, benefits, and compelling customer call to action.'}\n\n"
                "Requirements:\n"
                "- headline: 4 to 6 words. Catchy, benefit-driven hook.\n"
                f"- sub_tagline: Clean uppercase identifier: '{clean_title.upper()[:22]} • 2026'\n"
                "- story_quote: 12 to 16 words. Compelling value proposition.\n"
                "- caption: Persuasive marketing copy with customer hook, key benefits in clean bullet points, and an irresistible call to action.\n"
                f"- image_prompt: Commercial luxury product photography of {clean_title}, elegant pedestal, dramatic studio lighting, upper 60% subject, lower 40% clean negative space, 8k resolution, no text."
            )
        elif is_tech:
            clean_title = scraped_data.title.split("-")[0].split("|")[0].strip()
            prompt_directive = (
                f"Create an authoritative thought-leadership technology summary and social post for:\n"
                f"Topic / Title: '{clean_title}'\n"
                f"Source URL: {url}\n"
                f"Article Excerpt:\n{scraped_data.extracted_text[:1400]}\n\n"
                f"User Directive: {user_req or 'Write a comprehensive post with actionable insights.'}\n\n"
                "Requirements:\n"
                "- headline: 4 to 6 words. Clean, punchy tech hook.\n"
                f"- sub_tagline: Clean uppercase identifier: '{clean_title.upper()[:22]} • 2026'\n"
                "- story_quote: 12 to 16 words. Core architectural or industry insight.\n"
                "- caption: High-value LinkedIn/Instagram post. Opening hook, 3-4 bullet points detailing key insights, business impact, and an interactive question.\n"
                f"- image_prompt: Hyper-detailed visual metaphor specifically illustrating '{clean_title}'. Sleek modern digital horizons, cinematic lighting, upper 60% contains subject, lower 40% empty atmospheric space, Hasselblad 80mm lens, 8k resolution, no text."
            )
        else:
            
            # Cultural, historical, memorial, general topic or landmark (like India Gate)
            clean_title = scraped_data.title.split("-")[0].split("|")[0].strip()
            prompt_directive = (
                f"Create an awe-inspiring, culturally resonant social poster and narrative for:\n"
                f"Topic / Subject: '{clean_title}'\n"
                f"Overview: {scraped_data.description or 'A landmark and subject of profound historical and cultural significance'}\n"
                f"Context & Key Details:\n{scraped_data.extracted_text[:1400]}\n\n"
                f"User Directive: {user_req or 'Honor the historical significance, cultural pride, and iconic beauty.'}\n\n"
                "Requirements:\n"
                f"- headline: 4 to 6 words. A moving, cinema-grade tribute honoring {clean_title}.\n"
                f"- sub_tagline: Clean uppercase identifier: '{clean_title.upper()[:22]} • 2026'\n"
                f"- story_quote: 12 to 16 words. Moving reflection on the heritage, bravery, and timeless legacy of {clean_title}.\n"
                f"- caption: High-engagement narrative social post for LinkedIn and Instagram with tasteful emojis and structured paragraph bullet points honoring {clean_title}.\n"
                f"- image_prompt: Masterpiece cinema-grade photography specifically depicting {clean_title}. Grand architectural scale, volumetric golden hour twilight rays, dramatic atmospheric clouds, upper 60% contains the majestic monument {clean_title}, lower 40% clean dark empty space for typography, Hasselblad 80mm lens, 8k resolution, photorealistic, no text."
            )

        # 3. Delegate to GenerationService to produce poster, copy, hashtags, and DB record
        poster = await self.generation_service.generate_poster(
            raw_prompt=prompt_directive,
            brand=brand,
            aspect_ratio=aspect_ratio,
            db=db,
            created_by_id=creator_id,
        )

        return poster, scraped_data
