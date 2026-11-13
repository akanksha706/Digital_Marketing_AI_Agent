"""Interface for AI background image generation."""

from abc import ABC, abstractmethod


class AbstractImageGenerator(ABC):
    """Abstract contract for generating poster background images."""

    @abstractmethod
    async def generate_background(
        self,
        image_prompt: str,
        width: int = 1024,
        height: int = 1024,
    ) -> bytes:
        """Generate a raw background image given an optimized scene prompt."""
        pass

    async def edit_image(
        self,
        image_bytes: bytes,
        edit_prompt: str,
        width: int = 1024,
        height: int = 1024,
        strength: float = 0.65,
    ) -> bytes:
        """Edit an existing image using an image-to-image diffusion model based on prompt."""
        return image_bytes
