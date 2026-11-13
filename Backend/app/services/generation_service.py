"""Orchestration service coordinating AI generation, safety, rendering, and persistence."""

import asyncio
import uuid
from pathlib import Path
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Poster, Brand, PostStatus, User, UserRole
from app.interfaces.text_generator import AbstractTextGenerator
from app.interfaces.image_generator import AbstractImageGenerator
from app.interfaces.safety_checker import AbstractSafetyChecker
from app.interfaces.storage_provider import AbstractStorageProvider
from app.services.poster_compositor import PosterCompositor
from app.services.visual_director import VisualLayoutAnalyzer


class GenerationService:
    """Orchestrates the prompt-to-poster pipeline."""

    def __init__(
        self,
        safety_checker: AbstractSafetyChecker,
        text_generator: AbstractTextGenerator,
        image_generator: AbstractImageGenerator,
        storage_provider: AbstractStorageProvider,
        compositor: Optional[PosterCompositor] = None,
    ):
        self.safety_checker = safety_checker
        self.text_generator = text_generator
        self.image_generator = image_generator
        self.storage_provider = storage_provider
        self.compositor = compositor or PosterCompositor()

    @staticmethod
    def _resolve_dimensions(aspect_ratio: str) -> tuple[int, int]:
        """Map social media aspect ratio to pixel dimensions."""
        mapping = {
            "2:1": (1200, 600),
            "16:9": (1200, 675),
            "4:5": (1080, 1350),
            "9:16": (720, 1280),
            "1:1": (1024, 1024),
        }
        return mapping.get(aspect_ratio.strip(), (1024, 1024))

    async def generate_poster(
        self,
        raw_prompt: str,
        brand: Brand,
        created_by_id: Optional[int],
        db: AsyncSession,
        aspect_ratio: str = "1:1",
    ) -> Poster:
        """Execute full generation pipeline: safety -> parallel AI -> compositing -> persistence."""
        # Ensure a valid creator user exists
        if created_by_id is None:
            user_res = await db.execute(select(User).where(User.brand_id == brand.id).limit(1))
            user = user_res.scalar_one_or_none()
            if not user:
                user = User(
                    email=f"creator@{brand.team_name.lower().replace(' ', '')}.com",
                    hashed_password="hashed_dev_password",
                    role=UserRole.MEMBER,
                    brand_id=brand.id,
                )
                db.add(user)
                await db.flush()
            created_by_id = user.id

        # Step 1: Safety & Moderation Check
        safety_result = await self.safety_checker.validate_prompt_safety(
            raw_prompt, banned_words=brand.banned_words
        )
        if not safety_result.is_safe:
            raise ValueError(f"Content safety check failed: {safety_result.reason}")

        # Step 2: Mask Personal Identifiable Information
        sanitized_prompt = self.safety_checker.mask_personal_data(raw_prompt)

        # Step 3: Resolve dynamic dimensions based on requested aspect ratio
        width, height = self._resolve_dimensions(aspect_ratio)

        # Step 4: First generate director-grade creative plan with authentic visual direction
        plan = await self.text_generator.generate_poster_plan(
            prompt=sanitized_prompt,
            brand_tone=brand.tone_of_voice,
            banned_words=brand.banned_words,
        )

        # Step 5: Render cinema-grade background using the enriched image prompt
        background_bytes = await self.image_generator.generate_background(
            image_prompt=plan.image_prompt,
            width=width,
            height=height,
        )

        # Load brand logo for poster (42Works_logo2.png requested for generated posters)
        logo_bytes = None
        for candidate in [
            Path("Backend/storage/brand/42Works_logo2.png"),
            Path("storage/brand/42Works_logo2.png"),
            Path("Frontend/public/42Works_logo2.png"),
            Path("Backend/storage/brand/42works_logo.png"),
            Path("storage/brand/42works_logo.png"),
        ]:
            if candidate.exists():
                try:
                    logo_bytes = candidate.read_bytes()
                    break
                except Exception:
                    pass

        # Step 6: Autonomously scan background with Multimodal LLM Vision to identify objects, empty space & contrast colors
        layout_meta = await VisualLayoutAnalyzer.analyze_image_llm(
            image_input=background_bytes,
            brand_primary=brand.primary_color,
            brand_secondary=brand.secondary_color,
        )
        # Store cinematic image prompt and video motion brief in layout_meta for downstream video reel generation
        layout_meta["image_prompt"] = plan.image_prompt
        layout_meta["video_motion_prompt"] = plan.video_motion_prompt

        # Step 7: Composite text, branding, and readability overlays onto background
        poster_png_bytes = self.compositor.composite_poster(
            background_bytes=background_bytes,
            plan=plan,
            primary_color=layout_meta.get("accent_color", brand.primary_color),
            secondary_color=layout_meta.get("headline_color", brand.secondary_color),
            quote_color=layout_meta.get("quote_color"),
            headline_y_ratio=layout_meta.get("headline_y_ratio"),
            quote_y_ratio=layout_meta.get("quote_y_ratio"),
            logo_bytes=logo_bytes,
        )

        # Step 8: Save assets to storage (local disk or R2 bucket)
        unique_id = uuid.uuid4().hex[:12]
        bg_filename = f"posters/{unique_id}_background.png"
        final_filename = f"posters/{unique_id}_final.png"

        bg_url = await self.storage_provider.save_asset(bg_filename, background_bytes)
        final_url = await self.storage_provider.save_asset(final_filename, poster_png_bytes)

        # Step 9: Persist entity to database with full layout metadata for 0-effort UI alignment
        poster = Poster(
            brand_id=brand.id,
            created_by_id=created_by_id,
            prompt=raw_prompt,
            headline=plan.headline,
            caption=plan.caption,
            hashtags=plan.hashtags,
            quote=plan.quote or plan.story_quote,
            background_image_url=bg_url,
            final_poster_url=final_url,
            template_name=plan.template_name,
            aspect_ratio=aspect_ratio,
            layout_meta=layout_meta,
            status=PostStatus.IN_REVIEW,
        )
        db.add(poster)
        await db.commit()
        await db.refresh(poster)

        return poster
