"""Interface and response models for social media publishing."""

from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel


class PublishResult(BaseModel):
    """Result returned after attempting to publish to a social network."""
    success: bool
    platform_post_id: Optional[str] = None
    error_message: Optional[str] = None


class AbstractSocialPublisher(ABC):
    """Abstract contract for social media platform publishers."""

    @abstractmethod
    async def publish(
        self,
        caption: str,
        image_url: str,
        hashtags: list[str] | None = None,
    ) -> PublishResult:
        """Publish caption, hashtags, and poster image to the target platform."""
        pass
