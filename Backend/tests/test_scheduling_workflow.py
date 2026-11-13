"""Integration tests for social media scheduling, direct dispatch, and queue processing."""

from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cannot_schedule_unapproved_poster(async_client: AsyncClient):
    """Verify that unapproved posters are rejected when attempting to schedule or publish."""
    # Generate draft poster (status = IN_REVIEW)
    gen_resp = await async_client.post(
        "/api/v1/posters/generate",
        json={"prompt": "Diwali Special Offer", "brand_id": 1},
    )
    assert gen_resp.status_code == 201
    poster_id = gen_resp.json()["id"]

    # Attempt to post now without approval -> MUST FAIL
    schedule_resp = await async_client.post(
        f"/api/v1/schedules/{poster_id}",
        json={"platform": "linkedin", "post_now": True},
    )
    assert schedule_resp.status_code == 400
    assert "must be approved" in schedule_resp.json()["detail"]


@pytest.mark.asyncio
async def test_post_now_publishes_to_linkedin_and_updates_status(async_client: AsyncClient):
    """Verify immediate direct dispatch for an approved poster."""
    # 1. Generate poster
    gen_resp = await async_client.post(
        "/api/v1/posters/generate",
        json={"prompt": "Holi Celebration Poster", "brand_id": 1},
    )
    poster_id = gen_resp.json()["id"]

    # 2. Approve poster
    approve_resp = await async_client.post(
        f"/api/v1/reviews/{poster_id}/approve",
        json={"reviewer_id": 1},
    )
    assert approve_resp.status_code == 200

    # 3. Post to LinkedIn immediately
    dispatch_resp = await async_client.post(
        f"/api/v1/schedules/{poster_id}",
        json={"platform": "linkedin", "post_now": True},
    )
    assert dispatch_resp.status_code == 201
    job_data = dispatch_resp.json()
    assert job_data["status"] == "success"
    assert job_data["platform_post_id"] is not None

    # 4. Confirm poster status transitioned to PUBLISHED
    poster_resp = await async_client.get(f"/api/v1/posters/{poster_id}")
    assert poster_resp.status_code == 200
    assert poster_resp.json()["status"] == "published"


@pytest.mark.asyncio
async def test_schedule_future_job_and_cancel(async_client: AsyncClient):
    """Verify scheduling a post for the future and cancelling it before dispatch."""
    # Generate and approve poster
    gen_resp = await async_client.post(
        "/api/v1/posters/generate",
        json={"prompt": "Independence Day Creative", "brand_id": 1},
    )
    poster_id = gen_resp.json()["id"]
    await async_client.post(f"/api/v1/reviews/{poster_id}/approve", json={"reviewer_id": 1})

    # Schedule for tomorrow
    future_time = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    sched_resp = await async_client.post(
        f"/api/v1/schedules/{poster_id}",
        json={"platform": "instagram", "post_now": False, "scheduled_for": future_time},
    )
    assert sched_resp.status_code == 201
    job_id = sched_resp.json()["id"]
    assert sched_resp.json()["status"] == "pending"

    # Cancel scheduled job
    cancel_resp = await async_client.delete(f"/api/v1/schedules/{job_id}")
    assert cancel_resp.status_code == 200
    assert "cancelled" in cancel_resp.json()["message"]


@pytest.mark.asyncio
async def test_scheduler_worker_processes_due_jobs(async_client: AsyncClient):
    """Verify background worker picks up due scheduled posts and publishes them."""
    # Generate and approve poster
    gen_resp = await async_client.post(
        "/api/v1/posters/generate",
        json={"prompt": "Navratri Special Festivities", "brand_id": 1},
    )
    poster_id = gen_resp.json()["id"]
    await async_client.post(f"/api/v1/reviews/{poster_id}/approve", json={"reviewer_id": 1})

    # Schedule for past time (1 minute ago) so it is immediately due
    past_time = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    sched_resp = await async_client.post(
        f"/api/v1/schedules/{poster_id}",
        json={"platform": "instagram", "post_now": False, "scheduled_for": past_time},
    )
    assert sched_resp.status_code == 201

    # Trigger worker tick
    worker_resp = await async_client.post("/api/v1/schedules/worker/tick")
    assert worker_resp.status_code == 200
    assert worker_resp.json()["processed_count"] >= 1

    # Check job status is now SUCCESS
    jobs_resp = await async_client.get(f"/api/v1/schedules/{poster_id}")
    assert jobs_resp.status_code == 200
    jobs = jobs_resp.json()
    assert len(jobs) >= 1
    assert jobs[0]["status"] == "success"
    assert jobs[0]["platform_post_id"] is not None
