"""Interface for AI text-to-video and image-to-video generation."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class AbstractVideoGenerator(ABC):
    """Abstract contract for generating video reels from text prompts and images."""

    @abstractmethod
    async def generate_video(
        self,
        prompt: str,
        output_path: Path,
        duration_seconds: int = 4,
        source_image_path: Optional[Path] = None,
    ) -> bool:
        """Generate a video given a prompt and optional source image."""
        pass
