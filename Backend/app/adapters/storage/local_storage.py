"""Local filesystem implementation of the storage provider interface."""

import asyncio
from pathlib import Path
from app.interfaces.storage_provider import AbstractStorageProvider
from app.core.config import settings


class LocalStorageProvider(AbstractStorageProvider):
    """Stores generated image assets on the local filesystem."""

    def __init__(self, base_dir: str = settings.LOCAL_STORAGE_DIR):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, file_path: str) -> Path:
        """Resolve path and guard against directory traversal attacks."""
        target_path = (self.base_dir / file_path).resolve()
        if not target_path.is_relative_to(self.base_dir):
            raise ValueError(f"Illegal path traversal attempt: {file_path}")
        return target_path

    async def save_asset(
        self,
        file_path: str,
        content: bytes,
        content_type: str = "image/png",
    ) -> str:
        """Write binary file to disk asynchronously and return relative web URL."""
        target = self._resolve_safe_path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        # Offload blocking filesystem write to thread pool
        def _write():
            target.write_bytes(content)

        await asyncio.to_thread(_write)
        # Return web accessible path for local dev server
        return f"/static/{file_path.replace('\\', '/')}"

    async def get_asset(self, file_path: str) -> bytes:
        """Read binary asset from disk asynchronously."""
        target = self._resolve_safe_path(file_path)
        if not target.exists():
            raise FileNotFoundError(f"Asset not found: {file_path}")

        return await asyncio.to_thread(target.read_bytes)

    async def delete_asset(self, file_path: str) -> bool:
        """Delete an asset from disk if present."""
        target = self._resolve_safe_path(file_path)
        if target.exists():
            await asyncio.to_thread(target.unlink)
            return True
        return False
