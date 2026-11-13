"""Business logic orchestrating poster reviews, revisions, and approval locks."""

import logging
import re
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Poster, PosterRevision, PostStatus, Brand, User
from app.interfaces.text_generator import PosterPlan
from app.interfaces.storage_provider import AbstractStorageProvider
from app.services.poster_compositor import PosterCompositor
from app.services.knowledge_graph import KnowledgeGraphService
from app.services.video_service import VideoService

logger = logging.getLogger(__name__)


class ReviewService:
    """Manages reviewer modifications, immutable approval locks, and version history."""

    def __init__(
        self,
        storage_provider: AbstractStorageProvider,
        compositor: PosterCompositor,
        knowledge_graph: KnowledgeGraphService | None = None,
        video_service: Optional[VideoService] = None,
    ):
        self.storage_provider = storage_provider
        self.compositor = compositor
        self.knowledge_graph = knowledge_graph or KnowledgeGraphService()
        self.video_service = video_service

    def _parse_instruction_diff(self, instruction: str, current_poster: Poster) -> Dict[str, Any]:
        """Extract requested changes from plain language instruction."""
        diff: Dict[str, Any] = {}
        lowered = instruction.lower()

        # Check for explicit headline change quotes: change headline to "..." or '...'
        headline_match = re.search(r'headline\s+(?:to|as)\s+["\']([^"\']+)["\']', instruction, re.IGNORECASE)
        if not headline_match:
            # Check without quotes if phrased like: change headline to Happy Diwali
            headline_match = re.search(r'headline\s+(?:to|as)\s+([A-Za-z0-9\s!?,.-]+?)(?:\s+and\b|$)', instruction, re.IGNORECASE)

        if headline_match:
            new_headline = headline_match.group(1).strip()
            diff["headline"] = {"old": current_poster.headline, "new": new_headline}

        # Check for quote or subline changes
        quote_match = re.search(r'quote\s+(?:to|as)\s+["\']([^"\']+)["\']', instruction, re.IGNORECASE)
        if quote_match:
            diff["quote"] = {"old": current_poster.quote, "new": quote_match.group(1).strip()}

        # Check for hashtag addition/removal
        if "hashtag" in lowered or "#" in instruction:
            added_tags = re.findall(r'#\w+', instruction)
            if added_tags:
                new_tags = list(set(current_poster.hashtags + added_tags))
                diff["hashtags"] = {"old": current_poster.hashtags, "new": new_tags}

        # If no specific regex matched, treat instruction as headline tweak by default
        if not diff:
            diff["headline"] = {"old": current_poster.headline, "new": instruction.strip()}

        return diff

    async def apply_plain_language_edit(
        self,
        poster_id: int,
        instruction: str | None = None,
        user_id: int = 1,
        db: AsyncSession = None,
        headline: str | None = None,
        headline_y_ratio: float | None = None,
        headline_scale: float | None = None,
        quote: str | None = None,
        quote_y_ratio: float | None = None,
        quote_scale: float | None = None,
        caption: str | None = None,
        hashtags: list[str] | None = None,
        layout_meta: dict | None = None,
        primary_color: str | None = None,
        secondary_color: str | None = None,
        quote_color: str | None = None,
    ) -> Poster:
        """Apply requested changes, re-composite poster with cached background, and record revision."""
        poster = await db.get(Poster, poster_id)
        if not poster:
            raise ValueError(f"Poster with ID {poster_id} not found.")

        if poster.status == PostStatus.APPROVED:
            raise ValueError(f"Poster with ID {poster_id} has already been approved and locked against further edits.")

        diff: Dict[str, Any] = {}
        if instruction:
            diff.update(self._parse_instruction_diff(instruction, poster))
            if "headline" in diff and isinstance(diff["headline"], dict):
                poster.headline = diff["headline"]["new"]
            if "quote" in diff and isinstance(diff["quote"], dict):
                poster.quote = diff["quote"]["new"]
            if "hashtags" in diff and isinstance(diff["hashtags"], dict):
                poster.hashtags = diff["hashtags"]["new"]
            if "caption" in diff and isinstance(diff["caption"], dict):
                poster.caption = diff["caption"]["new"]

        # Directly update fields on the poster model
        if headline is not None:
            if headline.strip() != poster.headline:
                diff["headline"] = {"old": poster.headline, "new": headline.strip()}
            poster.headline = headline.strip()

        if quote is not None:
            if quote.strip() != (poster.quote or ""):
                diff["quote"] = {"old": poster.quote, "new": quote.strip()}
            poster.quote = quote.strip()

        if caption is not None:
            if caption.strip() != poster.caption:
                diff["caption"] = {"old": poster.caption, "new": caption.strip()}
            poster.caption = caption.strip()

        if hashtags is not None:
            if hashtags != poster.hashtags:
                diff["hashtags"] = {"old": poster.hashtags, "new": hashtags}
            poster.hashtags = hashtags

        # Persist visual layout coordinates and color tokens
        current_meta = dict(poster.layout_meta or {})
        if layout_meta is not None:
            current_meta.update(layout_meta)
        if headline_y_ratio is not None:
            current_meta["y"] = round(headline_y_ratio * 100)
        if headline_scale is not None:
            current_meta["scale"] = headline_scale
        if primary_color is not None:
            current_meta["accent_color"] = primary_color
        if secondary_color is not None:
            current_meta["headline_color"] = secondary_color
        if quote_color is not None:
            current_meta["quote_color"] = quote_color
        poster.layout_meta = current_meta

        if not diff:
            diff["edit"] = {"type": "direct_typography_or_layout_adjustment"}

        effective_instruction = instruction or f"Direct typography edit: '{poster.headline}'"

        # Fetch brand visual tokens as baseline fallback
        brand = await db.get(Brand, poster.brand_id)
        default_brand_accent = brand.primary_color if brand else "#FFDF0F"
        default_brand_text = brand.secondary_color if brand else "#FFFFFF"

        # Resolve colors prioritizing explicit params, then layout_meta, then brand defaults
        resolved_primary = (
            primary_color
            or current_meta.get("accent_color")
            or current_meta.get("primary_color")
            or default_brand_accent
        )
        resolved_secondary = (
            secondary_color
            or current_meta.get("headline_color")
            or current_meta.get("secondary_color")
            or default_brand_text
        )
        resolved_quote = (
            quote_color
            or current_meta.get("quote_color")
            or resolved_primary
        )

        # Re-use existing background without calling image model (cost = $0, latency = 20ms)
        bg_url = poster.background_image_url or poster.final_poster_url
        bg_rel_path = bg_url.split("/static/")[-1] if "/static/" in bg_url else bg_url.lstrip("/")
        background_bytes = await self.storage_provider.get_asset(bg_rel_path)

        # Re-composite typography and overlay
        plan = PosterPlan(
            headline=poster.headline,
            caption=poster.caption,
            hashtags=poster.hashtags,
            quote=poster.quote,
            image_prompt="",
            template_name=poster.template_name,
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

        updated_poster_bytes = self.compositor.composite_poster(
            background_bytes=background_bytes,
            plan=plan,
            primary_color=resolved_primary,
            secondary_color=resolved_secondary,
            quote_color=resolved_quote,
            logo_bytes=logo_bytes,
            quote_y_ratio=quote_y_ratio,
            quote_scale=quote_scale,
            headline_y_ratio=headline_y_ratio,
            headline_scale=headline_scale,
        )

        # Count existing revisions to calculate new version number
        rev_count_query = await db.execute(
            select(PosterRevision).where(PosterRevision.poster_id == poster_id)
        )
        existing_revisions = rev_count_query.scalars().all()
        version_number = len(existing_revisions) + 1

        # Save new composited image asset
        unique_id = uuid.uuid4().hex[:10]
        new_filename = f"posters/{unique_id}_v{version_number}.png"
        new_url = await self.storage_provider.save_asset(new_filename, updated_poster_bytes)

        poster.final_poster_url = new_url
        poster.updated_at = datetime.now(timezone.utc)

        # If poster has an associated video reel, automatically re-synthesize video typography & colors
        if poster.video_url and self.video_service:
            try:
                candidate_paths = [
                    Path(settings.LOCAL_STORAGE_DIR) / bg_rel_path,
                    Path(settings.LOCAL_STORAGE_DIR) / "posters" / Path(bg_rel_path).name,
                    Path("Backend/storage") / bg_rel_path,
                    Path("Backend/storage/posters") / Path(bg_rel_path).name,
                    Path("storage") / bg_rel_path,
                    Path("storage/posters") / Path(bg_rel_path).name,
                ]
                bg_disk_path = None
                for candidate in candidate_paths:
                    if candidate.exists():
                        bg_disk_path = candidate
                        break

                if bg_disk_path and bg_disk_path.exists():
                    vid_result = await self.video_service.generate_video_from_poster(
                        poster_image_path=bg_disk_path,
                        headline=poster.headline,
                        quote=poster.quote or "",
                        headline_color=resolved_secondary,
                        quote_color=resolved_quote,
                        accent_color=resolved_primary,
                        y_percent=current_meta.get("y"),
                        scale=current_meta.get("scale"),
                        rotation=current_meta.get("rotation", 0),
                        prompt=poster.prompt,
                        motion_prompt=current_meta.get("video_motion_prompt"),
                        skip_diffusion=True,
                    )
                    poster.video_url = vid_result.video_url
                    diff["video_url"] = {"new": vid_result.video_url}
                    logger.info("Auto-synchronized video reel for poster %s -> %s", poster.id, vid_result.video_url)
            except Exception as vid_err:
                logger.warning("Could not auto-synchronize video reel on edit for poster %s: %s", poster.id, vid_err)

        # Create audit revision entry
        revision_entry = PosterRevision(
            poster_id=poster.id,
            version_number=version_number,
            instruction=effective_instruction,
            diff_summary=diff,
        )
        db.add(revision_entry)

        await db.commit()
        await db.refresh(poster)
        return poster

    async def approve_poster(
        self,
        poster_id: int,
        reviewer_id: int,
        notes: str | None,
        db: AsyncSession,
    ) -> Poster:
        """Approve and lock poster, unlocking social publishing."""
        poster = await db.get(Poster, poster_id)
        if not poster:
            raise ValueError(f"Poster with ID {poster_id} not found.")

        if poster.status == PostStatus.APPROVED:
            raise ValueError("Poster is already approved.")

        # Ensure valid user ID for foreign key constraint
        valid_user = await db.get(User, reviewer_id)
        if not valid_user:
            valid_user = await db.get(User, poster.created_by_id)
            if valid_user:
                reviewer_id = valid_user.id

        poster.status = PostStatus.APPROVED
        poster.approved_by_id = reviewer_id
        poster.approval_locked_at = datetime.now(timezone.utc)
        poster.updated_at = datetime.now(timezone.utc)

        # Synchronously record approval in knowledge graph
        await self.knowledge_graph.record_approval(poster, db)

        await db.commit()
        await db.refresh(poster)
        return poster

    async def reject_poster(
        self,
        poster_id: int,
        reviewer_id: int,
        reason: str,
        db: AsyncSession,
    ) -> Poster:
        """Reject poster with feedback reason."""
        poster = await db.get(Poster, poster_id)
        if not poster:
            raise ValueError(f"Poster with ID {poster_id} not found.")

        poster.status = PostStatus.REJECTED
        poster.updated_at = datetime.now(timezone.utc)

        # Record rejection note in revision history
        revision_entry = PosterRevision(
            poster_id=poster.id,
            version_number=0,
            instruction=f"REJECTED: {reason}",
            diff_summary={"status": {"old": str(poster.status), "new": "rejected"}},
        )
        db.add(revision_entry)

        await db.commit()
        await db.refresh(poster)
        return poster

    async def get_revisions(self, poster_id: int, db: AsyncSession) -> List[PosterRevision]:
        """Fetch chronological list of revisions for a poster."""
        query = await db.execute(
            select(PosterRevision)
            .where(PosterRevision.poster_id == poster_id)
            .order_by(PosterRevision.version_number.asc())
        )
        return query.scalars().all()
