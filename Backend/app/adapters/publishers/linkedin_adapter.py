"""LinkedIn REST API publisher adapter with full media upload support."""

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
import httpx
from app.interfaces.social_publisher import AbstractSocialPublisher, PublishResult
from app.core.config import settings

logger = logging.getLogger(__name__)


class LinkedInPublisherAdapter(AbstractSocialPublisher):
    """Publishes approved posters and copy to LinkedIn via REST API."""

    def __init__(self):
        self.api_endpoint = "https://api.linkedin.com/rest/posts"
        self.images_endpoint = "https://api.linkedin.com/rest/images?action=initializeUpload"

    @property
    def api_version(self) -> str:
        """Returns the current active LinkedIn API version (YYYYMM)."""
        return datetime.now(timezone.utc).strftime("%Y%m")

    @property
    def access_token(self) -> str:
        return settings.LINKEDIN_ACCESS_TOKEN.strip()

    @property
    def author_urn(self) -> str:
        return settings.LINKEDIN_AUTHOR_URN.strip()

    def _get_api_headers(self) -> dict:
        """Construct standard LinkedIn REST API headers."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "LinkedIn-Version": self.api_version,
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }

    async def _upload_image(self, client: httpx.AsyncClient, headers: dict, image_url: str, author_urn: str) -> str | None:
        """Uploads image binary to LinkedIn and returns image URN (urn:li:image:...)."""
        try:
            # 1. Resolve image binary bytes from local disk or URL
            image_bytes: bytes | None = None
            if image_url.startswith("/static/"):
                rel_path = image_url.replace("/static/", "").lstrip("/\\")
                local_file = Path(settings.LOCAL_STORAGE_DIR) / rel_path
                if local_file.exists():
                    image_bytes = local_file.read_bytes()
            elif image_url.startswith("http://") or image_url.startswith("https://"):
                res = await client.get(image_url, timeout=15.0)
                if res.status_code == 200:
                    image_bytes = res.content

            if not image_bytes:
                logger.warning("Could not read image bytes for LinkedIn upload from: %s", image_url)
                return None

            # 2. Step 1: Initialize image upload
            init_payload = {
                "initializeUploadRequest": {
                    "owner": author_urn
                }
            }
            init_res = await client.post(self.images_endpoint, headers=headers, json=init_payload)
            if init_res.status_code != 200:
                logger.warning("LinkedIn image initializeUpload returned %s: %s", init_res.status_code, init_res.text)
                return None

            init_data = init_res.json().get("value", {})
            upload_url = init_data.get("uploadUrl")
            image_urn = init_data.get("image")

            if not upload_url or not image_urn:
                return None

            # 3. Step 2: Upload raw image binary to presigned URL
            upload_headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "image/png",
            }
            upload_res = await client.put(upload_url, headers=upload_headers, content=image_bytes)
            if upload_res.status_code in [200, 201]:
                logger.info("Successfully uploaded image to LinkedIn: %s", image_urn)
                return image_urn
            else:
                logger.warning("LinkedIn image binary upload returned %s: %s", upload_res.status_code, upload_res.text)
                return None
        except Exception as err:
            logger.warning("Failed to upload image to LinkedIn, falling back to text: %s", err)
            return None

    async def publish(
        self,
        caption: str,
        image_url: str,
        hashtags: list[str] | None = None,
    ) -> PublishResult:
        """Publish post to LinkedIn with caption and media."""
        full_text = caption
        if hashtags:
            clean_tags = [f"#{tag.lstrip('#')}" for tag in hashtags if tag]
            full_text = f"{caption}\n\n{' '.join(clean_tags)}"

        access_token = self.access_token
        author_urn = self.author_urn

        # Check if LinkedIn OAuth credentials are fully configured
        if not access_token or not author_urn:
            error_msg = (
                "LinkedIn account is not connected yet. "
                "Please connect your LinkedIn account by visiting http://localhost:8000/auth/linkedin/login"
            )
            logger.warning(error_msg)
            return PublishResult(success=False, error_message=error_msg)

        headers = self._get_api_headers()

        async with httpx.AsyncClient(timeout=45.0) as client:
            # Attempt to upload image asset
            image_urn = None
            if image_url:
                image_urn = await self._upload_image(client, headers, image_url, author_urn)

            payload = {
                "author": author_urn,
                "commentary": full_text,
                "visibility": "PUBLIC",
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": [],
                },
                "lifecycleState": "PUBLISHED",
                "isReshareDisabledByAuthor": False,
            }

            if image_urn:
                payload["content"] = {
                    "media": {
                        "id": image_urn,
                        "altText": caption[:100] if caption else "Social Media Poster",
                    }
                }

            try:
                response = await client.post(self.api_endpoint, headers=headers, json=payload)
                if response.status_code in [200, 201]:
                    post_id = response.headers.get("x-restli-id", f"urn:li:share:{uuid.uuid4().hex[:12]}")
                    logger.info("Successfully published live to LinkedIn! Post URN: %s", post_id)
                    return PublishResult(success=True, platform_post_id=post_id)
                else:
                    err_body = response.text
                    logger.error("LinkedIn publish failed [%s]: %s", response.status_code, err_body)
                    return PublishResult(
                        success=False,
                        error_message=f"LinkedIn API error [{response.status_code}]: {err_body}",
                    )
            except httpx.HTTPError as err:
                logger.error("Network error while dispatching to LinkedIn: %s", err)
                return PublishResult(success=False, error_message=str(err))
