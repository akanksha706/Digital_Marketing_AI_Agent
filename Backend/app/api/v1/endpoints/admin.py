"""API endpoints for brand profile administration and knowledge graph management."""

import calendar
from datetime import datetime, timezone, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.db.models import (
    Brand,
    User,
    UserRole,
    Poster,
    PostStatus,
    ScheduledJob,
    JobStatus,
    SocialPlatform,
)
from app.core.security import hash_password
from app.domain.schemas.brand import BrandCreate, BrandUpdate, BrandResponse
from app.domain.schemas.auth import UserCreate, UserResponse
from app.domain.schemas.analytics import (
    GlobalAnalyticsSummary,
    CreatorSummary,
    CreatorTimelinePoint,
)
from app.domain.schemas.knowledge_graph import (
    TeamKnowledgeSummary,
    StyleRuleResponse,
    StyleRuleCreate,
)
from app.api.dependencies import get_knowledge_graph_service
from app.services.knowledge_graph import KnowledgeGraphService

router = APIRouter(prefix="/admin", tags=["Brand Admin & Knowledge Graph"])


@router.post(
    "/brands",
    response_model=BrandResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new brand profile",
)
async def create_brand(
    payload: BrandCreate,
    db: AsyncSession = Depends(get_db_session),
):
    """Register a new brand visual identity and tone."""
    # Check if team name already exists
    existing = await db.execute(select(Brand).where(Brand.team_name == payload.team_name))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Brand with team name '{payload.team_name}' already exists.",
        )

    brand = Brand(**payload.model_dump())
    db.add(brand)
    await db.flush()
    await db.refresh(brand)
    return brand


@router.get(
    "/brands",
    response_model=List[BrandResponse],
    summary="List all brand profiles",
)
async def list_brands(
    db: AsyncSession = Depends(get_db_session),
):
    """Fetch all registered team brand configurations."""
    result = await db.execute(select(Brand).order_by(Brand.created_at.desc()))
    return result.scalars().all()


@router.get(
    "/brands/{brand_id}",
    response_model=BrandResponse,
    summary="Retrieve brand profile by ID",
)
async def get_brand(
    brand_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Fetch detailed settings for a single brand."""
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found.",
        )
    return brand


@router.put(
    "/brands/{brand_id}",
    response_model=BrandResponse,
    summary="Update brand settings",
)
async def update_brand(
    brand_id: int,
    payload: BrandUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    """Modify brand colors, typography, tone, banned words, or hashtags."""
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found.",
        )

    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(brand, field, val)

    await db.flush()
    await db.refresh(brand)
    return brand


@router.get(
    "/brands/{brand_id}/knowledge-graph",
    response_model=TeamKnowledgeSummary,
    summary="Retrieve brand knowledge graph and visual memory",
)
async def get_brand_knowledge_graph(
    brand_id: int,
    db: AsyncSession = Depends(get_db_session),
    kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
):
    """Fetch all identified campaign occasions, top-performing templates, and style rules."""
    summary = await kg_service.get_team_summary(brand_id=brand_id, db=db)
    return summary


@router.get(
    "/knowledge-graph/{brand_id}",
    response_model=TeamKnowledgeSummary,
    summary="Retrieve brand knowledge graph (alias)",
)
async def get_knowledge_graph_alias(
    brand_id: int,
    db: AsyncSession = Depends(get_db_session),
    kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
):
    """Alias for /brands/{brand_id}/knowledge-graph."""
    return await kg_service.get_team_summary(brand_id=brand_id, db=db)


@router.patch(
    "/style-rules/{rule_id}/confirm",
    response_model=StyleRuleResponse,
    summary="Confirm a suggested style rule",
)
async def confirm_style_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db_session),
    kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
):
    """Mark a learned style rule as confirmed by the team lead."""
    try:
        rule = await kg_service.confirm_style_rule(rule_id=rule_id, db=db)
        return rule
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Admin: Register a new team member",
)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db_session),
):
    """Admin registers a new team member with specified role and password."""
    existing = await db.execute(select(User).where(User.email == payload.email.lower().strip()))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email '{payload.email}' already exists.",
        )

    user = User(
        email=payload.email.lower().strip(),
        hashed_password=hash_password(payload.password),
        role=payload.role,
        is_active=True,
        brand_id=payload.brand_id or 1,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user




@router.get(
    "/users",
    response_model=List[UserResponse],
    summary="Admin: List all team users",
)
async def list_users(
    db: AsyncSession = Depends(get_db_session),
):
    """List all registered team users and their roles."""
    result = await db.execute(select(User).order_by(User.id.asc()))
    users = result.scalars().all()
    return users


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Admin: Remove or deactivate a team user",
)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Admin removes a team user account or deactivates them if they have historical posters."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if user.email == "admin@company.com":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the primary administrator account.",
        )

    # Check if this user created posters
    posters_res = await db.execute(select(Poster).where(Poster.created_by_id == user_id))
    has_posters = posters_res.scalars().first() is not None

    if has_posters:
        user.is_active = False
        await db.flush()
        return {
            "message": f"User {user.email} has associated posters, so their account has been deactivated.",
            "is_active": False,
        }
    else:
        await db.delete(user)
        await db.flush()
        return {
            "message": f"User {user.email} was successfully deleted.",
            "is_active": False,
        }


@router.patch(
    "/users/{user_id}/toggle-status",
    response_model=UserResponse,
    summary="Admin: Toggle user active status",
)
async def toggle_user_status(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Admin toggles a team user active/inactive status."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if user.email == "admin@company.com" and user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate the primary administrator.",
        )

    user.is_active = not user.is_active
    await db.flush()
    await db.refresh(user)
    return user


@router.get(
    "/creator-analytics",
    response_model=GlobalAnalyticsSummary,
    summary="Admin: Creator publishing performance & time-series tracking",
)
async def get_creator_analytics(
    timeframe: str = "all",  # "all", "week", "month", "year"
    db: AsyncSession = Depends(get_db_session),
):
    """Calculate weekly, monthly, and yearly publishing counts and platform breakdowns per creator."""
    now = datetime.now(timezone.utc)
    # Start of current week (Monday 00:00 UTC)
    start_of_week = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    # Start of current month
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # Start of current year
    start_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    # Fetch all users
    users_result = await db.execute(select(User).order_by(User.id.asc()))
    users = users_result.scalars().all()

    # Fetch all posters
    posters_result = await db.execute(select(Poster))
    all_posters = posters_result.scalars().all()

    # Fetch all successful jobs for platform attribution
    jobs_result = await db.execute(select(ScheduledJob))
    all_jobs = jobs_result.scalars().all()

    # Map jobs by poster_id
    jobs_by_poster: dict[int, list[ScheduledJob]] = {}
    for job in all_jobs:
        jobs_by_poster.setdefault(job.poster_id, []).append(job)

    creator_summaries: list[CreatorSummary] = []
    
    total_creators = len(users)
    total_posters_generated = len(all_posters)
    total_published = 0
    published_this_week = 0
    published_this_month = 0
    published_this_year = 0
    total_scheduled = 0
    total_archived = 0

    # Last 7 days labels for weekly chart
    last_7_days = [(now - timedelta(days=i)).date() for i in reversed(range(7))]

    for u in users:
        u_posters = [p for p in all_posters if p.created_by_id == u.id]
        u_published = [p for p in u_posters if p.status == PostStatus.PUBLISHED]
        u_scheduled = [p for p in u_posters if p.status == PostStatus.SCHEDULED]
        u_drafts = [p for p in u_posters if p.status in (PostStatus.DRAFT, PostStatus.IN_REVIEW)]
        u_archived = [p for p in u_posters if p.is_archived]

        u_pub_week = 0
        u_pub_month = 0
        u_pub_year = 0

        # Platform counts
        u_linkedin = 0
        u_instagram = 0

        for p in u_published:
            pub_date = p.published_at or p.created_at
            if pub_date >= start_of_week:
                u_pub_week += 1
            if pub_date >= start_of_month:
                u_pub_month += 1
            if pub_date >= start_of_year:
                u_pub_year += 1

            # Check jobs for platform
            p_jobs = jobs_by_poster.get(p.id, [])
            for j in p_jobs:
                if j.platform == SocialPlatform.LINKEDIN:
                    u_linkedin += 1
                elif j.platform == SocialPlatform.INSTAGRAM:
                    u_instagram += 1

        # Global aggregations
        total_published += len(u_published)
        published_this_week += u_pub_week
        published_this_month += u_pub_month
        published_this_year += u_pub_year
        total_scheduled += len(u_scheduled)
        total_archived += len(u_archived)

        # Build timeline according to selected timeframe (week, month, year, all)
        timeline: list[CreatorTimelinePoint] = []

        if timeframe == "week":
            # Current week: Monday to Sunday
            monday = (now - timedelta(days=now.weekday())).date()
            for i in range(7):
                day = monday + timedelta(days=i)
                day_published = 0
                day_linkedin = 0
                day_instagram = 0
                for p in u_published:
                    p_date = (p.published_at or p.created_at).date()
                    if p_date == day:
                        day_published += 1
                        for j in jobs_by_poster.get(p.id, []):
                            if j.platform == SocialPlatform.LINKEDIN:
                                day_linkedin += 1
                            elif j.platform == SocialPlatform.INSTAGRAM:
                                day_instagram += 1
                timeline.append(
                    CreatorTimelinePoint(
                        label=day.strftime("%a %d"),
                        published_count=day_published,
                        linkedin_count=day_linkedin,
                        instagram_count=day_instagram,
                    )
                )

        elif timeframe == "month":
            # Current month: split into 4 or 5 weekly buckets
            num_days = calendar.monthrange(now.year, now.month)[1]
            weeks = [
                ("W1 (1-7)", 1, 7),
                ("W2 (8-14)", 8, 14),
                ("W3 (15-21)", 15, 21),
                ("W4 (22-28)", 22, 28),
            ]
            if num_days > 28:
                weeks.append((f"W5 (29-{num_days})", 29, num_days))

            for label, start_day, end_day in weeks:
                w_pub = 0
                w_li = 0
                w_ig = 0
                for p in u_published:
                    dt = p.published_at or p.created_at
                    if dt.year == now.year and dt.month == now.month and start_day <= dt.day <= end_day:
                        w_pub += 1
                        for j in jobs_by_poster.get(p.id, []):
                            if j.platform == SocialPlatform.LINKEDIN:
                                w_li += 1
                            elif j.platform == SocialPlatform.INSTAGRAM:
                                w_ig += 1
                timeline.append(
                    CreatorTimelinePoint(
                        label=label,
                        published_count=w_pub,
                        linkedin_count=w_li,
                        instagram_count=w_ig,
                    )
                )

        elif timeframe == "year":
            # 12 months of the current year
            for m in range(1, 13):
                m_label = calendar.month_abbr[m]
                m_pub = 0
                m_li = 0
                m_ig = 0
                for p in u_published:
                    dt = p.published_at or p.created_at
                    if dt.year == now.year and dt.month == m:
                        m_pub += 1
                        for j in jobs_by_poster.get(p.id, []):
                            if j.platform == SocialPlatform.LINKEDIN:
                                m_li += 1
                            elif j.platform == SocialPlatform.INSTAGRAM:
                                m_ig += 1
                timeline.append(
                    CreatorTimelinePoint(
                        label=m_label,
                        published_count=m_pub,
                        linkedin_count=m_li,
                        instagram_count=m_ig,
                    )
                )

        else:  # "all"
            # Past 4 years
            for yr in range(now.year - 3, now.year + 1):
                yr_pub = 0
                yr_li = 0
                yr_ig = 0
                for p in u_published:
                    dt = p.published_at or p.created_at
                    if dt.year == yr:
                        yr_pub += 1
                        for j in jobs_by_poster.get(p.id, []):
                            if j.platform == SocialPlatform.LINKEDIN:
                                yr_li += 1
                            elif j.platform == SocialPlatform.INSTAGRAM:
                                yr_ig += 1
                timeline.append(
                    CreatorTimelinePoint(
                        label=str(yr),
                        published_count=yr_pub,
                        linkedin_count=yr_li,
                        instagram_count=yr_ig,
                    )
                )

        creator_summaries.append(
            CreatorSummary(
                creator_id=u.id,
                email=u.email,
                role=u.role.value if hasattr(u.role, "value") else str(u.role),
                total_generated=len(u_posters),
                total_published=len(u_published),
                published_this_week=u_pub_week,
                published_this_month=u_pub_month,
                published_this_year=u_pub_year,
                scheduled_count=len(u_scheduled),
                draft_count=len(u_drafts),
                archived_count=len(u_archived),
                linkedin_count=u_linkedin,
                instagram_count=u_instagram,
                timeline=timeline,
            )
        )

    return GlobalAnalyticsSummary(
        total_creators=total_creators,
        total_posters_generated=total_posters_generated,
        total_published=total_published,
        published_this_week=published_this_week,
        published_this_month=published_this_month,
        published_this_year=published_this_year,
        total_scheduled=total_scheduled,
        total_archived=total_archived,
        creators=creator_summaries,
    )
