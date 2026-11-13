"""Integration tests for brand management and knowledge graph memory."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_brand_crud(async_client: AsyncClient):
    """Verify brand creation, retrieval, and updating."""
    # 1. Create Brand
    create_resp = await async_client.post(
        "/api/v1/admin/brands",
        json={
            "team_name": "Growth Marketing Team",
            "primary_color": "#10b981",
            "secondary_color": "#ffffff",
            "font_family": "Roboto",
            "tone_of_voice": "energetic and bold",
            "banned_words": ["cheap", "unregulated"],
            "default_hashtags": ["#Growth", "#Marketing"],
        },
    )
    assert create_resp.status_code == 201
    brand_id = create_resp.json()["id"]
    assert create_resp.json()["team_name"] == "Growth Marketing Team"

    # 2. Get Brand by ID
    get_resp = await async_client.get(f"/api/v1/admin/brands/{brand_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["primary_color"] == "#10b981"

    # 3. Update Brand
    update_resp = await async_client.put(
        f"/api/v1/admin/brands/{brand_id}",
        json={"primary_color": "#059669", "tone_of_voice": "visionary and confident"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["primary_color"] == "#059669"
    assert update_resp.json()["tone_of_voice"] == "visionary and confident"


@pytest.mark.asyncio
async def test_approval_automatically_records_knowledge_graph(async_client: AsyncClient):
    """Verify that approving a poster updates the occasion node and increments template approval counts."""
    # 1. Create custom brand
    brand_resp = await async_client.post(
        "/api/v1/admin/brands",
        json={
            "team_name": "Festive Campaigns Unit",
            "primary_color": "#f59e0b",
            "secondary_color": "#ffffff",
            "tone_of_voice": "festive and joyful",
        },
    )
    brand_id = brand_resp.json()["id"]

    # 2. Generate poster under this brand
    gen_resp = await async_client.post(
        "/api/v1/posters/generate",
        json={"prompt": "Diwali Special Greetings", "brand_id": brand_id},
    )
    assert gen_resp.status_code == 201
    poster_id = gen_resp.json()["id"]

    # 3. Approve poster
    approve_resp = await async_client.post(
        f"/api/v1/reviews/{poster_id}/approve",
        json={"reviewer_id": 1},
    )
    assert approve_resp.status_code == 200

    # 4. Check Knowledge Graph summary for the brand
    kg_resp = await async_client.get(f"/api/v1/admin/brands/{brand_id}/knowledge-graph")
    assert kg_resp.status_code == 200
    kg_data = kg_resp.json()

    # Verify Occasion was extracted and recorded
    assert len(kg_data["occasions"]) >= 1
    assert any("Diwali" in occ["name"] for occ in kg_data["occasions"])

    # Verify template link count was incremented
    assert len(kg_data["top_templates"]) >= 1
    assert kg_data["top_templates"][0]["approval_count"] >= 1


@pytest.mark.asyncio
async def test_style_rule_learning_and_confirmation(async_client: AsyncClient):
    """Verify style rule derivation from edits and confirmation by team lead."""
    # 1. Create brand
    brand_resp = await async_client.post(
        "/api/v1/admin/brands",
        json={"team_name": "Executive Comms Team", "tone_of_voice": "crisp and clean"},
    )
    brand_id = brand_resp.json()["id"]

    # 2. Generate poster
    gen_resp = await async_client.post(
        "/api/v1/posters/generate",
        json={"prompt": "Annual Corporate Summit 2026", "brand_id": brand_id},
    )
    poster_id = gen_resp.json()["id"]

    # 3. Apply an edit that shortens the headline
    await async_client.post(
        f"/api/v1/reviews/{poster_id}/edit",
        json={"instruction": "Change headline to 'Summit 2026'", "user_id": 1},
    )

    # 4. Approve poster -> Knowledge graph analyzes revision history
    await async_client.post(f"/api/v1/reviews/{poster_id}/approve", json={"reviewer_id": 1})

    # 5. Check Knowledge Graph for derived style rule
    kg_resp = await async_client.get(f"/api/v1/admin/brands/{brand_id}/knowledge-graph")
    rules = kg_resp.json()["confirmed_rules"]
    assert len(rules) >= 1
    rule_id = rules[0]["id"]
    assert rules[0]["is_confirmed"] is False

    # 6. Team lead confirms the style rule
    confirm_resp = await async_client.patch(f"/api/v1/admin/style-rules/{rule_id}/confirm")
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["is_confirmed"] is True
