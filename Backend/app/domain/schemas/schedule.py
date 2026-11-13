"""Pydantic schemas for social media post scheduling and dispatch."""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator, computed_field
from app.db.models import SocialPlatform, JobStatus


class SchedulePostRequest(BaseModel):
    """Payload for scheduling or immediately publishing an approved poster."""
    platform: SocialPlatform = Field(..., description="Target platform: linkedin or instagram")
    poster_id: Optional[int] = Field(None, description="Poster ID")
    media_url: Optional[str] = Field(None, description="Optional custom media URL (video reel or customized image)")
    post_now: bool = Field(default=False, description="If true, dispatches immediately; otherwise schedules")
    scheduled_for: Optional[datetime] = Field(
        default=None,
        description="Target UTC timestamp for scheduled publishing. Required if post_now is False.",
    )
    scheduled_time: Optional[datetime] = Field(
        default=None,
        description="Alias for scheduled_for",
    )

    @model_validator(mode="after")
    def validate_schedule_time(self) -> "SchedulePostRequest":
        """Ensure scheduled_for is provided when post_now is False."""
        if self.scheduled_time and not self.scheduled_for:
            self.scheduled_for = self.scheduled_time
        if not self.post_now and not self.scheduled_for:
            raise ValueError("scheduled_for must be provided when post_now is False.")
        if self.post_now and not self.scheduled_for:
            self.scheduled_for = datetime.now(timezone.utc)
        return self


class ScheduledJobResponse(BaseModel):
    """Status representation of a queued or dispatched publishing job."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    poster_id: int
    platform: SocialPlatform
    scheduled_for: datetime
    status: JobStatus
    retry_count: int
    max_retries: int
    platform_post_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime

    @computed_field
    @property
    def scheduled_time(self) -> datetime:
        return self.scheduled_for

    @computed_field
    @property
    def error_log(self) -> Optional[str]:
        return self.error_message


class CancelJobResponse(BaseModel):
    """Response returned upon cancelling a scheduled post."""
    job_id: int
    message: str
