"""Pydantic schemas for the brand knowledge graph and style rules."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class OccasionResponse(BaseModel):
    """Identified occasion or campaign theme."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    brand_id: int
    name: str
    created_at: datetime


class KnowledgeLinkResponse(BaseModel):
    """Frequency link between an occasion and an approved template."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    brand_id: int
    occasion_id: int
    template_name: str
    approval_count: int
    last_approved_at: datetime


class StyleRuleCreate(BaseModel):
    """Payload for creating a style rule."""
    rule_text: str = Field(..., min_length=3, max_length=300)
    is_confirmed: bool = Field(default=True)


class StyleRuleResponse(BaseModel):
    """Visual or copy style guideline."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    brand_id: int
    rule_text: str
    is_confirmed: bool
    created_at: datetime


class TeamKnowledgeSummary(BaseModel):
    """Aggregated brand intelligence and memory overview."""
    brand_id: int
    occasions: List[OccasionResponse]
    top_templates: List[KnowledgeLinkResponse]
    confirmed_rules: List[StyleRuleResponse]
