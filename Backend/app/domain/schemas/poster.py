"""Pydantic schemas for poster creation requests and responses."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.db.models import PostStatus


class GeneratePosterRequest(BaseModel):
    """Input payload for poster generation."""
    prompt: str = Field(..., min_length=3, max_length=500, description="One-line topic prompt")
    brand_id: int = Field(default=1, description="Target brand identifier")
    aspect_ratio: str = Field(default="1:1", description="Target aspect ratio: 1:1, 4:5, 16:9")


class PosterResponse(BaseModel):
    """Output representation of a generated poster ready for review."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    brand_id: int
    prompt: str
    headline: str
    caption: str
    hashtags: List[str]
    quote: Optional[str] = None
    background_image_url: Optional[str] = None
    final_poster_url: Optional[str] = None
    video_url: Optional[str] = None
    template_name: str
    aspect_ratio: str
    status: PostStatus
    created_at: datetime
    created_by_id: Optional[int] = None
    approval_locked_at: Optional[datetime] = None
    is_archived: bool = False
    published_at: Optional[datetime] = None
    layout_meta: Optional[dict] = None
