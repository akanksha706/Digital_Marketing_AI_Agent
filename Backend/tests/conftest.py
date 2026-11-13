"""Pytest shared configuration and fixtures for testing the FastAPI application."""

import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import io
from PIL import Image
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.db.base import Base
from app.db.session import get_db_session
from app.api.dependencies import get_generation_service
from app.services.generation_service import GenerationService
from app.adapters.safety.guardrails import GuardrailsSafetyChecker
from app.adapters.storage.local_storage import LocalStorageProvider
from app.services.poster_compositor import PosterCompositor
from app.interfaces.text_generator import AbstractTextGenerator, PosterPlan
from sqlalchemy.pool import StaticPool
from app.interfaces.image_generator import AbstractImageGenerator

# Dedicated in-memory SQLite engine for the test suite
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)
test_async_session_factory = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def override_get_db_session():
    """Dependency override providing an async session bound to the test database."""
    async with test_async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class TestStubTextGenerator(AbstractTextGenerator):
    """Deterministic fast stub for test suite execution to avoid external rate limits."""
    async def generate_poster_plan(self, prompt: str, brand_tone: str, banned_words=None) -> PosterPlan:
        return PosterPlan(
            headline=f"Celebrate {prompt.title()}",
            caption=f"Experience the joy of {prompt}. Connect with our team to discover more.",
            hashtags=[f"#{prompt.replace(' ', '')}", "#Celebration", "#Growth"],
            quote="Where tradition meets modern grace.",
            category_tag="SPECIAL CELEBRATION",
            cta_text="Discover Now →",
            image_prompt="Festive background scene",
            template_name="glassmorphic",
        )


class TestStubImageGenerator(AbstractImageGenerator):
    """Deterministic fast canvas stub for test suite."""
    async def generate_background(self, image_prompt: str, width: int = 1024, height: int = 1024) -> bytes:
        img = Image.new("RGB", (width, height), color="#1e1b4b")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()


def override_get_generation_service() -> GenerationService:
    """Dependency override injecting fast stubs for unit testing."""
    return GenerationService(
        safety_checker=GuardrailsSafetyChecker(),
        text_generator=TestStubTextGenerator(),
        image_generator=TestStubImageGenerator(),
        storage_provider=LocalStorageProvider(),
        compositor=PosterCompositor(),
    )


from app.interfaces.social_publisher import AbstractSocialPublisher, PublishResult
from app.api.dependencies import get_generation_service, get_scheduling_service, get_scheduler_worker
from app.services.scheduling_service import SchedulingService
from app.workers.scheduler_worker import SchedulerWorker


class TestStubSocialPublisher(AbstractSocialPublisher):
    """Stub publisher for test suite execution."""
    async def publish(self, caption: str, image_url: str, hashtags: list[str] | None = None) -> PublishResult:
        return PublishResult(success=True, platform_post_id="test_post_12345")


def override_get_scheduling_service() -> SchedulingService:
    stub = TestStubSocialPublisher()
    return SchedulingService(linkedin_publisher=stub, instagram_publisher=stub)


def override_get_scheduler_worker() -> SchedulerWorker:
    stub = TestStubSocialPublisher()
    return SchedulerWorker(linkedin_publisher=stub, instagram_publisher=stub)


# Register test overrides
app.dependency_overrides[get_db_session] = override_get_db_session
app.dependency_overrides[get_generation_service] = override_get_generation_service
app.dependency_overrides[get_scheduling_service] = override_get_scheduling_service
app.dependency_overrides[get_scheduler_worker] = override_get_scheduler_worker


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    """Create all tables before each test and drop them afterwards for complete test isolation."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def async_client():
    """Yield an HTTP async test client bound to the FastAPI application."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
