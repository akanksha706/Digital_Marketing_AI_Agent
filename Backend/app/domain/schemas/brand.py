"""Pydantic schemas for brand profile management."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class BrandBase(BaseModel):
    """Base attributes for a team brand identity."""
    team_name: str = Field(..., min_length=2, max_length=100)
    logo_url: Optional[str] = None
    primary_color: str = Field(default="#000000", max_length=20)
    secondary_color: str = Field(default="#FFFFFF", max_length=20)
    font_family: str = Field(default="Inter", max_length=50)
    tone_of_voice: str = Field(default="professional", max_length=100)
    banned_words: List[str] = Field(default_factory=list)
    default_hashtags: List[str] = Field(default_factory=list)


class BrandCreate(BrandBase):
    """Payload for creating a new brand."""
    pass


class BrandUpdate(BaseModel):
    """Payload for updating existing brand properties."""
    team_name: Optional[str] = Field(None, min_length=2, max_length=100)
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    font_family: Optional[str] = None
    tone_of_voice: Optional[str] = None
    banned_words: Optional[List[str]] = None
    default_hashtags: Optional[List[str]] = None


class BrandResponse(BrandBase):
    """Output representation of a team brand profile."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
