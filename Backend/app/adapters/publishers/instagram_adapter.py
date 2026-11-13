"""Instagram Graph API publisher adapter."""

import logging
import uuid
import httpx
from app.interfaces.social_publisher import AbstractSocialPublisher, PublishResult
from app.core.config import settings

logger = logging.getLogger(__name__)


class InstagramPublisherAdapter(AbstractSocialPublisher):
    """Publishes approved posters and copy to Instagram via Graph API."""

    def __init__(self):
        self.access_token = settings.INSTAGRAM_ACCESS_TOKEN
        self.account_id = settings.INSTAGRAM_BUSINESS_ACCOUNT_ID
        self.base_url = "https://graph.facebook.com/v20.0"

    async def publish(
        self,
        caption: str,
        image_url: str,
        hashtags: list[str] | None = None,
    ) -> PublishResult:
        """Publish post to Instagram using the two-step media container workflow."""
        full_text = caption
        if hashtags:
            full_text = f"{caption}\n\n{' '.join(hashtags)}"

        # Development / Sandbox fallback simulation
        if not self.access_token or not self.account_id:
            logger.info("Instagram credentials not configured. Simulating successful dispatch.")
            simulated_id = f"ig_media_{uuid.uuid4().hex[:12]}"
            return PublishResult(success=True, platform_post_id=simulated_id)

        # Make sure image URL is an absolute public URL
        absolute_img_url = image_url
        if image_url.startswith("/"):
            absolute_img_url = f"{settings.PUBLIC_SERVER_BASE_URL}{image_url}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Step 1: Create media container
                container_resp = await client.post(
                    f"{self.base_url}/{self.account_id}/media",
                    params={
                        "image_url": absolute_img_url,
                        "caption": full_text,
                        "access_token": self.access_token,
                    },
                )
                container_resp.raise_for_status()
                container_id = container_resp.json().get("id")

                # Step 2: Publish the media container
                publish_resp = await client.post(
                    f"{self.base_url}/{self.account_id}/media_publish",
                    params={
                        "creation_id": container_id,
                        "access_token": self.access_token,
                    },
                )
                publish_resp.raise_for_status()
                published_media_id = publish_resp.json().get("id")

                return PublishResult(success=True, platform_post_id=published_media_id)
        except httpx.HTTPError as err:
            logger.error("Failed to post to Instagram: %s", err)
            return PublishResult(success=False, error_message=str(err))
