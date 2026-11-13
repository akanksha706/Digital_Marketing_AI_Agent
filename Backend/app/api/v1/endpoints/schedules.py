"""API endpoints for scheduling, dispatching, and cancelling social media posts."""

from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.db.models import ScheduledJob
from app.domain.schemas.schedule import (
    SchedulePostRequest,
    ScheduledJobResponse,
    CancelJobResponse,
)
from app.api.dependencies import get_scheduling_service, get_scheduler_worker
from app.services.scheduling_service import SchedulingService
from app.workers.scheduler_worker import SchedulerWorker

router = APIRouter(prefix="/schedules", tags=["Scheduling & Publishing"])


@router.get(
    "",
    response_model=List[ScheduledJobResponse],
    summary="List all scheduled jobs in queue",
)
@router.get(
    "/",
    response_model=List[ScheduledJobResponse],
    include_in_schema=False,
)
async def list_all_scheduled_jobs(
    db: AsyncSession = Depends(get_db_session),
):
    """Fetch status of all past, pending, and upcoming dispatch jobs."""
    query = select(ScheduledJob).order_by(desc(ScheduledJob.created_at))
    res = await db.execute(query)
    return res.scalars().all()


@router.post(
    "",
    response_model=ScheduledJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule or publish a poster",
)
@router.post(
    "/",
    response_model=ScheduledJobResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
@router.post(
    "/publish-now",
    response_model=ScheduledJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Publish approved poster immediately",
)
async def schedule_direct(
    payload: SchedulePostRequest,
    db: AsyncSession = Depends(get_db_session),
    scheduling_service: SchedulingService = Depends(get_scheduling_service),
):
    """Direct route for scheduling or publishing with payload containing poster_id."""
    if not payload.poster_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="poster_id must be provided in request body.",
        )
    try:
        job = await scheduling_service.schedule_or_dispatch(
            poster_id=payload.poster_id,
            platform=payload.platform,
            post_now=payload.post_now,
            scheduled_for=payload.scheduled_for,
            db=db,
            media_url=payload.media_url,
        )
        return job
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scheduling failed: {str(e)}",
        )


@router.post(
    "/{poster_id}",
    response_model=ScheduledJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Publish immediately or schedule an approved poster",
)
async def schedule_or_publish_post(
    poster_id: int,
    payload: SchedulePostRequest,
    db: AsyncSession = Depends(get_db_session),
    scheduling_service: SchedulingService = Depends(get_scheduling_service),
):
    """Confirm approval lock, then either dispatch directly or queue for scheduled execution."""
    try:
        job = await scheduling_service.schedule_or_dispatch(
            poster_id=poster_id,
            platform=payload.platform,
            post_now=payload.post_now,
            scheduled_for=payload.scheduled_for,
            db=db,
            media_url=payload.media_url,
        )
        return job
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scheduling failed: {str(e)}",
        )


@router.post(
    "/{job_id}/retry",
    response_model=ScheduledJobResponse,
    summary="Retry a failed dispatch job",
)
async def retry_failed_job(
    job_id: int,
    db: AsyncSession = Depends(get_db_session),
    scheduling_service: SchedulingService = Depends(get_scheduling_service),
):
    """Retry executing a failed scheduled job."""
    job = await db.get(ScheduledJob, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found.")
    return await scheduling_service.schedule_or_dispatch(
        poster_id=job.poster_id,
        platform=job.platform,
        post_now=True,
        scheduled_for=datetime.now(timezone.utc),
        db=db,
    )


@router.delete(
    "/{job_id}",
    response_model=CancelJobResponse,
    summary="Cancel a pending scheduled publishing job",
)
async def cancel_scheduled_job(
    job_id: int,
    db: AsyncSession = Depends(get_db_session),
    scheduling_service: SchedulingService = Depends(get_scheduling_service),
):
    """Cancel and remove a pending scheduled post from the dispatch queue."""
    try:
        await scheduling_service.cancel_scheduled_job(job_id=job_id, db=db)
        return CancelJobResponse(
            job_id=job_id,
            message="Scheduled job successfully cancelled and removed from queue.",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{poster_id}",
    response_model=List[ScheduledJobResponse],
    summary="List all publishing jobs for a poster",
)
async def get_poster_jobs(
    poster_id: int,
    db: AsyncSession = Depends(get_db_session),
    scheduling_service: SchedulingService = Depends(get_scheduling_service),
):
    """Fetch status of all past and upcoming dispatch jobs for this poster."""
    jobs = await scheduling_service.get_jobs_for_poster(poster_id=poster_id, db=db)
    return jobs


@router.post(
    "/worker/tick",
    summary="Trigger worker polling tick manually",
)
async def trigger_scheduler_tick(
    db: AsyncSession = Depends(get_db_session),
    worker: SchedulerWorker = Depends(get_scheduler_worker),
):
    """Process due pending jobs in the queue."""
    processed = await worker.process_due_jobs(db=db)
    return {"processed_count": processed, "timestamp": "ok"}
