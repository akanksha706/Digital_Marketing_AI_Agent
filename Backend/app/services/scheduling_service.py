"""Service orchestrating social post scheduling and direct dispatch."""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Poster, ScheduledJob, PostStatus, JobStatus, SocialPlatform
from app.interfaces.social_publisher import AbstractSocialPublisher


class SchedulingService:
    """Manages queueing, direct dispatch, and cancellation of social media posts."""

    def __init__(
        self,
        linkedin_publisher: AbstractSocialPublisher,
        instagram_publisher: AbstractSocialPublisher,
    ):
        self.linkedin_publisher = linkedin_publisher
        self.instagram_publisher = instagram_publisher

    def _get_publisher(self, platform: SocialPlatform) -> AbstractSocialPublisher:
        """Route to appropriate publisher adapter based on platform."""
        if platform == SocialPlatform.LINKEDIN:
            return self.linkedin_publisher
        elif platform == SocialPlatform.INSTAGRAM:
            return self.instagram_publisher
        raise ValueError(f"Unsupported social platform: {platform}")

    async def schedule_or_dispatch(
        self,
        poster_id: int,
        platform: SocialPlatform,
        post_now: bool,
        scheduled_for: datetime,
        db: AsyncSession,
        media_url: Optional[str] = None,
    ) -> ScheduledJob:
        """Publish post immediately or enqueue for future background dispatch."""
        poster = await db.get(Poster, poster_id)
        if not poster:
            raise ValueError(f"Poster with ID {poster_id} not found.")

        # Mandatory Approval Check: Never publish without prior reviewer approval
        if poster.status not in (PostStatus.APPROVED, PostStatus.SCHEDULED, PostStatus.PUBLISHED) or not poster.approval_locked_at:
            raise ValueError("Poster must be approved by a reviewer before scheduling or publishing.")

        job = ScheduledJob(
            poster_id=poster.id,
            platform=platform,
            scheduled_for=scheduled_for,
            status=JobStatus.PROCESSING if post_now else JobStatus.PENDING,
        )
        db.add(job)
        await db.flush()

        # Resolve media URL: prioritized custom media (video or adjusted image) -> final poster
        target_media_url = media_url or poster.final_poster_url or poster.background_image_url or ""

        if post_now:
            publisher = self._get_publisher(platform)
            publish_result = await publisher.publish(
                caption=poster.caption,
                image_url=target_media_url,
                hashtags=poster.hashtags,
            )

            if publish_result.success:
                job.status = JobStatus.SUCCESS
                job.platform_post_id = publish_result.platform_post_id
                poster.status = PostStatus.PUBLISHED
                poster.published_at = datetime.now(timezone.utc)
            else:
                job.status = JobStatus.FAILED
                job.error_message = publish_result.error_message
        else:
            poster.status = PostStatus.SCHEDULED

        poster.updated_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(job)
        return job

    async def cancel_scheduled_job(self, job_id: int, db: AsyncSession) -> ScheduledJob:
        """Cancel a pending scheduled job before it executes."""
        job = await db.get(ScheduledJob, job_id)
        if not job:
            raise ValueError(f"Scheduled job with ID {job_id} not found.")

        if job.status != JobStatus.PENDING:
            raise ValueError(f"Cannot cancel a job with status '{job.status}'. Only pending jobs can be cancelled.")

        poster_id = job.poster_id
        await db.delete(job)
        await db.flush()

        # Check if any remaining pending jobs exist for this poster
        remaining_jobs_query = await db.execute(
            select(ScheduledJob).where(
                ScheduledJob.poster_id == poster_id,
                ScheduledJob.status == JobStatus.PENDING,
            )
        )
        if not remaining_jobs_query.scalars().all():
            poster = await db.get(Poster, poster_id)
            if poster and poster.status == PostStatus.SCHEDULED:
                poster.status = PostStatus.APPROVED  # Revert back to approved

        return job

    async def get_jobs_for_poster(self, poster_id: int, db: AsyncSession) -> List[ScheduledJob]:
        """Fetch all dispatch jobs created for a given poster."""
        query = await db.execute(
            select(ScheduledJob)
            .where(ScheduledJob.poster_id == poster_id)
            .order_by(ScheduledJob.scheduled_for.desc())
        )
        return query.scalars().all()
