"""Integration tests for the reviewer feedback, approval locking, and revision history."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_plain_language_edit_updates_poster_and_creates_revision(async_client: AsyncClient):
    """Verify that a reviewer can modify copy in plain words, generating a new version without re-painting."""
    # Step 1: Generate initial poster
    gen_resp = await async_client.post(
        "/api/v1/posters/generate",
        json={"prompt": "Diwali Celebration", "brand_id": 1},
    )
    assert gen_resp.status_code == 201
    poster_id = gen_resp.json()["id"]

    # Step 2: Request plain-language revision
    edit_resp = await async_client.post(
        f"/api/v1/reviews/{poster_id}/edit",
        json={"instruction": "Change headline to 'Shubh Deepavali 2026' and #Joy", "user_id": 1},
    )
    assert edit_resp.status_code == 200
    updated_data = edit_resp.json()
    assert updated_data["headline"] == "Shubh Deepavali 2026"
    assert "#Joy" in updated_data["hashtags"]
    assert "_v1.png" in updated_data["final_poster_url"]

    # Step 3: Check revision history trail
    rev_resp = await async_client.get(f"/api/v1/reviews/{poster_id}/revisions")
    assert rev_resp.status_code == 200
    revisions = rev_resp.json()
    assert len(revisions) == 1
    assert revisions[0]["version_number"] == 1
    assert revisions[0]["instruction"] == "Change headline to 'Shubh Deepavali 2026' and #Joy"


@pytest.mark.asyncio
async def test_approval_lock_prevents_further_edits(async_client: AsyncClient):
    """Verify that once a poster is approved, the immutability lock blocks edits."""
    # Generate poster
    gen_resp = await async_client.post(
        "/api/v1/posters/generate",
        json={"prompt": "Spring Festive Offer", "brand_id": 1},
    )
    poster_id = gen_resp.json()["id"]

    # Approve poster
    approve_resp = await async_client.post(
        f"/api/v1/reviews/{poster_id}/approve",
        json={"reviewer_id": 1, "notes": "Approved for dispatch"},
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"

    # Attempt to edit approved poster -> MUST FAIL
    edit_resp = await async_client.post(
        f"/api/v1/reviews/{poster_id}/edit",
        json={"instruction": "Change headline to Something Else", "user_id": 1},
    )
    assert edit_resp.status_code == 400
    assert "already been approved" in edit_resp.json()["detail"]


@pytest.mark.asyncio
async def test_reject_poster(async_client: AsyncClient):
    """Verify rejection workflow."""
    gen_resp = await async_client.post(
        "/api/v1/posters/generate",
        json={"prompt": "Annual Gala Night", "brand_id": 1},
    )
    poster_id = gen_resp.json()["id"]

    reject_resp = await async_client.post(
        f"/api/v1/reviews/{poster_id}/reject",
        json={"reviewer_id": 1, "reason": "Brand colors do not match guidelines"},
    )
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "rejected"
