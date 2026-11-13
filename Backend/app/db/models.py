"""Database ORM models representing the core domain entities."""

import enum
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    String,
    Text,
    DateTime,
    ForeignKey,
    Enum,
    Integer,
    JSON,
    Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class UserRole(str, enum.Enum):
    """User authorization roles."""
    ADMIN = "admin"
    REVIEWER = "reviewer"
    MEMBER = "member"


class PostStatus(str, enum.Enum):
    """Lifecycle status of a poster and social post."""
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    REJECTED = "rejected"


class SocialPlatform(str, enum.Enum):
    """Supported social media publishing destinations."""
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"


class JobStatus(str, enum.Enum):
    """Execution status for asynchronous scheduled publishing jobs."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"


class Brand(Base):
    """Team brand profile defining visual identity and tone."""
    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    team_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    primary_color: Mapped[str] = mapped_column(String(20), default="#000000")
    secondary_color: Mapped[str] = mapped_column(String(20), default="#FFFFFF")
    font_family: Mapped[str] = mapped_column(String(50), default="Inter")
    tone_of_voice: Mapped[str] = mapped_column(String(100), default="professional")
    banned_words: Mapped[List[str]] = mapped_column(JSON, default=list)
    default_hashtags: Mapped[List[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="brand")
    posters: Mapped[List["Poster"]] = relationship("Poster", back_populates="brand")


class User(Base):
    """Team member, reviewer, or administrator account."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.MEMBER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    brand_id: Mapped[Optional[int]] = mapped_column(ForeignKey("brands.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    brand: Mapped[Optional["Brand"]] = relationship("Brand", back_populates="users")
    created_posters: Mapped[List["Poster"]] = relationship(
        "Poster", foreign_keys="Poster.created_by_id", back_populates="creator"
    )


class Poster(Base):
    """A generated social post including copy, visuals, and approval state."""
    __tablename__ = "posters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"), nullable=False)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Prompt and Copy
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    headline: Mapped[str] = mapped_column(String(200), nullable=False)
    caption: Mapped[str] = mapped_column(Text, nullable=False)
    hashtags: Mapped[List[str]] = mapped_column(JSON, default=list)
    quote: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)

    # Visual Assets
    background_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    final_poster_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    video_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    template_name: Mapped[str] = mapped_column(String(50), default="minimal_clean")
    aspect_ratio: Mapped[str] = mapped_column(String(20), default="1:1")
    layout_meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)

    # Workflow & Approval Lock
    status: Mapped[PostStatus] = mapped_column(
        Enum(PostStatus), default=PostStatus.DRAFT, nullable=False, index=True
    )
    approved_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    approval_locked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    brand: Mapped["Brand"] = relationship("Brand", back_populates="posters")
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by_id], back_populates="created_posters")
    revisions: Mapped[List["PosterRevision"]] = relationship("PosterRevision", back_populates="poster", cascade="all, delete-orphan")
    scheduled_jobs: Mapped[List["ScheduledJob"]] = relationship("ScheduledJob", back_populates="poster", cascade="all, delete-orphan")


class PosterRevision(Base):
    """Historical record of edits requested during review."""
    __tablename__ = "poster_revisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    poster_id: Mapped[int] = mapped_column(ForeignKey("posters.id"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    instruction: Mapped[str] = mapped_column(String(500), nullable=False)
    diff_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    poster: Mapped["Poster"] = relationship("Poster", back_populates="revisions")


class ScheduledJob(Base):
    """Publishing queue record for LinkedIn or Instagram dispatch."""
    __tablename__ = "scheduled_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    poster_id: Mapped[int] = mapped_column(ForeignKey("posters.id"), nullable=False)
    platform: Mapped[SocialPlatform] = mapped_column(Enum(SocialPlatform), nullable=False)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.PENDING, index=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=2)
    platform_post_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    poster: Mapped["Poster"] = relationship("Poster", back_populates="scheduled_jobs")


class OccasionTheme(Base):
    """Recurring event or campaign theme identified for a brand."""
    __tablename__ = "occasions_themes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    links: Mapped[List["KnowledgeLink"]] = relationship(
        "KnowledgeLink", back_populates="occasion", cascade="all, delete-orphan"
    )


class KnowledgeLink(Base):
    """Association tracking template and visual preferences per occasion."""
    __tablename__ = "knowledge_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"), nullable=False, index=True)
    occasion_id: Mapped[int] = mapped_column(ForeignKey("occasions_themes.id"), nullable=False, index=True)
    template_name: Mapped[str] = mapped_column(String(50), nullable=False)
    approval_count: Mapped[int] = mapped_column(Integer, default=1)
    last_approved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    occasion: Mapped["OccasionTheme"] = relationship("OccasionTheme", back_populates="links")


class StyleRule(Base):
    """Plain-language style rule derived from approved edits or admin settings."""
    __tablename__ = "style_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"), nullable=False, index=True)
    rule_text: Mapped[str] = mapped_column(String(300), nullable=False)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
