"""Pydantic schemas for poster review, revision, and approval workflows."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.db.models import PostStatus


class EditPosterRequest(BaseModel):
    """Payload for requesting modifications using plain language instructions or direct field edits."""
    instruction: Optional[str] = Field(
        None,
        max_length=500,
        description="Plain-language edit instruction (e.g., 'Change headline to Happy Diwali')",
    )
    headline: Optional[str] = Field(None, max_length=200, description="Direct new headline text")
    headline_y_ratio: Optional[float] = Field(None, ge=0.05, le=0.95, description="Vertical position ratio of headline")
    headline_scale: Optional[float] = Field(None, ge=0.5, le=2.5, description="Scale factor for headline typography")
    quote: Optional[str] = Field(None, max_length=300, description="Direct new reflection quote")
    quote_y_ratio: Optional[float] = Field(
        None,
        ge=0.05,
        le=0.95,
        description="Vertical position ratio of reflection quote (0.0 to 1.0, e.g. 0.58 for middle)",
    )
    quote_scale: Optional[float] = Field(None, ge=0.5, le=2.5, description="Scale factor for quote typography")
    caption: Optional[str] = Field(None, max_length=2000, description="Direct new social caption text")
    hashtags: Optional[list[str]] = Field(None, description="Direct new hashtags")
    layout_meta: Optional[Dict[str, Any]] = Field(None, description="Persisted visual layout coordinates and scales")
    primary_color: Optional[str] = Field(None, max_length=50, description="Accent color for tagline & decorative dividers (e.g. #FFC20E)")
    secondary_color: Optional[str] = Field(None, max_length=50, description="Main text color for headline (e.g. #FFFFFF or #0F172A)")
    quote_color: Optional[str] = Field(None, max_length=50, description="Color for quote text (e.g. #FFDF0F or #FFFFFF)")
    user_id: int = Field(default=1, description="Reviewer or user requesting the edit")


class ApprovalRequest(BaseModel):
    """Payload for approving and locking a poster."""
    reviewer_id: int = Field(default=1, description="ID of the user approving the poster")
    notes: Optional[str] = Field(None, max_length=500, description="Optional sign-off notes")


class RejectRequest(BaseModel):
    """Payload for rejecting a poster."""
    reviewer_id: int = Field(default=1, description="ID of the user rejecting the poster")
    reason: str = Field(..., min_length=3, max_length=500, description="Reason for rejection")


class RevisionResponse(BaseModel):
    """Audit record for a single revision of a poster."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    poster_id: int
    version_number: int
    instruction: str
    diff_summary: Dict[str, Any]
    created_at: datetime


class ReviewActionResponse(BaseModel):
    """Response returned after performing an approval or rejection action."""
    poster_id: int
    status: PostStatus
    message: str
    updated_at: datetime
