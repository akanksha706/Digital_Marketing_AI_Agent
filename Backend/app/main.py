"""FastAPI application initialization and lifespan management."""

import asyncio
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Ensure Backend root is always on python sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.dependencies import get_scheduler_worker
from app.api.v1.endpoints.linkedin_oauth import router as linkedin_router
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown hooks."""
    # Ensure storage directories exist
    Path(settings.LOCAL_STORAGE_DIR).mkdir(parents=True, exist_ok=True)

    # Start background scheduler worker loop for scheduled post dispatches
    worker = get_scheduler_worker()
    scheduler_task = asyncio.create_task(worker.start_polling(poll_interval_seconds=15))

    yield

    # Clean shutdown of worker task
    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass


def create_application() -> FastAPI:
    """Factory function creating the configured FastAPI instance."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",  # Direct /docs access
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Enable CORS for frontend integration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Redirect root to /docs
    @app.get("/", include_in_schema=False)
    async def root_redirect():
        return RedirectResponse(url="/docs")

    # Mount static assets directory for local preview
    storage_path = Path(settings.LOCAL_STORAGE_DIR)
    storage_path.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(storage_path)), name="static")

    # Mount API v1 router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # Direct top-level OAuth handlers (e.g. /auth/linkedin/callback matching developer portal redirect URI)
    app.include_router(linkedin_router)

    return app


app = create_application()
