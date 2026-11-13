"""Pydantic schemas for Creator Performance & Publishing Analytics."""

from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel


class CreatorTimelinePoint(BaseModel):
    """Data point for chart visualization."""
    label: str  # e.g., "Mon", "Tue", "Jan", "Feb" or "Week 42"
    published_count: int
    linkedin_count: int
    instagram_count: int


class CreatorSummary(BaseModel):
    """Aggregated publishing performance for a single creator."""
    creator_id: int
    email: str
    role: str
    total_generated: int
    total_published: int
    published_this_week: int
    published_this_month: int
    published_this_year: int
    scheduled_count: int
    draft_count: int
    archived_count: int
    linkedin_count: int
    instagram_count: int
    timeline: List[CreatorTimelinePoint]


class GlobalAnalyticsSummary(BaseModel):
    """High-level team analytics across all creators."""
    total_creators: int
    total_posters_generated: int
    total_published: int
    published_this_week: int
    published_this_month: int
    published_this_year: int
    total_scheduled: int
    total_archived: int
    creators: List[CreatorSummary]
