"""Background polling worker executing scheduled social media dispatches."""

import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ScheduledJob, Poster, JobStatus, PostStatus, SocialPlatform
from app.db.session import async_session_factory
from app.interfaces.social_publisher import AbstractSocialPublisher

logger = logging.getLogger(__name__)


class SchedulerWorker:
    """Worker polling PostgreSQL for due publishing jobs and dispatching them."""

    def __init__(
        self,
        linkedin_publisher: AbstractSocialPublisher,
        instagram_publisher: AbstractSocialPublisher,
    ):
        self.linkedin_publisher = linkedin_publisher
        self.instagram_publisher = instagram_publisher

    def _get_publisher(self, platform: SocialPlatform) -> AbstractSocialPublisher:
        """Route to matching publisher adapter."""
        if platform == SocialPlatform.LINKEDIN:
            return self.linkedin_publisher
        elif platform == SocialPlatform.INSTAGRAM:
            return self.instagram_publisher
        raise ValueError(f"Unsupported platform: {platform}")

    async def process_due_jobs(self, db: AsyncSession) -> int:
        """Query pending jobs whose scheduled time has arrived and dispatch them. Returns processed count."""
        now = datetime.now(timezone.utc)

        # Concurrency safe selection for pending due jobs
        query = await db.execute(
            select(ScheduledJob)
            .where(
                ScheduledJob.status == JobStatus.PENDING,
                ScheduledJob.scheduled_for <= now,
            )
            .order_by(ScheduledJob.scheduled_for.asc())
            .limit(10)
        )
        due_jobs = query.scalars().all()

        processed_count = 0
        for job in due_jobs:
            processed_count += 1
            poster = await db.get(Poster, job.poster_id)

            # Confirm approval lock still stands
            if not poster or poster.status not in (PostStatus.APPROVED, PostStatus.SCHEDULED) or not poster.approval_locked_at:
                job.status = JobStatus.FAILED
                job.error_message = "Dispatch aborted: Poster approval lock is no longer valid."
                continue

            job.status = JobStatus.PROCESSING
            await db.flush()

            publisher = self._get_publisher(job.platform)
            publish_result = await publisher.publish(
                caption=poster.caption,
                image_url=poster.final_poster_url or "",
                hashtags=poster.hashtags,
            )

            if publish_result.success:
                job.status = JobStatus.SUCCESS
                job.platform_post_id = publish_result.platform_post_id
                poster.status = PostStatus.PUBLISHED
                logger.info("Successfully published job %s to %s", job.id, job.platform)
            else:
                job.retry_count += 1
                job.error_message = publish_result.error_message
                if job.retry_count < job.max_retries:
                    # Retry once more on next tick
                    job.status = JobStatus.PENDING
                    logger.warning("Job %s failed; queued for retry (%s/%s)", job.id, job.retry_count, job.max_retries)
                else:
                    # Flag as failed after exceeding max retries
                    job.status = JobStatus.FAILED
                    logger.error("Job %s failed permanently after max retries: %s", job.id, publish_result.error_message)

            poster.updated_at = datetime.now(timezone.utc)
            await db.flush()

        if processed_count > 0:
            await db.commit()

        return processed_count

    async def start_polling(self, poll_interval_seconds: int = 15):
        """Continuously polls database for scheduled jobs due for execution."""
        logger.info("Scheduler worker background polling loop started (interval=%ss)...", poll_interval_seconds)
        while True:
            try:
                async with async_session_factory() as db:
                    count = await self.process_due_jobs(db)
                    if count > 0:
                        logger.info("Scheduler tick processed %s due jobs.", count)
            except asyncio.CancelledError:
                logger.info("Scheduler worker polling cancelled.")
                break
            except Exception as err:
                logger.error("Error in scheduler polling loop: %s", err, exc_info=True)
            await asyncio.sleep(poll_interval_seconds)
