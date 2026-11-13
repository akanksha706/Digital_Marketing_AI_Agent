"""Application configuration settings."""

from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global application settings validated via Pydantic."""

    model_config = SettingsConfigDict(
        env_file=(
            str(Path(__file__).resolve().parents[2] / ".env"),  # Backend/.env
            str(Path(__file__).resolve().parents[3] / ".env"),  # Root .env
            ".env",
        ),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Project Metadata
    PROJECT_NAME: str = "AI Poster & Social Content Studio"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Database
    # Default points to local PostgreSQL on port 5434
    DATABASE_URL: str = "postgresql+asyncpg://postgres:42works123@localhost:5434/poster_studio"

    # AI Model Providers (Cloudflare Workers AI & Hugging Face)
    CLOUDFLARE_ACCOUNT_ID: str = ""
    CLOUDFLARE_API_TOKEN: str = ""
    TEXT_MODEL: str = "@cf/meta/llama-3.1-8b-instruct"
    IMAGE_MODEL: str = "@cf/black-forest-labs/flux-1-schnell"
    VIDEO_MODEL: str = "Wan-AI/Wan2.2-TI2V-5B"
    HUGGINGFACE_API_KEY: str = ""
    HUGGING_FACE_TOKEN: str = ""

    # Fallback AI Provider
    GEMINI_API_KEY: str = ""

    # Storage Settings
    STORAGE_BACKEND: str = "local"  # 'local' or 'r2'
    LOCAL_STORAGE_DIR: str = str(Path(__file__).resolve().parents[2] / "storage")

    @field_validator("LOCAL_STORAGE_DIR", mode="after")
    @classmethod
    def resolve_storage_dir(cls, v: str) -> str:
        """Ensures storage directory always resolves to the canonical Backend/storage path."""
        p = Path(v)
        if not p.is_absolute():
            backend_dir = Path(__file__).resolve().parents[2]
            # Strip redundant 'Backend' prefix if already present in relative path
            parts = [part for part in p.parts if part.lower() != "backend"]
            p = backend_dir.joinpath(*parts) if parts else backend_dir / "storage"
        return str(p.resolve())

    # Cloudflare R2 Settings (Production Storage)
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "poster-studio-assets"
    R2_PUBLIC_BASE_URL: str = ""

    # Social Media Publishing Secrets
    LINKEDIN_CLIENT_ID: str = ""
    LINKEDIN_CLIENT_SECRET: str = ""
    LINKEDIN_REDIRECT_URI: str = "http://localhost:8000/auth/linkedin/callback"
    LINKEDIN_ACCESS_TOKEN: str = ""
    LINKEDIN_AUTHOR_URN: str = ""  # e.g. "urn:li:person:..." or "urn:li:organization:..."

    # Firecrawl / Web Scraping
    FIRECRAWL_API_KEY: str = ""
    FILECRAWLER_API_KEY: str = ""
    INSTAGRAM_ACCESS_TOKEN: str = ""
    INSTAGRAM_BUSINESS_ACCOUNT_ID: str = ""
    PUBLIC_SERVER_BASE_URL: str = "http://localhost:8000"

    # Pinecone Vector DB (Knowledge Base for Pickachoo / Assistant)
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = "poster-studio-knowledge"

    # Security & Auth
    JWT_SECRET_KEY: str = "insecure_dev_secret_key_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days


settings = Settings()
