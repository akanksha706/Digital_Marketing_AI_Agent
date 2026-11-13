"""Abstract base interfaces and contract definitions."""

from app.interfaces.image_generator import AbstractImageGenerator
from app.interfaces.text_generator import AbstractTextGenerator, PosterPlan
from app.interfaces.video_generator import AbstractVideoGenerator
from app.interfaces.safety_checker import AbstractSafetyChecker, SafetyCheckResult
from app.interfaces.social_publisher import AbstractSocialPublisher, PublishResult
from app.interfaces.storage_provider import AbstractStorageProvider

__all__ = [
    "AbstractImageGenerator",
    "AbstractTextGenerator",
    "PosterPlan",
    "AbstractVideoGenerator",
    "AbstractSafetyChecker",
    "SafetyCheckResult",
    "AbstractSocialPublisher",
    "PublishResult",
    "AbstractStorageProvider",
]
