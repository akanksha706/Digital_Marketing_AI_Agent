"""Service managing team memory, template frequency tracking, and brand style rules."""

import re
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Poster, OccasionTheme, KnowledgeLink, StyleRule, PosterRevision
from app.domain.schemas.knowledge_graph import TeamKnowledgeSummary


class KnowledgeGraphService:
    """Maintains team visual intelligence and approval statistics in PostgreSQL."""

    @staticmethod
    def _extract_theme_name(prompt: str) -> str:
        """Derive a clean normalized occasion/theme name from user prompt."""
        # Remove filler words
        cleaned = re.sub(r'\b(poster|creative|post|design|celebration|banner)\b', '', prompt, flags=re.IGNORECASE)
        cleaned = " ".join(cleaned.split()).strip()
        return cleaned.title() if cleaned else prompt.title()

    async def record_approval(self, poster: Poster, db: AsyncSession) -> None:
        """Atomically record approved template, theme association, and style habits."""
        theme_name = self._extract_theme_name(poster.prompt)

        # 1. Look up or create Occasion / Theme entity
        theme_query = await db.execute(
            select(OccasionTheme).where(
                OccasionTheme.brand_id == poster.brand_id,
                func.lower(OccasionTheme.name) == theme_name.lower(),
            )
        )
        occasion = theme_query.scalar_one_or_none()
        if not occasion:
            occasion = OccasionTheme(brand_id=poster.brand_id, name=theme_name)
            db.add(occasion)
            await db.flush()

        # 2. Update Knowledge Link (template approval frequency count)
        link_query = await db.execute(
            select(KnowledgeLink).where(
                KnowledgeLink.brand_id == poster.brand_id,
                KnowledgeLink.occasion_id == occasion.id,
                KnowledgeLink.template_name == poster.template_name,
            )
        )
        link = link_query.scalar_one_or_none()
        if link:
            link.approval_count += 1
            link.last_approved_at = datetime.now(timezone.utc)
        else:
            link = KnowledgeLink(
                brand_id=poster.brand_id,
                occasion_id=occasion.id,
                template_name=poster.template_name,
                approval_count=1,
            )
            db.add(link)

        # 3. Analyze revision habits: if headline was shortened repeatedly, suggest style rule
        rev_query = await db.execute(
            select(PosterRevision).where(PosterRevision.poster_id == poster.id)
        )
        revisions = rev_query.scalars().all()
        for rev in revisions:
            if "headline" in rev.diff_summary:
                old_len = len(rev.diff_summary["headline"].get("old", ""))
                new_len = len(rev.diff_summary["headline"].get("new", ""))
                if new_len < old_len:
                    rule_text = "Prefer concise headlines under 6 words"
                    # Check if rule exists
                    existing_rule = await db.execute(
                        select(StyleRule).where(
                            StyleRule.brand_id == poster.brand_id,
                            StyleRule.rule_text == rule_text,
                        )
                    )
                    if not existing_rule.scalar_one_or_none():
                        db.add(StyleRule(brand_id=poster.brand_id, rule_text=rule_text, is_confirmed=False))

        await db.flush()

    async def get_team_summary(self, brand_id: int, db: AsyncSession) -> TeamKnowledgeSummary:
        """Fetch all intelligence nodes and template habits for a brand."""
        occasions_query = await db.execute(
            select(OccasionTheme).where(OccasionTheme.brand_id == brand_id).order_by(OccasionTheme.created_at.desc())
        )
        occasions = occasions_query.scalars().all()

        links_query = await db.execute(
            select(KnowledgeLink)
            .where(KnowledgeLink.brand_id == brand_id)
            .order_by(KnowledgeLink.approval_count.desc())
        )
        links = links_query.scalars().all()

        rules_query = await db.execute(
            select(StyleRule)
            .where(StyleRule.brand_id == brand_id)
            .order_by(StyleRule.created_at.desc())
        )
        rules = rules_query.scalars().all()

        return TeamKnowledgeSummary(
            brand_id=brand_id,
            occasions=occasions,
            top_templates=links,
            confirmed_rules=rules,
        )

    async def confirm_style_rule(self, rule_id: int, db: AsyncSession) -> StyleRule:
        """Confirm a suggested style rule so the AI uses it for future generation."""
        rule = await db.get(StyleRule, rule_id)
        if not rule:
            raise ValueError(f"Style rule with ID {rule_id} not found.")

        rule.is_confirmed = True
        await db.flush()
        return rule
