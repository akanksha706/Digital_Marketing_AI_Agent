"""Interface for binary file storage (local disk or cloud bucket)."""

from abc import ABC, abstractmethod


class AbstractStorageProvider(ABC):
    """Abstract contract for storing and retrieving poster image assets."""

    @abstractmethod
    async def save_asset(
        self,
        file_path: str,
        content: bytes,
        content_type: str = "image/png",
    ) -> str:
        """Store an asset and return its accessible URI or URL."""
        pass

    @abstractmethod
    async def get_asset(self, file_path: str) -> bytes:
        """Retrieve binary asset content by path."""
        pass

    @abstractmethod
    async def delete_asset(self, file_path: str) -> bool:
        """Delete an asset from storage."""
        pass
