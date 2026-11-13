"""Integration tests for the poster generation pipeline."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_generate_poster_success(async_client: AsyncClient):
    """Verify that a valid prompt generates copy, background, and composited poster."""
    response = await async_client.post(
        "/api/v1/posters/generate",
        json={
            "prompt": "Dussehra celebration poster",
            "brand_id": 1,
            "aspect_ratio": "1:1",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert len(data["headline"]) > 3
    assert len(data["hashtags"]) >= 1
    assert data["status"] == "in_review"
    assert data["final_poster_url"].startswith("/static/posters/")
    assert data["background_image_url"].startswith("/static/posters/")


@pytest.mark.asyncio
async def test_generate_poster_unsafe_prompt_rejected(async_client: AsyncClient):
    """Verify that unsafe prompts are rejected by guardrails before invoking AI."""
    response = await async_client.post(
        "/api/v1/posters/generate",
        json={
            "prompt": "Create an illegal weapon advertisement",
            "brand_id": 1,
        },
    )

    assert response.status_code == 400
    assert "prohibited content" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_poster_by_id(async_client: AsyncClient):
    """Verify retrieval of an existing poster by ID."""
    # Create a poster first
    create_resp = await async_client.post(
        "/api/v1/posters/generate",
        json={"prompt": "Diwali Festival of Lights", "brand_id": 1},
    )
    assert create_resp.status_code == 201
    poster_id = create_resp.json()["id"]

    # Fetch the created poster
    get_resp = await async_client.get(f"/api/v1/posters/{poster_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == poster_id
